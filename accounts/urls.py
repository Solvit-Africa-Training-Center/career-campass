from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomTokenRefreshView, LoginAPIView, LogoutAPIView, UserViewSet, ProfileViewSet, StudentViewSet, AgentViewSet, RoleViewSet,RegisterAPIView,VerifyEmailAPIView,ResendOTPAPIView,RemoveRolesAPIView,AssignRolesAPIView

router = DefaultRouter()
router.register(r"roles", RoleViewSet)
router.register(r"users", UserViewSet)
router.register(r"profiles", ProfileViewSet)
router.register(r"students", StudentViewSet)
router.register(r"agents", AgentViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("verify-email/", VerifyEmailAPIView.as_view(), name="verify_email"),
    path("resend-otp/", ResendOTPAPIView.as_view(), name="resend_otp"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("assign-role/", AssignRolesAPIView.as_view(), name="assign_role"),
    path("remove-role/", RemoveRolesAPIView.as_view(), name="remove_role"),
]
