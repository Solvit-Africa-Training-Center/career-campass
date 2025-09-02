
import pytest
from django.contrib.auth import get_user_model
from accounts.models import Role

User = get_user_model()

@pytest.mark.django_db
def test_role_creation():
	role = Role.objects.create(code="student", name="Student")
	assert role.code == "student"
	assert role.name == "Student"
	assert role.is_active is True

@pytest.mark.django_db
def test_user_creation_assigns_default_role():
	user = User.objects.create_user(email="test@example.com", password="testpass123")
	assert user.email == "test@example.com"
	assert user.roles.filter(code="student").exists()

@pytest.mark.django_db
def test_create_superuser():
	admin = User.objects.create_superuser(email="admin@example.com", password="adminpass123")
	assert admin.is_staff
	assert admin.is_superuser
