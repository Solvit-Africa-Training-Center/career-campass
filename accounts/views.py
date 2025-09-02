from rest_framework import viewsets, permissions
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .serializers import LoginSerializer, UserSerializer

from .models import Profile, Student, Agent, Role
from .serializers import (
    UserSerializer, ProfileSerializer, StudentSerializer,
    AgentSerializer, RoleSerializer
)
from .mixins import SoftDeleteMixin

User = get_user_model()

@extend_schema(tags=["Roles"], description="Retrieve, create, update or soft-delete roles.")
class RoleViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    queryset = Role.objects.filter(is_active=True)
    serializer_class = RoleSerializer
    http_method_names = ["get", "post", "put", "delete"]

@extend_schema(tags=["Users"], description="Retrieve, create, update or soft-delete users.")
class UserViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "put", "delete"]

@extend_schema(tags=["Profiles"], description="Retrieve, create, update or soft-delete profiles.")
class ProfileViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    queryset = Profile.objects.filter(is_active=True)
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "put", "delete"]

@extend_schema(tags=["Students"], description="Retrieve, create, update or soft-delete students.")
class StudentViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    queryset = Student.objects.filter(is_active=True)
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "put", "delete"]

@extend_schema(tags=["Agents"], description="Retrieve, create, update or soft-delete agents.")
class AgentViewSet(SoftDeleteMixin, viewsets.ModelViewSet):
    queryset = Agent.objects.filter(is_active=True)
    serializer_class = AgentSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "put", "delete"]



@extend_schema(
    tags=["Authentication"],
    request=LoginSerializer,
    responses={200: LoginSerializer},
    description="User login endpoint. Returns JWT access and refresh tokens."
)
class LoginAPIView(APIView):
    """
    User login and return JWT tokens (access + refresh).
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
    request=None,
    responses={205: None},
    description="Logout endpoint. Blacklists the provided refresh token."
)
class LogoutAPIView(APIView):
    """
    Logout user by blacklisting their refresh token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()  # blacklist the token
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