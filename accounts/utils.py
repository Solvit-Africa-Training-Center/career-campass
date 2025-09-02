# accounts/utils.py
from django.core.mail import send_mail
from django.conf import settings

def send_otp_via_email(email, otp):
    subject = "Verify your account"
    message = f"Your OTP code is {otp}. Use this to verify your account."
    email_from = settings.EMAIL_HOST_USER
    send_mail(subject, message, email_from, [email])
