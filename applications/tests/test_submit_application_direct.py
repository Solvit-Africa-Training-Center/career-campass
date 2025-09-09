import uuid
import pytest
from django.db import transaction
from unittest.mock import patch, MagicMock
from applications.models import Application, ApplicationsEvent, ApplicationRequiredDocument, ApplicationDocument, Status
from applications.views import ApplicationViewSet

@pytest.mark.django_db
class TestSubmitApplicationDirect:
    """Tests for the submit application endpoint by directly calling the viewset method"""
    
    def test_submit_application_success(self):
        """Test successfully submitting an application with all required documents"""
        # Create application and documents
        app = Application.objects.create(
            student_id=uuid.uuid4(),
            program_id=uuid.uuid4(),
            intake_id=uuid.uuid4(),
            status=Status.DRAFT
        )
        
        req_doc = ApplicationRequiredDocument.objects.create(
            application=app,
            doc_type_id=uuid.uuid4(),
            is_mandatory=True,
            min_items=1,
            max_items=1
        )
        
        ApplicationDocument.objects.create(
            application=app,
            doc_type_id=req_doc.doc_type_id,
            student_document_id=uuid.uuid4()
        )
        
        # Mock request and view
        request = MagicMock()
        request.user.is_authenticated = True
        viewset = ApplicationViewSet()
        viewset.request = request
        
        # Mock current_user_id to return the student ID
        with patch('applications.views.current_user_id', return_value=str(app.student_id)):
            # Call the submit_application method directly
            with transaction.atomic():
                response = viewset.submit_application(request, pk=str(app.id))
        
        # Check response
        assert response.status_code == 200
        assert response.data['status'] == Status.SUBMITTED
        
        # Verify database was updated
        app.refresh_from_db()
        assert app.status == Status.SUBMITTED
        
        # Verify event was created
        assert ApplicationsEvent.objects.filter(
            application=app,
            event_type="status_changed"
        ).exists()
    
    def test_submit_application_missing_documents(self):
        """Test application submission fails when mandatory documents are missing"""
        # Create application with required document but no attachment
        app = Application.objects.create(
            student_id=uuid.uuid4(),
            program_id=uuid.uuid4(),
            intake_id=uuid.uuid4(),
            status=Status.DRAFT
        )
        
        ApplicationRequiredDocument.objects.create(
            application=app,
            doc_type_id=uuid.uuid4(),
            is_mandatory=True,
            min_items=1,
            max_items=1
        )
        
        # Mock request and view
        request = MagicMock()
        request.user.is_authenticated = True
        viewset = ApplicationViewSet()
        viewset.request = request
        
        # Mock current_user_id to return the student ID
        with patch('applications.views.current_user_id', return_value=str(app.student_id)):
            # Call the submit_application method directly
            with transaction.atomic():
                response = viewset.submit_application(request, pk=str(app.id))
        
        # Check response
        assert response.status_code == 422
        assert 'missing_documents' in response.data
        assert len(response.data['missing_documents']) == 1
        
        # Verify database was not updated
        app.refresh_from_db()
        assert app.status == Status.DRAFT
    
    def test_submit_application_not_draft(self):
        """Test application submission fails when application is not in Draft status"""
        app = Application.objects.create(
            student_id=uuid.uuid4(),
            program_id=uuid.uuid4(),
            intake_id=uuid.uuid4(),
            status=Status.SUBMITTED  # Already submitted
        )
        
        # Mock request and view
        request = MagicMock()
        request.user.is_authenticated = True
        viewset = ApplicationViewSet()
        viewset.request = request
        
        # Mock current_user_id to return the student ID
        with patch('applications.views.current_user_id', return_value=str(app.student_id)):
            # Call the submit_application method directly
            with transaction.atomic():
                response = viewset.submit_application(request, pk=str(app.id))
        
        # Check response
        assert response.status_code == 409
        assert 'cannot be submitted' in response.data['detail']
    
    def test_submit_application_not_owner(self):
        """Test application submission fails when user is not the application owner"""
        app = Application.objects.create(
            student_id=uuid.uuid4(),
            program_id=uuid.uuid4(),
            intake_id=uuid.uuid4(),
            status=Status.DRAFT
        )
        
        # Mock request and view
        request = MagicMock()
        request.user.is_authenticated = True
        viewset = ApplicationViewSet()
        viewset.request = request
        
        # Mock current_user_id to return a different student ID
        different_student_id = uuid.uuid4()
        with patch('applications.views.current_user_id', return_value=str(different_student_id)):
            # Call the submit_application method directly
            with transaction.atomic():
                response = viewset.submit_application(request, pk=str(app.id))
        
        # Check response
        assert response.status_code == 403
        assert 'Forbidden' in response.data['detail']
    
    def test_submit_application_unauthenticated(self):
        """Test application submission fails when user is not authenticated"""
        app = Application.objects.create(
            student_id=uuid.uuid4(),
            program_id=uuid.uuid4(),
            intake_id=uuid.uuid4(),
            status=Status.DRAFT
        )
        
        # Mock request and view
        request = MagicMock()
        request.user.is_authenticated = True  # The view uses current_user_id so this doesn't matter
        viewset = ApplicationViewSet()
        viewset.request = request
        
        # Mock current_user_id to return None (unauthenticated)
        with patch('applications.views.current_user_id', return_value=None):
            # Call the submit_application method directly
            with transaction.atomic():
                response = viewset.submit_application(request, pk=str(app.id))
        
        # Check response
        assert response.status_code == 401
        assert 'Authentication required' in response.data['detail']
