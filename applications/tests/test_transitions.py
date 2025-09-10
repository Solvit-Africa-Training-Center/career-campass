import uuid
import pytest
from django.urls import reverse
from rest_framework import status

from applications.models import Application, ApplicationRequiredDocument, ApplicationDocument, Status, ApplicationsEvent
from applications.tests.conftest import create_test_application


@pytest.mark.django_db
class TestApplicationTransitions:
    """Tests for application status transitions"""
    
    def test_submit_missing_docs(self, authenticated_api_client, mock_current_user_id):
        """Test submitting an application with missing mandatory documents fails"""
        # Mock the current user ID
        student_id = "00000000-0000-0000-0000-000000000001"
        mock_current_user_id.return_value = student_id
        
        # Create a draft application
        app = create_test_application(
            student_id=student_id,
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
        
        # No document attached, should fail
        url = reverse('applications-transition', kwargs={'pk': str(app.id)})
        data = {
            "transition_type": "submit"
        }
        
        # Act with student role
        authenticated_api_client.credentials(HTTP_X_ROLE='student')
        response = authenticated_api_client.post(url, data)
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert 'missing_documents' in response.data
        
    def test_transition_happy_path(self, authenticated_api_client, mock_current_user_id):
        """Test the complete happy path of transitions"""
        # Mock the current user ID
        student_id = "00000000-0000-0000-0000-000000000001"
        mock_current_user_id.return_value = student_id
        
        # Create a draft application
        app = create_test_application(
            student_id=student_id,
            status=Status.DRAFT
        )
        
        # Create required document and attach it
        doc_type_id = uuid.uuid4()
        req_doc = ApplicationRequiredDocument.objects.create(
            application=app,
            doc_type_id=doc_type_id,
            is_mandatory=True,
            min_items=1,
            max_items=1
        )
        
        ApplicationDocument.objects.create(
            application=app,
            doc_type_id=doc_type_id,
            student_document_id=uuid.uuid4()
        )
        
        url = reverse('applications-transition', kwargs={'pk': str(app.id)})
        
        # Step 1: Submit as student
        authenticated_api_client.credentials(HTTP_X_ROLE='student')
        response = authenticated_api_client.post(url, {"transition_type": "submit"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == Status.SUBMITTED
        
        # Step 2: Start review as staff
        authenticated_api_client.credentials(HTTP_X_ROLE='staff')
        response = authenticated_api_client.post(url, {"transition_type": "start_review"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == Status.UNDER_REVIEW
        
        # Step 3: Make offer as staff
        response = authenticated_api_client.post(url, {"transition_type": "offer"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == Status.OFFER
        
        # Step 4: Accept offer as student
        authenticated_api_client.credentials(HTTP_X_ROLE='student')
        response = authenticated_api_client.post(url, {"transition_type": "accept_offer"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == Status.ACCEPTED
        
    def test_transition_withdraw(self, authenticated_api_client, mock_current_user_id):
        """Test withdrawing an application from different states"""
        # Mock the current user ID
        student_id = "00000000-0000-0000-0000-000000000001"
        mock_current_user_id.return_value = student_id
        
        # Test withdrawing from Draft
        app = create_test_application(
            student_id=student_id,
            status=Status.DRAFT
        )
        
        url = reverse('applications-transition', kwargs={'pk': str(app.id)})
        authenticated_api_client.credentials(HTTP_X_ROLE='student')
        response = authenticated_api_client.post(url, {"transition_type": "withdraw"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == Status.WITHDRAWN
        
        # Test withdrawing from Submitted
        app = create_test_application(
            student_id=student_id,
            status=Status.SUBMITTED
        )
        
        url = reverse('applications-transition', kwargs={'pk': str(app.id)})
        response = authenticated_api_client.post(url, {"transition_type": "withdraw"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == Status.WITHDRAWN
        
        # Test withdrawing from Under Review
        app = create_test_application(
            student_id=student_id,
            status=Status.UNDER_REVIEW
        )
        
        url = reverse('applications-transition', kwargs={'pk': str(app.id)})
        response = authenticated_api_client.post(url, {"transition_type": "withdraw"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == Status.WITHDRAWN
        
        # Test withdrawing from Offer
        app = create_test_application(
            student_id=student_id,
            status=Status.OFFER
        )
        
        url = reverse('applications-transition', kwargs={'pk': str(app.id)})
        response = authenticated_api_client.post(url, {"transition_type": "withdraw"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == Status.WITHDRAWN
        
    def test_transition_reject(self, authenticated_api_client, mock_current_user_id):
        """Test rejecting an application from different states"""
        # Mock the current user ID
        student_id = "00000000-0000-0000-0000-000000000001"
        mock_current_user_id.return_value = student_id
        
        # Test rejecting from Under Review
        app = create_test_application(
            student_id=student_id,
            status=Status.UNDER_REVIEW
        )
        
        url = reverse('applications-transition', kwargs={'pk': str(app.id)})
        authenticated_api_client.credentials(HTTP_X_ROLE='staff')
        response = authenticated_api_client.post(url, {"transition_type": "reject"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == Status.REJECTED
        
        # Test rejecting from Offer
        app = create_test_application(
            student_id=student_id,
            status=Status.OFFER
        )
        
        url = reverse('applications-transition', kwargs={'pk': str(app.id)})
        response = authenticated_api_client.post(url, {"transition_type": "reject"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == Status.REJECTED
        
    def test_forbidden_role(self, authenticated_api_client, mock_current_user_id):
        """Test transitions with forbidden roles"""
        # Mock the current user ID
        student_id = "00000000-0000-0000-0000-000000000001"
        mock_current_user_id.return_value = student_id
        
        # Create an application
        app = create_test_application(
            student_id=student_id,
            status=Status.SUBMITTED
        )
        
        url = reverse('applications-transition', kwargs={'pk': str(app.id)})
        
        # Test student trying to do staff action
        authenticated_api_client.credentials(HTTP_X_ROLE='student')
        response = authenticated_api_client.post(url, {"transition_type": "start_review"})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Test staff trying to do student action (accept_offer)
        app.status = Status.OFFER
        app.save()
        
        authenticated_api_client.credentials(HTTP_X_ROLE='staff')
        response = authenticated_api_client.post(url, {"transition_type": "accept_offer"})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_forbidden_user(self, authenticated_api_client, mock_current_user_id):
        """Test student trying to transition someone else's application"""
        # Mock the current user ID
        student_id = "00000000-0000-0000-0000-000000000001"
        other_student_id = "00000000-0000-0000-0000-000000000002"
        mock_current_user_id.return_value = student_id
        
        # Create an application owned by other_student_id
        app = create_test_application(
            student_id=other_student_id,
            status=Status.DRAFT
        )
        
        # Add a required doc and attachment to make it eligible for submission
        doc_type_id = uuid.uuid4()
        req_doc = ApplicationRequiredDocument.objects.create(
            application=app,
            doc_type_id=doc_type_id,
            is_mandatory=True,
            min_items=1,
            max_items=1
        )
        
        ApplicationDocument.objects.create(
            application=app,
            doc_type_id=doc_type_id,
            student_document_id=uuid.uuid4()
        )
        
        url = reverse('applications-transition', kwargs={'pk': str(app.id)})
        
        # Test student trying to submit someone else's application
        authenticated_api_client.credentials(HTTP_X_ROLE='student')
        response = authenticated_api_client.post(url, {"transition_type": "submit"})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_timeline(self, authenticated_api_client, mock_current_user_id):
        """Test timeline endpoint"""
        # Mock the current user ID
        student_id = "00000000-0000-0000-0000-000000000001"
        mock_current_user_id.return_value = student_id
        
        # Create a draft application
        app = create_test_application(
            student_id=student_id,
            status=Status.DRAFT
        )
        
        # Create some events
        ApplicationsEvent.objects.create(
            application=app,
            actor_id=student_id,
            event_type="created",
            note="Application created"
        )
        
        ApplicationsEvent.objects.create(
            application=app,
            actor_id=student_id,
            event_type="doc_attached",
            note="Document attached"
        )
        
        ApplicationsEvent.objects.create(
            application=app,
            actor_id=student_id,
            event_type="status_changed",
            from_status=Status.DRAFT,
            to_status=Status.SUBMITTED,
            note="Status changed"
        )
        
        # Get timeline
        url = reverse('applications-timeline', kwargs={'pk': str(app.id)})
        authenticated_api_client.credentials(HTTP_X_ROLE='student')
        response = authenticated_api_client.get(url)
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        assert response.data[0]['event_type'] == "created"
        assert response.data[1]['event_type'] == "doc_attached"
        assert response.data[2]['event_type'] == "status_changed"
        assert response.data[2]['from_status'] == Status.DRAFT
        assert response.data[2]['to_status'] == Status.SUBMITTED
