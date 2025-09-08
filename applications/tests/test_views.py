
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from applications.models import Application, ApplicationRequiredDocument, Status
from applications.integrations.catalog import CatalogError, CatalogNotFound
from unittest.mock import patch
import uuid

@pytest.mark.django_db
def test_application_create_success():
    client = APIClient()
    url = reverse("applications-list")
    program_id = uuid.uuid4()
    intake_id = uuid.uuid4()
    student_id = str(uuid.uuid4())
    with patch("applications.views.get_program_required_documents") as mock_prog, \
         patch("applications.views.resolve_student_required_documents") as mock_student:
        mock_prog.return_value = [
            {"doc_type_id": uuid.uuid4(), "is_mandatory": True, "min_items": 1, "max_items": 1, "source": "program"}
        ]
        mock_student.return_value = []
        response = client.post(
            url,
            {"program_id": program_id, "intake_id": intake_id},
            format="json",
            HTTP_X_USER_ID=student_id
        )
        assert response.status_code == 201
        app = Application.objects.get(id=response.data["id"])
        assert app.status == Status.DRAFT
        assert ApplicationRequiredDocument.objects.filter(application=app).exists()

@pytest.mark.django_db
def test_application_create_invalid_data():
    client = APIClient()
    url = reverse("applications-list")
    student_id = str(uuid.uuid4())
    response = client.post(url, {"program_id": ""}, format="json", HTTP_X_USER_ID=student_id)
    assert response.status_code == 400

@pytest.mark.django_db
def test_application_create_catalog_error():
    client = APIClient()
    url = reverse("applications-list")
    program_id = uuid.uuid4()
    intake_id = uuid.uuid4()
    student_id = str(uuid.uuid4())
    with patch("applications.views.get_program_required_documents") as mock_prog:
        mock_prog.side_effect = CatalogError("Catalog error")
        response = client.post(
            url,
            {"program_id": program_id, "intake_id": intake_id},
            format="json",
            HTTP_X_USER_ID=student_id
        )
        assert response.status_code == 502

@pytest.mark.django_db
def test_application_list_only_own():
    client = APIClient()
    student_id = uuid.uuid4()
    other_id = uuid.uuid4()
    Application.objects.create(student_id=student_id, program_id=uuid.uuid4(), intake_id=uuid.uuid4(), status=Status.DRAFT)
    Application.objects.create(student_id=other_id, program_id=uuid.uuid4(), intake_id=uuid.uuid4(), status=Status.DRAFT)
    url = reverse("applications-list")
    response = client.get(url, HTTP_X_USER_ID=str(student_id))
    assert response.status_code == 200
    assert all(app["id"] for app in response.data)
    assert len(response.data) == 1

@pytest.mark.django_db
def test_attach_document_max_items_exceeded():
    client = APIClient()
    student_id = uuid.uuid4()
    app = Application.objects.create(student_id=student_id, program_id=uuid.uuid4(), intake_id=uuid.uuid4(), status=Status.DRAFT)
    doc_type_id = uuid.uuid4()
    ApplicationRequiredDocument.objects.create(application=app, doc_type_id=doc_type_id, is_mandatory=True, min_items=1, max_items=1, source="program")
    from applications.models import ApplicationDocument
    ApplicationDocument.objects.create(application=app, doc_type_id=doc_type_id, student_document_id=uuid.uuid4())
    with patch("applications.views.get_student_document") as mock_doc:
        mock_doc.return_value = {
            "id": str(uuid.uuid4()),
            "user_id": str(student_id),
            "doc_type_id": str(doc_type_id),
            "status": "clean"
        }
        url = reverse("applications-attach-document", args=[app.id])
        response = client.post(
            url,
            {"doc_type_id": doc_type_id, "student_document_id": uuid.uuid4()},
            format="json",
            HTTP_X_USER_ID=str(student_id)
        )
        assert response.status_code == 422
        assert "max_items" in response.data["detail"]

@pytest.mark.django_db
def test_attach_document_wrong_owner():
    client = APIClient()
    student_id = uuid.uuid4()
    other_id = uuid.uuid4()
    app = Application.objects.create(student_id=student_id, program_id=uuid.uuid4(), intake_id=uuid.uuid4(), status=Status.DRAFT)
    doc_type_id = uuid.uuid4()
    ApplicationRequiredDocument.objects.create(application=app, doc_type_id=doc_type_id, is_mandatory=True, min_items=1, max_items=1, source="program")
    with patch("applications.views.get_student_document") as mock_doc:
        mock_doc.return_value = {
            "id": str(uuid.uuid4()),
            "user_id": str(other_id),
            "doc_type_id": str(doc_type_id),
            "status": "clean"
        }
        url = reverse("applications-attach-document", args=[app.id])
        response = client.post(
            url,
            {"doc_type_id": doc_type_id, "student_document_id": uuid.uuid4()},
            format="json",
            HTTP_X_USER_ID=str(student_id)
        )
        assert response.status_code == 403
        assert "not your application" in response.data["detail"] or "does not belong" in response.data["detail"]

@pytest.mark.django_db
def test_attach_document_status_not_clean():
    client = APIClient()
    student_id = uuid.uuid4()
    app = Application.objects.create(student_id=student_id, program_id=uuid.uuid4(), intake_id=uuid.uuid4(), status=Status.DRAFT)
    doc_type_id = uuid.uuid4()
    ApplicationRequiredDocument.objects.create(application=app, doc_type_id=doc_type_id, is_mandatory=True, min_items=1, max_items=1, source="program")
    with patch("applications.views.get_student_document") as mock_doc:
        mock_doc.return_value = {
            "id": str(uuid.uuid4()),
            "user_id": str(student_id),
            "doc_type_id": str(doc_type_id),
            "status": "infected"
        }
        url = reverse("applications-attach-document", args=[app.id])
        response = client.post(
            url,
            {"doc_type_id": doc_type_id, "student_document_id": uuid.uuid4()},
            format="json",
            HTTP_X_USER_ID=str(student_id)
        )
        assert response.status_code == 409
        assert "status must be 'clean'" in response.data["detail"]

@pytest.mark.django_db
def test_attach_document_doc_type_mismatch():
    client = APIClient()
    student_id = uuid.uuid4()
    app = Application.objects.create(student_id=student_id, program_id=uuid.uuid4(), intake_id=uuid.uuid4(), status=Status.DRAFT)
    doc_type_id = uuid.uuid4()
    ApplicationRequiredDocument.objects.create(application=app, doc_type_id=doc_type_id, is_mandatory=True, min_items=1, max_items=1, source="program")
    with patch("applications.views.get_student_document") as mock_doc:
        mock_doc.return_value = {
            "id": str(uuid.uuid4()),
            "user_id": str(student_id),
            "doc_type_id": str(uuid.uuid4()),  # mismatch
            "status": "clean"
        }
        url = reverse("applications-attach-document", args=[app.id])
        response = client.post(
            url,
            {"doc_type_id": doc_type_id, "student_document_id": uuid.uuid4()},
            format="json",
            HTTP_X_USER_ID=str(student_id)
        )
        assert response.status_code == 422
        assert "doc_type_id mismatch" in response.data["detail"]
