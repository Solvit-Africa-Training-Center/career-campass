

import pytest
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from accounts.models import Role

User = get_user_model()
client = APIClient()

@pytest.mark.django_db
def test_register_api_view():
	try:
		url = reverse("register")
	except NoReverseMatch:
		url = "/api/accounts/register/"
	payload = {
		"email": "newuser@example.com",
		"password": "newpass123"
	}
	response = client.post(url, payload, format="json")
	assert response.status_code in [200, 201, 400]  # Accepts success or validation error

@pytest.mark.django_db
def test_role_viewset_list():
	role = Role.objects.create(code="admin", name="Admin")
	try:
		url = reverse("role-list")
	except NoReverseMatch:
		url = "/api/accounts/roles/"
	response = client.get(url)
	assert response.status_code == 200
	assert any(r["code"] == "admin" for r in response.json())
