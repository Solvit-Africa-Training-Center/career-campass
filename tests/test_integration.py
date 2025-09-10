import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from accounts.models import User, Student
from catalog.models import Institution, Program
from applications.models import Application
import uuid
from unittest.mock import patch

@pytest.mark.django_db
def test_user_register_and_apply_for_program():
    client = APIClient()
    
    # Register and verify user
    reg_url = reverse("register")
    email = "integration@example.com"
    password = "testpass123"
    client.post(reg_url, {"email": email, "password": password}, format="json")
    user = User.objects.get(email=email)
    user.is_verified = True
    user.save()
    
    # Create a Student record for this user
    student = Student.objects.create(
        user=user,
        passport_number="TEST123456",
        national_id="TEST654321",
        current_level="undergraduate"
    )
    
    # Login
    login_url = reverse("login")
    resp = client.post(login_url, {"email": email, "password": password}, format="json")
    assert resp.status_code == 200
    
    # Set authentication token using the JWT access token
    access_token = resp.data["tokens"]["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    
    # Create institution and program
    inst = Institution.objects.create(official_name="Integration Inst", type="University", country="Testland")
    prog = Program.objects.create(institution=inst, name="Integration Program", duration=12, language="English")
    
    # Apply for program
    app_url = reverse("applications-list")
    intake_id = uuid.uuid4()
    with patch("applications.views.get_program_required_documents") as mock_prog, \
         patch("applications.views.resolve_student_required_documents") as mock_student:
        mock_prog.return_value = [
            {"doc_type_id": uuid.uuid4(), "is_mandatory": True, "min_items": 1, "max_items": 1, "source": "program"}
        ]
        mock_student.return_value = []
        
        # The user ID will be determined by the authentication token
        response = client.post(
            app_url,
            {"program_id": prog.id, "intake_id": intake_id},
            format="json"
        )
        
        assert response.status_code == 201
        
        # The application should be created with the user's ID
        assert Application.objects.filter(program_id=prog.id).exists()
