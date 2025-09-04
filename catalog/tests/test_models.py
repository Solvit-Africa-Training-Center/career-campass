import pytest
from catalog.models import Institution, Campus, Program, ProgramFee

@pytest.mark.django_db
def test_institution_creation():
    inst = Institution.objects.create(
        official_name="Test University",
        type="University",
        country="Testland",
        website="https://test.edu"
    )
    assert inst.official_name == "Test University"
    assert inst.is_active

@pytest.mark.django_db
def test_campus_creation():
    inst = Institution.objects.create(
        official_name="Test University",
        type="University",
        country="Testland"
    )
    campus = Campus.objects.create(
        institution=inst,
        name="Main Campus",
        city="Test City",
        address="123 Test St"
    )
    assert campus.name == "Main Campus"
    assert campus.institution == inst

@pytest.mark.django_db
def test_program_fee_scholarship():
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
    fee = ProgramFee.objects.create(
        program=prog,
        tuition_amount=10000,
        tuition_currency="USD",
        application_fee_amount=100,
        deposit_amount=500,
        has_scholarship=True,
        scholarship_percent=50
    )
    assert fee.get_tuition_fee() == 5000