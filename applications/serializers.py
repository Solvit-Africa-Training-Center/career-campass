from rest_framework import serializers
from .models import Application, ApplicationsEvent
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


class ApplicationTransitionSerializer(serializers.Serializer):
    """Serializer for application status transitions"""
    transition_type = serializers.CharField(required=True)
    note = serializers.CharField(required=False, allow_blank=True)


class EventSerializer(UUIDSerializerMixin, serializers.ModelSerializer):
    """Serializer for ApplicationsEvent model"""
    actor_id = UUIDRelatedField(
        format='hex',
        related_model="User",
        service_name="accounts"
    )
    
    class Meta:
        model = ApplicationsEvent
        fields = ('event_type', 'from_status', 'to_status', 'note', 'created_at', 'actor_id')
        