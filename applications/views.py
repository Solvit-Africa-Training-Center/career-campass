# applications/views.py  (only the create method changes; comments included)

from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.response import Response

from .models import (
    Application, ApplicationsEvent, ApplicationRequiredDocument, Status
)
from .serializers import ApplicationCreateSerializer, ApplicationSerializer
from .integrations.catalog import (
    get_program_required_documents,
    resolve_student_required_documents,
    CatalogNotFound, CatalogError,
)
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

    @transaction.atomic  # <<< everything below is "all-or-nothing"
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
            # Program doesn't exist in Catalog → roll back
            transaction.set_rollback(True)
            return Response({"detail": "Program not found in Catalog."}, status=status.HTTP_404_NOT_FOUND)
        except CatalogError as e:
            # Catalog is unhealthy → bubble as 502
            transaction.set_rollback(True)
            return Response({"detail": f"Upstream Catalog error: {e}"}, status=status.HTTP_502_BAD_GATEWAY)

        # Student rules are *helpful*, not critical → treat error as "no extra rules"
        try:
            student_reqs = resolve_student_required_documents(student_id)
        except CatalogError:
            student_reqs = []

        # 3) Merge -> snapshot to application_required_documents
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
            # Unique constraint (application, doc_type_id) protects against duplicates
            ApplicationRequiredDocument.objects.bulk_create(rows, ignore_conflicts=True)

        # 4) Timeline event
        ApplicationsEvent.objects.create(
            application=app,
            actor_id=student_id,
            event_type="created",
            to_status=Status.DRAFT,
            note=f"Snapshot {len(rows)} required document(s).",
        )

        # 5) Return minimal payload (id + status for client nav)
        return Response(ApplicationSerializer(app).data, status=status.HTTP_201_CREATED)
