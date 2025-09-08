from rest_framework import serializers
from .models import Application

class ApplicationCreateSerializer(serializers.Serializer):
    program_id = serializers.UUIDField()
    intake_id = serializers.UUIDField()

class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ("id", "status")
        