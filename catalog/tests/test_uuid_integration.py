import pytest
import uuid
from django.urls import reverse
from rest_framework.test import APIClient
from catalog.models import Institution, Program

@pytest.mark.django_db
class TestUUIDIntegration:
    """
    Test case to validate UUID integration across the project
    """
    
    @pytest.fixture
    def setup_data(self):
        """Set up test data with UUIDs"""
        # Create test institution with UUID
        institution = Institution.objects.create(
            official_name="Test University",
            type="University",
            country="Test Country"
        )
        
        # Create test program with UUID
        program = Program.objects.create(
            institution=institution,
            name="Test Program",
            description="Test description",
            duration=24,
            language="English"
        )
        
        return {
            "institution": institution,
            "program": program
        }
    
    def test_uuid_retrieval(self, setup_data):
        """Test retrieving objects by UUID"""
        institution = setup_data["institution"]
        program = setup_data["program"]
        
        # Verify UUIDs are properly assigned
        assert isinstance(institution.id, uuid.UUID)
        assert isinstance(program.id, uuid.UUID)
        
        # Test direct retrieval by UUID
        retrieved_institution = Institution.objects.get(id=institution.id)
        assert retrieved_institution.official_name == "Test University"
        
        retrieved_program = Program.objects.get(id=program.id)
        assert retrieved_program.name == "Test Program"
    
    def test_uuid_api_response(self, setup_data, client):
        """Test UUID formatting in API responses"""
        institution = setup_data["institution"]
        
        # Make API request
        response = client.get(
            reverse('institution-detail', kwargs={'pk': institution.id})
        )
        
        # Verify response
        assert response.status_code == 200
        
        # Check UUID is properly formatted in response
        assert response.data["id"] == str(institution.id)
    
    def test_invalid_uuid_api_request(self, client):
        """Test error handling for invalid UUIDs"""
        # Try to access with invalid UUID
        response = client.get(
            reverse('institution-detail', kwargs={'pk': 'not-a-uuid'})
        )
        
        # Verify appropriate error response
        assert response.status_code == 400
        assert "Invalid UUID format" in response.data["detail"]
