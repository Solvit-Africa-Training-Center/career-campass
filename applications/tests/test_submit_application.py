import uuid
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from applications.models import Application, ApplicationRequiredDocument, ApplicationDocument, Status
from applications.tests.conftest import create_test_application


@pytest.mark.django_db
class TestSubmitApplication:
    """Tests for the submit application endpoint"""

    def test_submit_application_success(self, authenticated_api_client, mock_current_user_id):
        """Test successfully submitting an application with all required documents"""
        # Arrange
        mock_current_user_id.return_value = "00000000-0000-0000-0000-000000000001"
        app = create_test_application(
            student_id="00000000-0000-0000-0000-000000000001",
            status=Status.DRAFT
        )
        
        # Create required document
        req_doc = ApplicationRequiredDocument.objects.create(
            application=app,
            doc_type_id=uuid.uuid4(),
            is_mandatory=True,
            min_items=1,
            max_items=1
        )
        
        # Attach document
        ApplicationDocument.objects.create(
            application=app,
            doc_type_id=req_doc.doc_type_id,
            student_document_id=uuid.uuid4()
        )
        
        url = reverse('applications-submit-application', kwargs={'pk': str(app.id)})
        
        # Act
        response = authenticated_api_client.post(url)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == Status.SUBMITTED
        
        # Verify database was updated
        app.refresh_from_db()
        assert app.status == Status.SUBMITTED
        
        # Verify event was created
        assert app.events.filter(event_type="status_changed").exists()

    def test_submit_application_missing_documents(self, authenticated_api_client, mock_current_user_id):
        """Test application submission fails when mandatory documents are missing"""
        # Arrange
        mock_current_user_id.return_value = "00000000-0000-0000-0000-000000000001"
        app = create_test_application(
            student_id="00000000-0000-0000-0000-000000000001",
            status=Status.DRAFT
        )
        
        # Create required document with no attachment
        req_doc = ApplicationRequiredDocument.objects.create(
            application=app,
            doc_type_id=uuid.uuid4(),
            is_mandatory=True,
            min_items=1,
            max_items=1
        )
        
        url = reverse('applications-submit-application', kwargs={'pk': str(app.id)})
        
        # Act
        response = authenticated_api_client.post(url)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert 'missing_documents' in response.data
        assert len(response.data['missing_documents']) == 1
        assert response.data['missing_documents'][0]['doc_type_id'] == str(req_doc.doc_type_id)
        
        # Verify status was not changed
        app.refresh_from_db()
        assert app.status == Status.DRAFT

    def test_submit_application_not_draft(self, authenticated_api_client, mock_current_user_id):
        """Test application submission fails when application is not in Draft status"""
        # Arrange
        mock_current_user_id.return_value = "00000000-0000-0000-0000-000000000001"
        app = create_test_application(
            student_id="00000000-0000-0000-0000-000000000001",
            status=Status.SUBMITTED  # Already submitted
        )
        
        url = reverse('applications-submit-application', kwargs={'pk': str(app.id)})
        
        # Act
        response = authenticated_api_client.post(url)
        
        # Assert
        assert response.status_code == status.HTTP_409_CONFLICT
        assert 'cannot be submitted' in response.data['detail']

    def test_submit_application_not_owner(self, authenticated_api_client, mock_current_user_id):
        """Test application submission fails when user is not the application owner"""
        # Arrange
        mock_current_user_id.return_value = "00000000-0000-0000-0000-000000000002"  # Different user
        app = create_test_application(
            student_id="00000000-0000-0000-0000-000000000001",
            status=Status.DRAFT
        )
        
        url = reverse('applications-submit-application', kwargs={'pk': str(app.id)})
        
        # Act
        response = authenticated_api_client.post(url)
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_submit_application_unauthenticated(self, api_client, mock_current_user_id):
        """Test application submission fails when user is not authenticated"""
        # Arrange
        mock_current_user_id.return_value = None  # Not authenticated
        app = create_test_application(
            student_id="00000000-0000-0000-0000-000000000001",
            status=Status.DRAFT
        )
        
        url = reverse('applications-submit-application', kwargs={'pk': str(app.id)})
        
        # Act
        response = api_client.post(url)  # Use non-authenticated client
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
