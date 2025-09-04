import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from catalog.models import Institution, Campus, Program, ProgramFee

@pytest.mark.django_db
def test_institution_list_view():
    Institution.objects.create(
        official_name="Test University",
        type="University",
        country="Testland"
    )
    client = APIClient()
    url = reverse("institution-list")  # Update if your router uses a different name
    response = client.get(url)
    assert response.status_code == 200
    assert response.data[0]["official_name"] == "Test University"

@pytest.mark.django_db
def test_institution_create_view():
    client = APIClient()
    url = reverse("institution-list")
    data = {
        "official_name": "New University",
        "type": "College",
        "country": "Newland",
        "website": "https://new.edu"
    }
    response = client.post(url, data, format="json")
    assert response.status_code in [200, 201]
    assert response.data["official_name"] == "New University"

@pytest.mark.django_db
def test_campus_create_view():
    inst = Institution.objects.create(
        official_name="Test University",
        type="University",
        country="Testland"
    )
    client = APIClient()
    url = reverse("campus-list")
    data = {
        "institution": inst.id,
        "name": "Main Campus",
        "city": "Test City",
        "address": "123 Test St"
    }
    response = client.post(url, data, format="json")
    assert response.status_code in [200, 201]
    assert response.data["name"] == "Main Campus"

@pytest.mark.django_db
def test_program_create_view():
    inst = Institution.objects.create(
        official_name="Test University",
        type="University",
        country="Testland"
    )
    client = APIClient()
    url = reverse("program-list")
    data = {
        "institution": inst.id,
        "name": "Test Program",
        "description": "A test program",
        "duration": 12,
        "language": "English"
    }
    response = client.post(url, data, format="json")
    assert response.status_code in [200, 201]
    assert response.data["name"] == "Test Program"

@pytest.mark.django_db
def test_program_fee_create_view():
    inst = Institution.objects.create(
        official_name="Test University",
        type="University",
        country="Testland"
    )
    prog = Program.objects.create(
        institution=inst,
        name="Test Program",
        duration=12,
        language="English"
    )
    client = APIClient()
    url = reverse("programfee-list")
    data = {
        "program": prog.id,
        "tuition_amount": "10000.00",
        "tuition_currency": "USD",
        "application_fee_amount": "100.00",
        "deposit_amount": "500.00"
    }
    response = client.post(url, data, format="json")
    assert response.status_code in [200, 201]
    assert response.data["tuition_currency"] == "USD"