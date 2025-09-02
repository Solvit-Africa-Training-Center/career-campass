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
        fields = '__all__'
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



class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

class RegisterRequestSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "password"]  # only email and password

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)     # hash the password
        user.is_active = True           # allow login only after verification if needed
        user.is_verified = False        # email verification pending
        user.save()
        return user    
    
class UserRoleSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    role_ids = serializers.ListField(
        child=serializers.IntegerField(), 
        help_text="List of role IDs to assign or remove"
    )    




class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        required=True,
        help_text="Refresh token to blacklist"
    )
