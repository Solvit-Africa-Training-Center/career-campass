from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentTypeViewSet, UserDocumentViewSet, ProgramDocumentViewSet,ApplicationDocumentViewSet

router = DefaultRouter()
router.register(r'document-types', DocumentTypeViewSet)
router.register(r'user-documents', UserDocumentViewSet)
router.register(r'program-documents', ProgramDocumentViewSet)
router.register(r'application-documents',ApplicationDocumentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]