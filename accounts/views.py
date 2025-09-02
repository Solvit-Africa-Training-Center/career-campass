from rest_framework import viewsets, permissions
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics

from .serializers import LoginSerializer, LogoutSerializer, UserRoleSerializer, UserRoleSerializer, UserSerializer,ResendOTPSerializer,VerifyEmailSerializer,RegisterRequestSerializer

from .models import Profile, Student, Agent, Role
from .serializers import (
    UserSerializer, ProfileSerializer, StudentSerializer,
    AgentSerializer, RoleSerializer
)
from .mixins import SoftDeleteMixin
from .utils import send_otp_via_email

User = get_user_model()

@extend_schema(tags=["Roles"], description="Retrieve, create, update or soft-delete roles.")
class RoleViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    queryset = Role.objects.filter(is_active=True)
    serializer_class = RoleSerializer
    http_method_names = ["get", "post", "put", "delete"]

@extend_schema(
    tags=["Authentication"],
    request=RegisterRequestSerializer,
    description="Register a new user and send OTP for email verification."
)
class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterRequestSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # Create user, inactive until email verified
        user = serializer.save(is_active=True, is_verified=False)
        # Generate OTP
        otp = user.generate_otp()
        # Send OTP via email
        send_otp_via_email(user.email, otp)

@extend_schema(
    tags=["Authentication"],
    request=VerifyEmailSerializer,
    description="Verify user email using OTP."
)
class VerifyEmailAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_otp_valid(otp):
            user.is_verified = True
            user.otp = None
            user.otp_created_at = None
            user.save()
            return Response({"detail": "Email verified successfully."}, status=status.HTTP_200_OK)

        return Response({"detail": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    tags=["Authentication"],
    request=ResendOTPSerializer,
    description="Resend OTP for email verification."
)
class ResendOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_verified:
            return Response({"detail": "Email already verified."}, status=status.HTTP_400_BAD_REQUEST)

        otp = user.generate_otp()
        send_otp_via_email(user.email, otp)
        return Response({"detail": "OTP resent successfully."}, status=status.HTTP_200_OK)
    


@extend_schema(tags=["Users"], description="Retrieve, create, update or soft-delete users.")
class UserViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ["get", "put", "delete"]

@extend_schema(tags=["Profiles"], description="Retrieve, create, update or soft-delete profiles.")
class ProfileViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    queryset = Profile.objects.filter(is_active=True)
    serializer_class = ProfileSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ["get", "post", "put", "delete"]

@extend_schema(tags=["Students"], description="Retrieve, create, update or soft-delete students.")
class StudentViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    queryset = Student.objects.filter(is_active=True)
    serializer_class = StudentSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ["get", "post", "put", "delete"]

@extend_schema(tags=["Agents"], description="Retrieve, create, update or soft-delete agents.")
class AgentViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    queryset = Agent.objects.filter(is_active=True)
    serializer_class = AgentSerializer
    permission_classes = [permissions.AllowAny]
    http_method_names = ["get", "post", "put", "delete"]



@extend_schema(
    tags=["Authentication"],
    request=LoginSerializer,
    responses={200: LoginSerializer},
    description="User login endpoint. Returns JWT access and refresh tokens."
)
class LoginAPIView(APIView):
    """
    User login and return JWT tokens (access + refresh). Only verified users can login.
    """
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = request.data.get("password")
        user = authenticate(username=email, password=password)

        if not user:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({"detail": "User account is inactive."}, status=status.HTTP_403_FORBIDDEN)

        if not user.is_verified:
            return Response({"detail": "Email not verified. Please verify first."}, status=status.HTTP_403_FORBIDDEN)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            "user": {
                "id": user.id,
                "email": user.email,
                "roles": [role.code for role in user.roles.all()],
            },
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Authentication"],
    request=LogoutSerializer,
    responses={205: None},
    description="Logout endpoint. Blacklists the provided refresh token."
)
class LogoutAPIView(APIView):
    """
    Logout user by blacklisting their refresh token.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh"]

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logout successful."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"detail": "Invalid or expired refresh token."}, status=status.HTTP_400_BAD_REQUEST)
        
        
@extend_schema(
    tags=["Authentication"],
    request=None,
    responses={200: None},
    description="Custom token refresh endpoint. Returns new access and refresh tokens."
)
class CustomTokenRefreshView(TokenRefreshView):
    """
    Overrides default token refresh to include user info in the response.
    """
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            return Response({"detail": "Invalid or expired refresh token."}, status=status.HTTP_401_UNAUTHORIZED)

        # Get the new access token
        access_token = serializer.validated_data.get("access")
        refresh_token = request.data.get("refresh")

        # Optionally include user info
        try:
            refresh_obj = RefreshToken(refresh_token)
            user = User.objects.get(id=refresh_obj["user_id"])
            user_data = {
                "id": user.id,
                "email": user.email,
                "roles": [role.code for role in user.roles.all()],
            }
        except Exception:
            user_data = None

        return Response({
            "access": access_token,
            "refresh": refresh_token,  # optionally return the same refresh token
            "user": user_data
        }, status=status.HTTP_200_OK)
    

@extend_schema(
    tags=["Roles"],
    request=UserRoleSerializer,
    responses={200: UserRoleSerializer},
    description="Assign role to user."
)
class AssignRolesAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Assign multiple roles to a user.
        """
        serializer = UserRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data["user_id"]
        role_ids = serializer.validated_data["role_ids"]

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        roles = Role.objects.filter(id__in=role_ids, is_active=True)
        if not roles.exists():
            return Response({"detail": "No valid roles found"}, status=status.HTTP_404_NOT_FOUND)

        user.roles.add(*roles)
        return Response({"detail": f"{roles.count()} role(s) assigned to user {user.email}"}, status=status.HTTP_200_OK)

@extend_schema(
    tags=["Roles"],
    request=UserRoleSerializer,
    responses={200: UserRoleSerializer},
    description="Remove role from user."
)
class RemoveRolesAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Remove multiple roles from a user.
        """
        serializer = UserRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data["user_id"]
        role_ids = serializer.validated_data["role_ids"]

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        roles = Role.objects.filter(id__in=role_ids)
        user.roles.remove(*roles)
        return Response({"detail": f"{roles.count()} role(s) removed from user {user.email}"}, status=status.HTTP_200_OK)