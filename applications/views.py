
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import (
    Application, ApplicationsEvent, ApplicationRequiredDocument, ApplicationDocument, Status
)
from .serializers import ApplicationCreateSerializer, ApplicationSerializer
from .serializers_attach import AttachDocumentIn
from .integrations.catalog import (
    get_program_required_documents,
    resolve_student_required_documents,
    CatalogNotFound, CatalogError,
)
from .integrations.documents import get_student_document, DocumentsError, StudentDocumentNotFound
from .services.snapshot import merge_required_docs

def current_user_id(request) -> str:
    """
    TEMP: get user from header to keep moving.
    Later, replace with your real auth (e.g., request.user or JWT).
    """
    return request.headers.get("X-User-Id", "00000000-0000-0000-0000-000000000001")


class ApplicationViewSet(viewsets.ViewSet):
    def list(self, request):
        student_id = current_user_id(request)
        qs = Application.objects.filter(student_id=student_id).order_by("-created_at")[:50]
        return Response([{"id": str(a.id), "status": a.status} for a in qs])

    @transaction.atomic
    def create(self, request):
        """
        Create a Draft application AND snapshot required documents from Catalog.
        If any step fails (e.g., unknown program), we roll the DB back to clean state.
        """
        student_id = current_user_id(request)
        ser = ApplicationCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        program_id = str(ser.validated_data["program_id"])
        intake_id = str(ser.validated_data["intake_id"])

        # 1) Create Draft application row
        app = Application.objects.create(
            student_id=student_id,
            program_id=program_id,
            intake_id=intake_id,
            status=Status.DRAFT,
        )

        # 2) Ask Catalog for policy
        try:
            program_reqs = get_program_required_documents(program_id)
        except CatalogNotFound:
            transaction.set_rollback(True)
            return Response({"detail": "Program not found in Catalog."}, status=status.HTTP_404_NOT_FOUND)
        except CatalogError as e:
            transaction.set_rollback(True)
            return Response({"detail": f"Upstream Catalog error: {e}"}, status=status.HTTP_502_BAD_GATEWAY)

        try:
            student_reqs = resolve_student_required_documents(student_id)
        except CatalogError:
            student_reqs = []

        merged = merge_required_docs(program_reqs, student_reqs)
        rows = [
            ApplicationRequiredDocument(
                application=app,
                doc_type_id=item["doc_type_id"],
                is_mandatory=item["is_mandatory"],
                min_items=item["min_items"],
                max_items=item["max_items"],
                source=item["source"],
            )
            for item in merged
        ]
        if rows:
            ApplicationRequiredDocument.objects.bulk_create(rows, ignore_conflicts=True)

        ApplicationsEvent.objects.create(
            application=app,
            actor_id=student_id,
            event_type="created",
            from_status=None,  # No previous status as this is a new application
            note=f"Snapshot {len(rows)} required document(s).",
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

        if str(app.student_id) != str(student_id):
            return Response({"detail": "Forbidden: not your application."}, status=403)

        ser = AttachDocumentIn(data=request.data)
        ser.is_valid(raise_exception=True)
        doc_type_id = str(ser.validated_data["doc_type_id"])
        student_document_id = str(ser.validated_data["student_document_id"])

        try:
            req = ApplicationRequiredDocument.objects.get(application=app, doc_type_id=doc_type_id)
        except ApplicationRequiredDocument.DoesNotExist:
            return Response({"detail": "doc_type_id not required for this application."}, status=422)

        attached_count = ApplicationDocument.objects.filter(application=app, doc_type_id=doc_type_id).count()
        if attached_count >= req.max_items:
            return Response({"detail": "max_items reached for this document type."}, status=422)

        try:
            sd = get_student_document(student_document_id)
        except StudentDocumentNotFound:
            return Response({"detail": "student_document not found."}, status=404)
        except DocumentsError as e:
            return Response({"detail": f"Upstream Documents error: {e}"}, status=502)

        if str(sd.get("user_id")) != str(student_id):
            return Response({"detail": "student_document does not belong to current user."}, status=403)
        if sd.get("status") != "clean":
            return Response({"detail": "student_document status must be 'clean'."}, status=409)
        if str(sd.get("doc_type_id")) != doc_type_id:
            return Response({"detail": "doc_type_id mismatch between payload and student_document."}, status=422)

        link = ApplicationDocument.objects.create(
            application=app,
            doc_type_id=doc_type_id,
            student_document_id=student_document_id,
        )

        ApplicationsEvent.objects.create(
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