
import pytest
from django.contrib.auth import get_user_model
from accounts.models import Role
from accounts.serializers import RoleSerializer, UserSerializer

User = get_user_model()

@pytest.mark.django_db
def test_role_serializer():
	role = Role.objects.create(code="agent", name="Agent")
	serializer = RoleSerializer(role)
	data = serializer.data
	assert data["code"] == "agent"
	assert data["name"] == "Agent"

@pytest.mark.django_db
def test_user_serializer_create():
	payload = {
		"email": "user2@example.com",
		"password": "pass1234"
	}
	serializer = UserSerializer(data=payload)
	assert serializer.is_valid(), serializer.errors
	user = serializer.save()
	assert user.email == "user2@example.com"
	assert user.check_password("pass1234")
