from rest_framework import serializers
from .models import Application
from core.utils.serializer_fields import UUIDRelatedField
from core.mixins.uuid_serializer import UUIDSerializerMixin

class ApplicationCreateSerializer(serializers.Serializer):
    program_id = UUIDRelatedField(
        help_text="UUID of the program to apply to",
        related_model="Program",
        service_name="catalog"
    )
    intake_id = UUIDRelatedField(
        help_text="UUID of the program intake (semester/session)",
        related_model="ProgramIntake",
        service_name="catalog"
    )

class ApplicationSerializer(UUIDSerializerMixin, serializers.ModelSerializer):
    """Serializer for Application model with formatted UUIDs"""
    id = serializers.UUIDField(format='hex')
    student_id = UUIDRelatedField(
        format='hex',
        related_model="User",
        service_name="accounts"
    )
    program_id = UUIDRelatedField(
        format='hex',
        related_model="Program",
        service_name="catalog"
    )
    intake_id = UUIDRelatedField(
        format='hex',
        related_model="ProgramIntake",
        service_name="catalog"
    )
    
    class Meta:
        model = Application
        fields = ("id", "student_id", "program_id", "intake_id", "status", "created_at", "updated_at")
        