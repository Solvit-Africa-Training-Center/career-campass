import uuid
import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from applications.models import Application, Status
from applications.integrations.catalog import CatalogError, CatalogNotFound
from core.mixins.uuid_viewset import InvalidUUIDException

pytestmark = pytest.mark.django_db

class TestApplicationFlowIntegration:
    """
    Test the entire application flow after fixes.
    This ensures all the fixed issues are actually resolved.
    """

    @pytest.fixture
    def api_client(self):
        """Return an authenticated API client"""
        client = APIClient()
        # Mock authentication - replace with actual auth as needed
        with patch('applications.views.current_user_id', return_value=str(uuid.uuid4())):
            yield client

    @patch('applications.views.get_program_required_documents')
    @patch('applications.views.resolve_student_required_documents')
    def test_create_application_success(self, mock_student_docs, mock_program_docs, api_client):
        """Test creating an application with all validations passing"""
        # Setup mocks
        mock_program_docs.return_value = [
            {"doc_type_id": str(uuid.uuid4()), "is_mandatory": True, "min_items": 1, "max_items": 1, "source": "program"}
        ]
        mock_student_docs.return_value = [
            {"doc_type_id": str(uuid.uuid4()), "is_mandatory": False, "min_items": 0, "max_items": 3, "source": "student"}
        ]
        
        # Test data
        data = {
            "program_id": str(uuid.uuid4()),
            "intake_id": str(uuid.uuid4())
        }
        
        # Make request
        url = reverse('application-list')
        response = api_client.post(url, data, format='json')
        
        # Assertions
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['status'] == Status.DRAFT
        assert Application.objects.count() == 1
    
    @patch('applications.views.get_program_required_documents')
    def test_create_application_catalog_error(self, mock_program_docs, api_client):
        """Test creating an application with catalog error"""
        # Setup mock to simulate catalog error
        mock_program_docs.side_effect = CatalogNotFound("Program not found")
        
        # Test data
        data = {
            "program_id": str(uuid.uuid4()),
            "intake_id": str(uuid.uuid4())
        }
        
        # Make request
        url = reverse('application-list')
        response = api_client.post(url, data, format='json')
        
        # Assertions
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Application.objects.count() == 0  # Should roll back transaction
    
    @patch('applications.integrations.catalog._client')
    def test_resolve_student_required_docs_error_handling(self, mock_client):
        """Test that the catalog integration properly handles errors"""
        from applications.integrations.catalog import resolve_student_required_documents
        
        # Setup mock for non-404 error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.is_error = True
        mock_response.text = "Internal Server Error"
        
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        # Test that CatalogError is raised
        with pytest.raises(CatalogError):
            resolve_student_required_documents(str(uuid.uuid4()))
    
    def test_uuid_viewset_exception_handling(self):
        """Test that the UUIDViewSetMixin properly raises exceptions"""
        from core.mixins.uuid_viewset import UUIDViewSetMixin
        
        # Create a test instance
        mixin = UUIDViewSetMixin()
        mixin.kwargs = {"pk": "not-a-uuid"}
        mixin.lookup_field = "pk"
        
        # Test that InvalidUUIDException is raised
        with pytest.raises(InvalidUUIDException):
            mixin.get_object()

    @patch('applications.views.get_object_or_404')
    @patch('applications.views.current_user_id')
    @patch('applications.views.get_student_document')
    def test_attach_document_flow(self, mock_get_doc, mock_user_id, mock_get_obj, api_client):
        """Test the document attachment flow after fixing the duplicate method"""
        # Setup mocks
        student_id = str(uuid.uuid4())
        mock_user_id.return_value = student_id
        
        app = MagicMock()
        app.student_id = student_id
        mock_get_obj.return_value = app
        
        doc_type_id = str(uuid.uuid4())
        student_doc_id = str(uuid.uuid4())
        
        mock_get_doc.return_value = {
            "user_id": student_id,
            "status": "clean",
            "doc_type_id": doc_type_id
        }
        
        # Make request
        url = reverse('application-documents', args=[str(uuid.uuid4())])
        data = {
            "doc_type_id": doc_type_id,
            "student_document_id": student_doc_id
        }
        
        # This will use the correct attach_document method after our fix
        response = api_client.post(url, data, format='json')
        
        # Check that the method was called correctly
        mock_get_obj.assert_called_once()
        mock_get_doc.assert_called_once_with(student_doc_id)
