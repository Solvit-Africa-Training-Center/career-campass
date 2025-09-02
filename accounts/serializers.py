from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from .models import Role, Profile, Student, Agent

User = get_user_model()



class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("id", "code", "name")


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    roles = RoleSerializer(many=True, read_only=True)

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    class Meta:
        model = User
        fields = ("id", "email", "password", "roles", "is_active", "is_staff", "created_at")
        extra_kwargs = {
            "password": {"write_only": True}
        }



class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Profile
        fields = (
            "id", "user", "first_name", "last_name", "birth_date",
            "gender", "country", "city", "phone_number", "avatar", "created_at"
        )



class StudentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Student
        fields = (
            "id", "user", "passport_number", "national_id",
            "current_level", "target_countries", "intended_major", "targeted_fields"
        )



class AgentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Agent
        fields = ("id", "user", "description", "is_active", "is_verified")



class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    id = serializers.CharField(max_length=15, read_only=True)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if not email:
            raise serializers.ValidationError("Email is required.")
        if not password:
            raise serializers.ValidationError("Password is required.")

        user = authenticate(username=email, password=password)
        if user is None:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("User account is inactive.")

        return {
            "id": user.id,
            "email": user.email,
            "roles": [role.code for role in user.roles.all()],
        }
