import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from applications.models import Application, Status
import uuid

@pytest.mark.django_db
class TestApplicationsFlow:
    """
    Test the critical path for applications creation and management
    """
    
    def test_application_create_authenticated(self, mocker):
        """Test application creation with a mocked authenticated user"""
        # Mock the JWT authentication
        client = APIClient()
        user_id = uuid.uuid4()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer fake_token')
        
        # Mock the current_user_id function to return our test user
        mocker.patch('applications.views.current_user_id', return_value=str(user_id))
        
        # Mock the catalog integration
        program_reqs = [{"doc_type_id": str(uuid.uuid4()), "is_mandatory": True, "min_items": 1, "max_items": 1}]
        mocker.patch('applications.views.get_program_required_documents', return_value=program_reqs)
        mocker.patch('applications.views.resolve_student_required_documents', return_value=[])
        
        # Prepare request data
        program_id = str(uuid.uuid4())
        intake_id = str(uuid.uuid4())
        request_data = {
            "program_id": program_id,
            "intake_id": intake_id
        }
        
        # Make the request
        response = client.post(reverse('application-list'), request_data, format='json')
        
        # Assert the response
        assert response.status_code == 201
        assert response.data["status"] == Status.DRAFT
        
        # Verify application was created in the database
        app = Application.objects.get(id=response.data["id"])
        assert str(app.student_id) == str(user_id)
        assert str(app.program_id) == program_id
        assert str(app.intake_id) == intake_id
        assert app.status == Status.DRAFT
        
        # Verify required documents were created
        assert app.required_docs.count() == len(program_reqs)
        
    def test_application_create_unauthenticated(self):
        """Test application creation fails without authentication"""
        client = APIClient()
        
        # Prepare request data
        program_id = str(uuid.uuid4())
        intake_id = str(uuid.uuid4())
        request_data = {
            "program_id": program_id,
            "intake_id": intake_id
        }
        
        # Make the request without auth credentials
        response = client.post(reverse('application-list'), request_data, format='json')
        
        # Assert the response
        assert response.status_code == 401
