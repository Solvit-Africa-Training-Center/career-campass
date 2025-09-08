# accounts/utils.py
from django.core.mail import send_mail
from django.conf import settings
from .models import Student

def send_otp_via_email(email, otp):
    subject = "Verify your account"
    message = f"Your OTP code is {otp}. Use this to verify your account."
    email_from = settings.EMAIL_HOST_USER
    send_mail(subject, message, email_from, [email])

def get_student_uuid(user_id):
    """
    Get the UUID of a student from their user ID
    """
    try:
        student = Student.objects.get(user_id=user_id)
        return student.uuid
    except Student.DoesNotExist:
        return None
