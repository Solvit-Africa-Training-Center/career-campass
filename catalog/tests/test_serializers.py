import pytest
from catalog.models import Institution
from catalog.serializers import InstitutionSerializer

@pytest.mark.django_db
def test_institution_serializer():
    inst = Institution.objects.create(
        official_name="Test University",
        type="University",
        country="Testland",
        website="https://test.edu"
    )
    serializer = InstitutionSerializer(inst)
    data = serializer.data
    assert data["official_name"] == "Test University"
    assert data["website"] == "https://test.edu"