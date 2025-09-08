from rest_framework import serializers
from .models import *

class BaseSoftDeleteSerializer(serializers.ModelSerializer):
    """Base serializer with DRY create, update, list, and soft delete support."""

    def create(self, validated_data):
        """Reusable create logic."""
        instance = self.Meta.model.objects.create(**validated_data)
        return instance

    def update(self, instance, validated_data):
        """Reusable update logic for both full & partial updates."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


    def to_representation(self, instance):
        """Handles both single objects and lists."""
        if isinstance(instance, list):
            return [super().to_representation(obj) for obj in instance]
        return super().to_representation(instance)

class InstitutionSerializer(BaseSoftDeleteSerializer):
    class Meta:
        model = Institution
        fields = "__all__"


class InstitutionStaffSerializer(BaseSoftDeleteSerializer):
    class Meta:
        model = InstitutionStaff
        fields = "__all__"


class CampusSerializer(BaseSoftDeleteSerializer):
    class Meta:
        model = Campus
        fields = "__all__"


class ProgramSerializer(BaseSoftDeleteSerializer):
    class Meta:
        model = Program
        fields = "__all__"


class ProgramIntakeSerializer(BaseSoftDeleteSerializer):
    class Meta:
        model = ProgramIntake
        fields = "__all__"


class ProgramFeeSerializer(BaseSoftDeleteSerializer):
    tuition_fee = serializers.SerializerMethodField()

    class Meta:
        model = ProgramFee
        fields = "__all__"

    def get_tuition_fee(self, obj):
        return obj.get_tuition_fee()


class ProgramFeatureSerializer(BaseSoftDeleteSerializer):
    class Meta:
        model = ProgramFeature
        fields = "__all__"


class AdmissionRequirementSerializer(BaseSoftDeleteSerializer):
    class Meta:
        model = AdmissionRequirement
        fields = "__all__"
