from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import DocumentType, UserDocument

User = get_user_model()

@receiver(post_save, sender=User)
def enforce_user_documents(sender, instance, created, **kwargs):
    """Enforce document requirements for non-admin/staff users"""
    if created and not (instance.is_staff or instance.is_superuser):
        required_doc_types = DocumentType.objects.filter(is_active=True)
        
        if required_doc_types.exists() and not UserDocument.objects.filter(
            user=instance, is_active=True
        ).exists():
            raise ValidationError(
                "Regular users must have at least one document uploaded. "
                "Please upload required documents."
            )