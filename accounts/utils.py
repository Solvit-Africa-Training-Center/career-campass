# accounts/utils.py
from django.core.mail import send_mail
from django.conf import settings
from .models import Student

def send_otp_via_email(email, otp):
    subject = "Verify your account"
    message = f"Your OTP code is {otp}. Use this to verify your account."
    email_from = settings.EMAIL_HOST_USER or 'noreply@careercompass.com'
    
    try:
        # Send email using configured backend (console in debug mode)
        send_mail(subject, message, email_from, [email])
        print(f"✅ OTP {otp} sent to {email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def get_student_uuid(user_id):
    """
    Get the UUID of a student from their user ID (returns the User's UUID)
    """
    try:
        student = Student.objects.get(user_id=user_id)
        return student.user.id  # Return the User's UUID primary key
    except Student.DoesNotExist:
        return None
