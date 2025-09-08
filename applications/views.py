
import logging
from typing import Optional
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from core.utils.uuid_helpers import parse_uuid, is_valid_uuid
from core.utils.view_decorators import validate_uuid_params
from core.mixins.uuid_viewset import UUIDViewSetMixin

logger = logging.getLogger(__name__)
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

def current_user_id(request) -> Optional[str]:
    """
    Get authenticated user's Student UUID for cross-service references.
    
    This function retrieves the Student UUID associated with the authenticated user
    to be used for cross-service references.
    
    Args:
        request: The HTTP request object with authenticated user
        
    Returns:
        Optional[str]: The Student UUID as a string or None if not authenticated
                      or if the user has no associated Student record
    """
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return None
    
    # Get the Student UUID from the accounts service
    try:
        from accounts.utils import get_student_uuid
        student_uuid = get_student_uuid(request.user.id)
        
        if student_uuid is None:
            logger.warning(f"User {request.user.id} has no associated Student record")
            return None
        
        return str(student_uuid)
    except Exception as e:
        logger.error(f"Error getting student UUID: {str(e)}")
        return None


class ApplicationViewSet(UUIDViewSetMixin, viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        student_id = current_user_id(request)
        if not student_id:
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        qs = Application.objects.filter(student_id=student_id).order_by("-created_at")[:50]
        return Response([{"id": str(a.id), "status": a.status} for a in qs])

    @transaction.atomic
    def create(self, request):
        """
        Create a Draft application AND snapshot required documents from Catalog.
        If any step fails (e.g., unknown program), we roll the DB back to clean state.
        """
        student_id = current_user_id(request)
        if not student_id:
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        ser = ApplicationCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        # Validate UUIDs from the serializer
        program_id = str(ser.validated_data["program_id"])
        intake_id = str(ser.validated_data["intake_id"])
        
        # Double-check UUID validity
        if not is_valid_uuid(program_id) or not is_valid_uuid(intake_id):
            return Response(
                {"detail": "Invalid UUID format for program_id or intake_id"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

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
    @validate_uuid_params('pk')
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
        if not student_id:
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        # Get application and check permissions
        app = self.get_object()  # This line is missing or corrupted 
        
        ApplicationsEvent.objects.create(
            application=app,
            actor_id=student_id,
            event_type="document_attached",
            from_status=app.status,  # Current status
            note="Document attached to application.",
        )

        return Response(ApplicationSerializer(app).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="documents")
    @transaction.atomic
    @validate_uuid_params('pk')
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
        if not student_id:
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
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