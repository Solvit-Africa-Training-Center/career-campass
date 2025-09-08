import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from accounts.models import Role, Profile, Student

User = get_user_model()

@pytest.mark.django_db
def test_register_and_login_flow():
    client = APIClient()
    # Register
    url = reverse("register")
    payload = {"email": "user1@example.com", "password": "testpass123"}
    response = client.post(url, payload, format="json")
    assert response.status_code in (200, 201, 400)
    # Simulate email verification
    user = User.objects.get(email="user1@example.com")
    user.is_verified = True
    user.save()
    # Login
    url = reverse("login")
    response = client.post(url, {"email": "user1@example.com", "password": "testpass123"}, format="json")
    assert response.status_code == 200
    assert "tokens" in response.data

@pytest.mark.django_db
def test_assign_and_remove_role():
    client = APIClient()
    user = User.objects.create_user(email="roleuser@example.com", password="pass1234")
    role = Role.objects.create(code="admin", name="Admin")
    # Assign role
    url = reverse("assign_role")
    # Print the types and values for debugging
    print(f"User ID type: {type(user.id)}, value: {user.id}")
    print(f"Role ID type: {type(role.id)}, value: {role.id}")
    
    # Use actual UUIDs rather than string representation
    payload = {"user_id": user.id, "role_ids": [role.id]}
    response = client.post(url, payload, format="json")
    print(f"Response content: {response.content}")  # Debug output
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.roles.filter(code="admin").exists()
    # Remove role
    url = reverse("remove_role")
    response = client.post(url, {"user_id": user.id, "role_ids": [role.id]}, format="json")
    assert response.status_code == 200
    user.refresh_from_db()
    assert not user.roles.filter(code="admin").exists()

@pytest.mark.django_db
def test_soft_delete_user():
    client = APIClient()
    user = User.objects.create_user(email="softdelete@example.com", password="pass1234")
    url = reverse("user-detail", args=[user.id])
    response = client.delete(url)
    assert response.status_code == 204
    user.refresh_from_db()
    assert not user.is_active

@pytest.mark.django_db
def test_profile_crud():
    client = APIClient()
    user = User.objects.create_user(email="profile@example.com", password="pass1234")
    profile = Profile.objects.create(user=user, first_name="Test", last_name="User")
    url = reverse("profile-detail", args=[profile.id])
    response = client.get(url)
    assert response.status_code == 200
    response = client.put(url, {"first_name": "Updated", "last_name": "User", "user": user.id}, format="json")
    assert response.status_code == 200
    profile.refresh_from_db()
    assert profile.first_name == "Updated"

@pytest.mark.django_db
def test_student_crud():
    client = APIClient()
    user = User.objects.create_user(email="student@example.com", password="pass1234")
    student = Student.objects.create(user=user, national_id="1234567890")
    url = reverse("student-detail", args=[student.id])
    response = client.get(url)
    assert response.status_code == 200
    response = client.put(url, {"national_id": "9876543210", "user": user.id}, format="json")
    assert response.status_code == 200
    student.refresh_from_db()
    assert student.national_id == "9876543210"

@pytest.mark.django_db
def test_login_invalid_credentials():
    client = APIClient()
    url = reverse("login")
    response = client.post(url, {"email": "nouser@example.com", "password": "wrongpass"}, format="json")
    assert response.status_code == 401 or response.status_code == 400

@pytest.mark.django_db
def test_permission_denied_for_unverified_user():
    client = APIClient()
    user = User.objects.create_user(email="unverified@example.com", password="pass1234", is_verified=False)
    url = reverse("login")
    response = client.post(url, {"email": "unverified@example.com", "password": "pass1234"}, format="json")
    assert response.status_code == 403
    assert "verify" in response.data["detail"].lower()
