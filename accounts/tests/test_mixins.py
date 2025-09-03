import pytest
from rest_framework.test import APIRequestFactory
from accounts.mixins import SoftDeleteMixin
from accounts.models import Role
from rest_framework import status

class DummyView(SoftDeleteMixin):
    def get_object(self):
        return self.obj
    def __init__(self, obj):
        self.obj = obj

@pytest.mark.django_db
def test_soft_delete_mixin():
    role = Role.objects.create(code="soft", name="SoftDelete")
    view = DummyView(role)
    factory = APIRequestFactory()
    request = factory.delete("/")
    response = view.destroy(request)
    role.refresh_from_db()
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert role.is_active is False
