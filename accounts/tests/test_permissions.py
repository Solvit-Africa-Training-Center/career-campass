import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from accounts.permissions import HasRolePermission

User = get_user_model()

@pytest.mark.django_db
def test_has_role_permission_grants_access():
    user = User.objects.create_user(email="roleuser@example.com", password="pass123")
    role = user.roles.first()
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = user
    class DummyView:
        required_roles = [role.code]
    perm = HasRolePermission()
    assert perm.has_permission(request, DummyView())

@pytest.mark.django_db
def test_has_role_permission_denies_access():
    user = User.objects.create_user(email="nouser@example.com", password="pass123")
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = user
    class DummyView:
        required_roles = ["admin"]
    perm = HasRolePermission()
    assert not perm.has_permission(request, DummyView())
