import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from catalog.models import Institution, Campus, Program, ProgramFee

@pytest.mark.django_db
def test_institution_crud():
    client = APIClient()
    url = reverse("institution-list")
    data = {"official_name": "Test University", "type": "University", "country": "Testland"}
    response = client.post(url, data, format="json")
    assert response.status_code in (200, 201)
    inst_id = response.data["id"]
    # Retrieve
    url_detail = reverse("institution-detail", args=[inst_id])
    response = client.get(url_detail)
    assert response.status_code == 200
    # Update
    response = client.put(url_detail, {**data, "official_name": "Updated University"}, format="json")
    assert response.status_code == 200
    # Soft delete
    response = client.delete(url_detail)
    assert response.status_code == 204
    inst = Institution.all_objects.get(id=inst_id)
    assert not inst.is_active

@pytest.mark.django_db
def test_program_crud():
    client = APIClient()
    inst = Institution.objects.create(official_name="Test Inst", type="University", country="Testland")
    url = reverse("program-list")
    data = {"institution": inst.id, "name": "Test Program", "duration": 12, "language": "English"}
    response = client.post(url, data, format="json")
    assert response.status_code in (200, 201)
    prog_id = response.data["id"]
    # Retrieve
    url_detail = reverse("program-detail", args=[prog_id])
    response = client.get(url_detail)
    assert response.status_code == 200
    # Update
    response = client.put(url_detail, {**data, "name": "Updated Program"}, format="json")
    assert response.status_code == 200
    # Soft delete
    response = client.delete(url_detail)
    assert response.status_code == 204
    prog = Program.all_objects.get(id=prog_id)
    assert not prog.is_active

@pytest.mark.django_db
def test_program_fee_scholarship():
    inst = Institution.objects.create(official_name="Test Inst", type="University", country="Testland")
    prog = Program.objects.create(institution=inst, name="Test Program", duration=12, language="English")
    fee = ProgramFee.objects.create(program=prog, tuition_amount=10000, tuition_currency="USD", application_fee_amount=100, deposit_amount=500, has_scholarship=True, scholarship_percent=50)
    assert fee.get_tuition_fee() == 5000

@pytest.mark.django_db
def test_campus_crud():
    client = APIClient()
    inst = Institution.objects.create(official_name="Test Inst", type="University", country="Testland")
    url = reverse("campus-list")
    data = {"institution": inst.id, "name": "Main Campus", "city": "Test City", "address": "123 Test St"}
    response = client.post(url, data, format="json")
    assert response.status_code in (200, 201)
    campus_id = response.data["id"]
    url_detail = reverse("campus-detail", args=[campus_id])
    response = client.get(url_detail)
    assert response.status_code == 200
    response = client.put(url_detail, {**data, "name": "Updated Campus"}, format="json")
    assert response.status_code == 200
    response = client.delete(url_detail)
    assert response.status_code == 204
    campus = Campus.all_objects.get(id=campus_id)
    assert not campus.is_active
