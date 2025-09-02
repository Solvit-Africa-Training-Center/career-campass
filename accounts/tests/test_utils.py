import pytest
from django.core import mail
from accounts.utils import send_otp_via_email

@pytest.mark.django_db
def test_send_otp_via_email(settings):
    settings.EMAIL_HOST_USER = "test@example.com"
    send_otp_via_email("receiver@example.com", "123456")
    assert len(mail.outbox) == 1
    assert "123456" in mail.outbox[0].body
    assert mail.outbox[0].to == ["receiver@example.com"]
