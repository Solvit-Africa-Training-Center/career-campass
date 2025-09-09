import uuid
import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from applications.models import Application, Status


@pytest.fixture
def api_client():
    """Return an API client for testing."""
    return APIClient()


@pytest.fixture
def mock_current_user_id(monkeypatch):
    """Mock the current_user_id function to return a specific ID."""
    class MockUserID:
        def __init__(self):
            self.return_value = None
            
    mock = MockUserID()
    
    def mock_current_user_id(request):
        return mock.return_value
        
    monkeypatch.setattr('applications.views.current_user_id', mock_current_user_id)
    return mock


def create_test_application(student_id=None, program_id=None, intake_id=None, status=Status.DRAFT):
    """
    Create a test application with default values.
    
    Args:
        student_id: UUID of the student
        program_id: UUID of the program
        intake_id: UUID of the intake
        status: Application status
        
    Returns:
        Application: A newly created application instance
    """
    return Application.objects.create(
        student_id=student_id or uuid.uuid4(),
        program_id=program_id or uuid.uuid4(),
        intake_id=intake_id or uuid.uuid4(),
        status=status,
        created_at=timezone.now(),
    )

@pytest.fixture
def authenticated_api_client(api_client, monkeypatch):
    """Return an authenticated API client for testing."""
    
    # Create a simpler approach by directly mocking request.user
    from django.contrib.auth import get_user_model
    
    # Use a mock user object instead of creating a real one
    # This avoids database operations and potential issues with AUTH_USER_MODEL
    class MockUser:
        id = 1
        is_authenticated = True
        
    mock_user = MockUser()
    
    # Force authenticate the API client
    api_client.force_authenticate(user=mock_user)
    
    # Return the authenticated client
    return api_client
