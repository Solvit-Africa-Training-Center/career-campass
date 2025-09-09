from rest_framework import viewsets, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema_view, extend_schema
from .models import DocumentType, UserDocument, ProgramDocument,ApplicationDocument
from .serializers import DocumentTypeSerializer, UserDocumentSerializer, ProgramDocumentSerializer,ApplicationDocumentSerializer


class BaseActiveViewSet(viewsets.ModelViewSet):
    """Base viewset with soft delete and no PATCH"""
    
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options']
    
    def get_queryset(self):
        return self.queryset.filter(is_active=True)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(tags=['Document Types']),
    create=extend_schema(tags=['Document Types']),
    retrieve=extend_schema(tags=['Document Types']),
    update=extend_schema(tags=['Document Types']),
    destroy=extend_schema(tags=['Document Types'])
)
class DocumentTypeViewSet(BaseActiveViewSet):
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer


@extend_schema_view(
    list=extend_schema(tags=['User Documents']),
    create=extend_schema(tags=['User Documents']),
    retrieve=extend_schema(tags=['User Documents']),
    update=extend_schema(tags=['User Documents']),
    destroy=extend_schema(tags=['User Documents'])
)
class UserDocumentViewSet(BaseActiveViewSet):
    queryset = UserDocument.objects.all()
    serializer_class = UserDocumentSerializer


@extend_schema_view(
    list=extend_schema(tags=['Program Documents']),
    create=extend_schema(tags=['Program Documents']),
    retrieve=extend_schema(tags=['Program Documents']),
    update=extend_schema(tags=['Program Documents']),
    destroy=extend_schema(tags=['Program Documents'])
)
class ProgramDocumentViewSet(BaseActiveViewSet):
    queryset = ProgramDocument.objects.all()
    serializer_class = ProgramDocumentSerializer

@extend_schema_view(
    list=extend_schema(tags=['Aplication Documents']),
    create=extend_schema(tags=['Aplication Documents']),
    retrieve=extend_schema(tags=['Aplication Documents']),
    update=extend_schema(tags=['Aplication Documents']),
    destroy=extend_schema(tags=['Aplication Documents'])
)
class ApplicationDocumentViewSet(BaseActiveViewSet):
    queryset=ApplicationDocument.objects.all()
    serializer= ApplicationDocumentSerializer    