
import logging
import json
import time
import uuid
from datetime import datetime
from typing import Optional
from functools import wraps
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

def log_action(action, user_id, app_id=None, outcome="success", extra=None, start_time=None):
    """
    Log an action in structured JSON format.
    
    Args:
        action (str): The action being performed (create, attach, transition, etc.)
        user_id (str): The ID of the user performing the action
        app_id (str, optional): The ID of the application being acted upon
        outcome (str): The outcome of the action (success, error, etc.)
        extra (dict, optional): Additional information to include in the log
        start_time (float, optional): The start time of the action in seconds
    """
    log_data = {
        "action": action,
        "user_id": str(user_id),
        "outcome": outcome
    }
    
    if app_id:
        log_data["app_id"] = str(app_id)
        
    if extra:
        log_data.update(extra)
        
    if start_time:
        log_data["elapsed_ms"] = int((time.time() - start_time) * 1000)
    
    logger.info(json.dumps(log_data))


def error_response(message, code, data=None):
    """
    Generate a standardized error response
    
    Args:
        message (str): Error message
        code (int): HTTP status code
        data (dict, optional): Additional data to include in the response
    
    Returns:
        Response: DRF Response object with standardized format
    """
    response_data = {
        "error": {
            "message": message,
            "code": code
        }
    }
    
    if data:
        response_data["error"]["data"] = data
        
    return Response(response_data, status=code)
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


def get_user_role(request) -> Optional[str]:
    """
    Get the user's role from the X-Role header.
    
    Args:
        request: The HTTP request object
        
    Returns:
        Optional[str]: The user's role as a string ('student' or 'staff') or None if not specified
    """
    return request.headers.get('X-Role')


# Define transition rules
TRANSITION_RULES = {
    'submit': {
        'allowed_from_statuses': [Status.DRAFT],
        'to_status': Status.SUBMITTED,
        'allowed_roles': ['student'],
    },
    'start_review': {
        'allowed_from_statuses': [Status.SUBMITTED],
        'to_status': Status.UNDER_REVIEW,
        'allowed_roles': ['staff'],
    },
    'offer': {
        'allowed_from_statuses': [Status.UNDER_REVIEW],
        'to_status': Status.OFFER,
        'allowed_roles': ['staff'],
    },
    'reject': {
        'allowed_from_statuses': [Status.UNDER_REVIEW, Status.OFFER],
        'to_status': Status.REJECTED,
        'allowed_roles': ['staff'],
    },
    'withdraw': {
        'allowed_from_statuses': [Status.DRAFT, Status.SUBMITTED, Status.UNDER_REVIEW, Status.OFFER],
        'to_status': Status.WITHDRAWN,
        'allowed_roles': ['student'],
    },
    'accept_offer': {
        'allowed_from_statuses': [Status.OFFER],
        'to_status': Status.ACCEPTED,
        'allowed_roles': ['student'],
    },
}


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
        start_time = time.time()
        student_id = current_user_id(request)
        if not student_id:
            log_action("create", "anonymous", outcome="error", extra={"error": "unauthorized"})
            return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            
        log_action("create", student_id, outcome="start", start_time=start_time)
        
        ser = ApplicationCreateSerializer(data=request.data)
        try:
            ser.is_valid(raise_exception=True)
        except Exception as e:
            log_action("create", student_id, outcome="error", 
                      extra={"error": "validation_error"}, start_time=start_time)
            raise

        # Get validated UUIDs from the serializer
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
            log_action("create", student_id, app_id=app.id, outcome="error", 
                      extra={"error": "program_not_found"}, start_time=start_time)
            return Response({"detail": "Program not found in Catalog."}, status=status.HTTP_404_NOT_FOUND)
        except CatalogError as e:
            transaction.set_rollback(True)
            log_action("create", student_id, app_id=app.id, outcome="error", 
                      extra={"error": "catalog_error", "message": str(e)}, start_time=start_time)
            return Response({"detail": f"Upstream Catalog error: {e}"}, status=status.HTTP_502_BAD_GATEWAY)

        try:
            student_reqs = resolve_student_required_documents(student_id)
        except CatalogError as e:
            student_reqs = []
            log_action("create", student_id, app_id=app.id, outcome="warning", 
                      extra={"warning": "student_docs_error", "message": str(e)})

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
        
        log_action("create", student_id, app_id=app.id, outcome="success", 
                 extra={"doc_count": len(rows)}, start_time=start_time)

        return Response(ApplicationSerializer(app).data, status=status.HTTP_201_CREATED)



    @action(detail=True, methods=["post"], url_path="submit")
    @transaction.atomic
    @validate_uuid_params('pk')
    def submit_application(self, request, pk=None):
        """
        Submit an application, changing its status from Draft to Submitted.
        
        Validates:
        - Application is in Draft status
        - All mandatory documents are attached
        - Application belongs to the current student
        
        This is a legacy endpoint that now uses the transition endpoint internally.
        """
        # Modify the data to include transition_type
        modified_data = {'transition_type': 'submit', 'note': 'Application submitted for review.'}
        
        # Add X-Role header to request META
        request.META['HTTP_X_ROLE'] = 'student'
        
        # Call the transition endpoint directly
        return self.transition(request, pk=pk, transition_data=modified_data)
        
        return Response(ApplicationSerializer(app).data)
        
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
        start_time = time.time()
        student_id = current_user_id(request)
        if not student_id:
            log_action("attach_document", "anonymous", outcome="error", extra={"error": "unauthorized"})
            return error_response("Authentication required", status.HTTP_401_UNAUTHORIZED)
            
        app = get_object_or_404(Application, pk=pk)
        log_action("attach_document", student_id, app_id=app.id, outcome="start", start_time=start_time)

        if str(app.student_id) != str(student_id):
            log_action("attach_document", student_id, app_id=app.id, outcome="error", 
                      extra={"error": "forbidden"}, start_time=start_time)
            return error_response("Forbidden: not your application.", status.HTTP_403_FORBIDDEN)

        try:
            ser = AttachDocumentIn(data=request.data)
            ser.is_valid(raise_exception=True)
            doc_type_id = str(ser.validated_data["doc_type_id"])
            student_document_id = str(ser.validated_data["student_document_id"])
        except Exception as e:
            log_action("attach_document", student_id, app_id=app.id, outcome="error", 
                      extra={"error": "validation_error"}, start_time=start_time)
            raise

        try:
            req = ApplicationRequiredDocument.objects.get(application=app, doc_type_id=doc_type_id)
        except ApplicationRequiredDocument.DoesNotExist:
            log_action("attach_document", student_id, app_id=app.id, outcome="error", 
                      extra={"error": "doc_type_not_required", "doc_type_id": doc_type_id}, start_time=start_time)
            return error_response(
                "doc_type_id not required for this application.", 
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                {"doc_type_id": doc_type_id}
            )

        attached_count = ApplicationDocument.objects.filter(application=app, doc_type_id=doc_type_id).count()
        if attached_count >= req.max_items:
            log_action("attach_document", student_id, app_id=app.id, outcome="error", 
                      extra={"error": "max_items_reached", "max_items": req.max_items, "current_count": attached_count}, 
                      start_time=start_time)
            return error_response(
                "max_items reached for this document type.", 
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                {
                    "max_items": req.max_items,
                    "current_count": attached_count,
                    "doc_type_id": doc_type_id
                }
            )

        try:
            sd = get_student_document(student_document_id)
        except StudentDocumentNotFound:
            log_action("attach_document", student_id, app_id=app.id, outcome="error", 
                      extra={"error": "document_not_found", "document_id": student_document_id}, 
                      start_time=start_time)
            return error_response(
                "student_document not found.", 
                status.HTTP_404_NOT_FOUND,
                {"document_id": student_document_id}
            )
        except DocumentsError as e:
            log_action("attach_document", student_id, app_id=app.id, outcome="error", 
                      extra={"error": "upstream_error", "message": str(e)}, 
                      start_time=start_time)
            return error_response(
                f"Upstream Documents error: {e}", 
                status.HTTP_502_BAD_GATEWAY
            )

        if str(sd.get("user_id")) != str(student_id):
            log_action("attach_document", student_id, app_id=app.id, outcome="error", 
                      extra={"error": "document_not_owned", "document_id": student_document_id}, 
                      start_time=start_time)
            return error_response(
                "student_document does not belong to current user.",
                status.HTTP_403_FORBIDDEN,
                {"document_id": student_document_id}
            )
        if sd.get("status") != "clean":
            log_action("attach_document", student_id, app_id=app.id, outcome="error", 
                      extra={"error": "document_not_clean", "status": sd.get("status")}, 
                      start_time=start_time)
            return error_response(
                "student_document status must be 'clean'.",
                status.HTTP_409_CONFLICT,
                {"document_id": student_document_id, "status": sd.get("status")}
            )
        if str(sd.get("doc_type_id")) != doc_type_id:
            log_action("attach_document", student_id, app_id=app.id, outcome="error", 
                      extra={"error": "doc_type_mismatch", "payload_type": doc_type_id, "document_type": str(sd.get("doc_type_id"))}, 
                      start_time=start_time)

        return error_response(
            "doc_type_id mismatch between payload and student_document.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            {"payload_type": doc_type_id, "document_type": str(sd.get("doc_type_id"))}
        )

        try:
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
            
            log_action("attach_document", student_id, app_id=app.id, outcome="success", 
                     extra={"doc_type_id": doc_type_id, "student_document_id": student_document_id}, 
                     start_time=start_time)

            return Response(
                {
                    "id": str(link.id),
                    "application_id": str(app.id),
                    "doc_type_id": doc_type_id,
                    "student_document_id": student_document_id,
                },
                status=201,
            )
        except Exception as e:
            log_action("attach_document", student_id, app_id=app.id, outcome="error", 
                     extra={"error": "creation_error", "message": str(e)}, 
                     start_time=start_time)
            raise
        
    @action(detail=True, methods=["post"], url_path="transition")
    @transaction.atomic
    @validate_uuid_params('pk')
    def transition(self, request, pk=None, transition_data=None):
        """
        Transition an application from one status to another based on defined rules.
        
        Request body must include "transition_type" field with one of the following values:
        - submit: Draft -> Submitted (student)
        - start_review: Submitted -> UnderReview (staff)
        - offer: UnderReview -> Offer (staff)
        - reject: UnderReview|Offer -> Rejected (staff)
        - withdraw: Draft|Submitted|UnderReview|Offer -> Withdrawn (student)
        - accept_offer: Offer -> Accepted (student)
        
        Roles are currently determined by X-Role header ("student" or "staff")
        """
        start_time = time.time()
        student_id = current_user_id(request)
        if not student_id:
            log_action("transition", "anonymous", outcome="error", extra={"error": "unauthorized"})
            return error_response("Authentication required", status.HTTP_401_UNAUTHORIZED)
            
        # Use transition_data if provided (for internal calls) or request.data otherwise
        data = transition_data if transition_data is not None else request.data
            
        # Check if transition_type is provided and valid
        transition_type = data.get("transition_type")
        if not transition_type:
            log_action("transition", student_id, outcome="error", 
                     extra={"error": "missing_transition_type"}, start_time=start_time)
            return error_response(
                "transition_type is required", 
                status.HTTP_400_BAD_REQUEST
            )
        
        if transition_type not in TRANSITION_RULES:
            log_action("transition", student_id, outcome="error", 
                     extra={"error": "invalid_transition_type", "provided": transition_type}, 
                     start_time=start_time)
            return error_response(
                f"Invalid transition_type. Must be one of: {', '.join(TRANSITION_RULES.keys())}", 
                status.HTTP_400_BAD_REQUEST
            )
            
        # Get the application
        app = get_object_or_404(Application, pk=pk)
        log_action("transition", student_id, app_id=app.id, outcome="start", 
                 extra={"transition_type": transition_type}, start_time=start_time)
        
        # Check user role
        role = get_user_role(request)
        if not role:
            log_action("transition", student_id, app_id=app.id, outcome="error", 
                     extra={"error": "missing_role"}, start_time=start_time)
            return error_response(
                "X-Role header is required", 
                status.HTTP_400_BAD_REQUEST
            )
            
        # Check if student is the owner of the application
        if role == 'student' and str(app.student_id) != str(student_id):
            log_action("transition", student_id, app_id=app.id, outcome="error", 
                     extra={"error": "forbidden", "role": role}, start_time=start_time)
            return error_response(
                "Forbidden: not your application", 
                status.HTTP_403_FORBIDDEN
            )
            
        # Check if user has the required role for this transition
        rule = TRANSITION_RULES[transition_type]
        if role not in rule['allowed_roles']:
            log_action("transition", student_id, app_id=app.id, outcome="error", 
                     extra={"error": "invalid_role", "role": role, "required_roles": rule['allowed_roles']}, 
                     start_time=start_time)
            return error_response(
                f"Forbidden: {transition_type} requires role {rule['allowed_roles']}", 
                status.HTTP_403_FORBIDDEN
            )
            
        # Check if current status allows this transition
        if app.status not in rule['allowed_from_statuses']:
            # Special handling for submit to match legacy behavior
            if transition_type == 'submit':
                log_action("transition", student_id, app_id=app.id, outcome="error", 
                         extra={"error": "invalid_status_for_submit", "current_status": app.status}, 
                         start_time=start_time)
                return error_response(
                    f"Application cannot be submitted. Current status: {app.status}",
                    status.HTTP_409_CONFLICT
                )
            else:
                log_action("transition", student_id, app_id=app.id, outcome="error", 
                         extra={"error": "invalid_status_transition", "current_status": app.status, 
                               "allowed_statuses": rule['allowed_from_statuses']}, 
                         start_time=start_time)
                return error_response(
                    f"Cannot transition from {app.status} with {transition_type}. Valid from: {rule['allowed_from_statuses']}",
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                )
            
        # For submit transition, we need to validate mandatory documents
        if transition_type == 'submit':
            # Get all required documents for this application
            required_docs = ApplicationRequiredDocument.objects.filter(
                application=app, 
                is_mandatory=True
            )
            
            # Check for missing mandatory documents
            missing_docs = []
            for req_doc in required_docs:
                doc_count = ApplicationDocument.objects.filter(
                    application=app,
                    doc_type_id=req_doc.doc_type_id
                ).count()
                
                if doc_count < req_doc.min_items:
                    missing_docs.append({
                        "doc_type_id": str(req_doc.doc_type_id),
                        "required": req_doc.min_items,
                        "attached": doc_count
                    })
                    
            if missing_docs:
                log_action("transition", student_id, app_id=app.id, outcome="error", 
                         extra={"error": "missing_documents", "missing_count": len(missing_docs)}, 
                         start_time=start_time)
                return error_response(
                    "Missing required documents",
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    {"missing_documents": missing_docs}
                )
                
        # All validations passed, perform the transition
        try:
            old_status = app.status
            app.status = rule['to_status']
            app.save()
            
            # Create event
            note = data.get("note", f"Status changed from {old_status} to {rule['to_status']} via {transition_type}")
            ApplicationsEvent.objects.create(
                application=app,
                actor_id=student_id,
                event_type="status_changed",
                from_status=old_status,
                to_status=rule['to_status'],
                note=note
            )
            
            log_action("transition", student_id, app_id=app.id, outcome="success", 
                     extra={
                         "transition_type": transition_type, 
                         "from_status": old_status, 
                         "to_status": rule['to_status']
                     }, 
                     start_time=start_time)
            
            return Response(ApplicationSerializer(app).data)
        except Exception as e:
            log_action("transition", student_id, app_id=app.id, outcome="error", 
                     extra={"error": "transition_failed", "message": str(e)}, 
                     start_time=start_time)
            raise
        
    @action(detail=True, methods=["get"], url_path="timeline")
    @validate_uuid_params('pk')
    def timeline(self, request, pk=None):
        """
        Get the timeline of events for an application.
        
        Returns a list of events with:
        - event_type
        - from_status
        - to_status
        - note
        - created_at
        - actor_id
        """
        start_time = time.time()
        student_id = current_user_id(request)
        if not student_id:
            log_action("timeline", "anonymous", outcome="error", extra={"error": "unauthorized"})
            return error_response("Authentication required", status.HTTP_401_UNAUTHORIZED)
            
        # Get the application
        app = get_object_or_404(Application, pk=pk)
        log_action("timeline", student_id, app_id=app.id, outcome="start", start_time=start_time)
        
        # Students can only view their own applications
        role = get_user_role(request)
        if role == 'student' and str(app.student_id) != str(student_id):
            log_action("timeline", student_id, app_id=app.id, outcome="error", 
                     extra={"error": "forbidden", "role": role}, start_time=start_time)
            return error_response(
                "Forbidden: not your application", 
                status.HTTP_403_FORBIDDEN,
                {"role": role}
            )
            
        try:
            # Get all events for this application
            events = ApplicationsEvent.objects.filter(application=app).order_by('created_at')
            
            # Format the response
            result = []
            for event in events:
                result.append({
                    "event_type": event.event_type,
                    "from_status": event.from_status,
                    "to_status": getattr(event, 'to_status', None),
                    "note": event.note,
                    "created_at": event.created_at.isoformat(),
                    "actor_id": str(event.actor_id)
                })
            
            log_action("timeline", student_id, app_id=app.id, outcome="success", 
                     extra={"event_count": len(result)}, start_time=start_time)
                     
            return Response(result)
        except Exception as e:
            log_action("timeline", student_id, app_id=app.id, outcome="error", 
                     extra={"error": "retrieval_error", "message": str(e)}, start_time=start_time)
            raise