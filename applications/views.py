from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from .models import (
    Application, ApplicationEvent, ApplicationRequiredDocument, ApplicationDocument, Status
)
from .serializers_attach import AttachDocumentIn
from .integrations.documents import get_student_document, DocumentsError, StudentDocumentNotFound


# Create your views here.

def current_user_id(request) -> str:
    return request.headers.get("X-User-id", "00000000-0000-0000-0000-000000000001")

class ApplicationViewSet(viewsets.ViewSet):
    def list(self, request):
        student_id = current_user_id(request)
        qs = Application.objects.filter(student_id=student_id).order_by("-created_at")[:50]
        return Response([{"id": str(a.id), "status": a.status} for a in qs])
    
    def create(self, request):
        student_id = current_user_id(request)
        ser = ApplicationCreateSerializer(data = request.data)
        ser.is_valid(raise_exception=True)
        
        app = Application.objects.create(
            student_id = student_id,
            program_id = ser.validated_data["program_id"],
            intake_id = ser.validated_data["intake_id"],
            status = Status.DRAFT,
        )
        
        
        ApplicationsEvent.objects.create(
            application = app, 
            actor_id = student_id,
            event_type = "creates",
            to_status = Status.DRAFT,
            note = "Application created",
            
        )
        
        return Response(ApplicationSerializer(app).data, status=status.HTTP_201_CREATED)
    @action(detail=True, methods=["post"], url_path="documents")
    @transaction.atomic
    def attach_document(self, request, pk=None):
        """
        Attach a student's uploaded document to this application under a specific doc_type_id.
        Validates:
        - ownership (application.student_id == current_user_id)
        - doc_type_id exists in snapshot for this application
        - max_items not exceeded
        - student_document belongs to same student and is status="clean"
        - doc_type match between payload and student_document
        """
        student_id = current_user_id(request)
        app = get_object_or_404(Application, pk=pk)

        # Only the owner (student) can attach here; staff UI can be added later
        if str(app.student_id) != str(student_id):
            return Response({"detail": "Forbidden: not your application."}, status=403)

        ser = AttachDocumentIn(data=request.data)
        ser.is_valid(raise_exception=True)
        doc_type_id = str(ser.validated_data["doc_type_id"])
        student_document_id = str(ser.validated_data["student_document_id"])

        # Snapshot check
        try:
            req = ApplicationRequiredDocument.objects.get(application=app, doc_type_id=doc_type_id)
        except ApplicationRequiredDocument.DoesNotExist:
            return Response({"detail": "doc_type_id not required for this application."}, status=422)

        # Enforce max_items (how many already attached for this type?)
        attached_count = ApplicationDocument.objects.filter(application=app, doc_type_id=doc_type_id).count()
        if attached_count >= req.max_items:
            return Response({"detail": "max_items reached for this document type."}, status=422)

        # Fetch student document info from Documents service
        try:
            sd = get_student_document(student_document_id)
        except StudentDocumentNotFound:
            return Response({"detail": "student_document not found."}, status=404)
        except DocumentsError as e:
            return Response({"detail": f"Upstream Documents error: {e}"}, status=502)

        # Validate ownership + status + type
        if str(sd.get("user_id")) != str(student_id):
            return Response({"detail": "student_document does not belong to current user."}, status=403)
        if sd.get("status") != "clean":
            return Response({"detail": "student_document status must be 'clean'."}, status=409)
        if str(sd.get("doc_type_id")) != doc_type_id:
            return Response({"detail": "doc_type_id mismatch between payload and student_document."}, status=422)

        # Create link row
        link = ApplicationDocument.objects.create(
            application=app,
            doc_type_id=doc_type_id,
            student_document_id=student_document_id,
        )

        # Event
        ApplicationEvent.objects.create(
            application=app,
            actor_id=student_id,
            event_type="doc_attached",
            note=f"Attached {student_document_id} to type {doc_type_id}.",
        )

        return Response(
            {
                "id": str(link.id),
                "application_id": str(app.id),
                "doc_type_id": doc_type_id,
                "student_document_id": student_document_id,
            },
            status=201,
        )