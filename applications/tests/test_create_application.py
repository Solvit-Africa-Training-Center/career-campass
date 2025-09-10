import uuid
import pytest
import respx
import httpx
from django.urls import reverse
from rest_framework import status

from applications.models import Application, ApplicationRequiredDocument, ApplicationsEvent


@pytest.mark.django_db
class TestCreateApplication:
    """Tests for the create application endpoint with document snapshot"""

    @respx.mock
    def test_create_application_success(self, authenticated_api_client, mock_current_user_id):
        """Test successfully creating an application with document snapshot"""
        # Mock the current user ID
        student_id = "00000000-0000-0000-0000-000000000001"
        mock_current_user_id.return_value = student_id

        # Create test data
        program_id = "11111111-1111-1111-1111-111111111111"
        intake_id = "22222222-2222-2222-2222-222222222222"
        
        # Mock catalog API responses
        program_docs_url = f"http://127.0.0.1:8000/api/catalog/programs/{program_id}/required-documents"
        student_docs_url = f"http://127.0.0.1:8000/api/catalog/student-required-documents:resolve"

        # Program required documents response
        program_docs_mock = respx.get(program_docs_url).mock(
            return_value=httpx.Response(
                200, 
                json=[
                    {"doc_type_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "is_mandatory": True, "min_items": 1, "max_items": 1},
                    {"doc_type_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "is_mandatory": False, "min_items": 0, "max_items": 3}
                ]
            )
        )

        # Student required documents response
        student_docs_mock = respx.get(f"{student_docs_url}?student_id={student_id}").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"doc_type_id": "cccccccc-cccc-cccc-cccc-cccccccccccc", "is_mandatory": True, "min_items": 1, "max_items": 1},
                    {"doc_type_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "is_mandatory": False, "min_items": 1, "max_items": 2}
                ]
            )
        )

        # Prepare request data
        url = reverse('applications-list')
        data = {
            "program_id": program_id,
            "intake_id": intake_id
        }

        # Act
        response = authenticated_api_client.post(url, data)
        
        # Assert response status and content
        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.data
        assert response.data["program_id"] == program_id
        assert response.data["intake_id"] == intake_id
        assert response.data["status"] == "Draft"

        # Assert API calls were made
        assert program_docs_mock.called
        assert student_docs_mock.called
        
        # Get the created application
        app_id = response.data["id"]
        app = Application.objects.get(id=app_id)
        
        # Verify ApplicationRequiredDocument records were created with merged data
        required_docs = ApplicationRequiredDocument.objects.filter(application=app)
        assert required_docs.count() == 3  # Total unique doc types
        
        # Verify specific merged values for doc_type that appeared in both program and student responses
        common_doc = required_docs.get(doc_type_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa") 
        assert common_doc.is_mandatory is True  # OR operation of True and False
        assert common_doc.min_items == 1  # max(1, 1)
        assert common_doc.max_items == 2  # max(1, 2)
        assert common_doc.source == "program"  # Program takes precedence
        
        # Verify ApplicationEvent was created
        event = ApplicationsEvent.objects.get(application=app)
        assert event.event_type == "created"
        assert event.from_status is None
        assert f"Snapshot {required_docs.count()} required document(s)" in event.note

    @respx.mock
    def test_create_application_program_not_found(self, authenticated_api_client, mock_current_user_id):
        """Test error handling when program is not found"""
        # Mock the current user ID
        student_id = "00000000-0000-0000-0000-000000000001"
        mock_current_user_id.return_value = student_id

        # Create test data
        program_id = "11111111-1111-1111-1111-111111111111"
        intake_id = "22222222-2222-2222-2222-222222222222"
        
        # Mock catalog API responses - 404 for program not found
        program_docs_url = f"http://127.0.0.1:8000/api/catalog/programs/{program_id}/required-documents"
        program_docs_mock = respx.get(program_docs_url).mock(
            return_value=httpx.Response(404, json={"detail": "Program not found"})
        )

        # Prepare request data
        url = reverse('applications-list')
        data = {
            "program_id": program_id,
            "intake_id": intake_id
        }

        # Act
        response = authenticated_api_client.post(url, data)
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Program not found" in response.data["detail"]
        assert program_docs_mock.called
        
        # Verify no Application was created
        assert Application.objects.count() == 0

    @respx.mock
    def test_create_application_catalog_error(self, authenticated_api_client, mock_current_user_id):
        """Test error handling when catalog service returns an error"""
        # Mock the current user ID
        student_id = "00000000-0000-0000-0000-000000000001"
        mock_current_user_id.return_value = student_id

        # Create test data
        program_id = "11111111-1111-1111-1111-111111111111"
        intake_id = "22222222-2222-2222-2222-222222222222"
        
        # Mock catalog API responses - 500 internal server error
        program_docs_url = f"http://127.0.0.1:8000/api/catalog/programs/{program_id}/required-documents"
        program_docs_mock = respx.get(program_docs_url).mock(
            return_value=httpx.Response(500, json={"detail": "Internal server error"})
        )

        # Prepare request data
        url = reverse('applications-list')
        data = {
            "program_id": program_id,
            "intake_id": intake_id
        }

        # Act
        response = authenticated_api_client.post(url, data)
        
        # Assert
        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        assert "Upstream Catalog error" in response.data["detail"]
        assert program_docs_mock.called
        
        # Verify no Application was created
        assert Application.objects.count() == 0
