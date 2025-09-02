from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomTokenRefreshView, LoginAPIView, LogoutAPIView, UserViewSet, ProfileViewSet, StudentViewSet, AgentViewSet, RoleViewSet

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
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
]
