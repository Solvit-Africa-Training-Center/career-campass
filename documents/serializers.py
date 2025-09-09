from rest_framework import serializers
from .models import DocumentType, UserDocument, ProgramDocument,ApplicationDocument


class BaseActiveSerializer(serializers.ModelSerializer):
    """Base serializer with soft delete functionality"""
    
    def get_queryset(self):
        return self.Meta.model.objects.filter(is_active=True)
    
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()


class DocumentTypeSerializer(BaseActiveSerializer):
    class Meta:
        model = DocumentType
        fields = ['id', 'name', 'description', 'is_active']
        read_only_fields = ['id']


class UserDocumentSerializer(BaseActiveSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    document_type_name = serializers.CharField(source='document_type.name', read_only=True)
    
    class Meta:
        model = UserDocument
        fields = ['id', 'user', 'user_email', 'document_type', 'document_type_name', 
                 'file', 'issued_date', 'expires_date', 'is_active']
        read_only_fields = ['id']


class ProgramDocumentSerializer(BaseActiveSerializer):
    program_name = serializers.CharField(source='program.name', read_only=True)
    document_type_name = serializers.CharField(source='document_type.name', read_only=True)
    
    class Meta:
        model = ProgramDocument
        fields = ['id', 'program', 'program_name', 'document_type', 'document_type_name',
                 'is_mandatory', 'is_active']
        read_only_fields = ['id']


class ApplicationDocumentSerializer(BaseActiveSerializer):
    user_email = serializers.CharField(source='user_document.user.email', read_only=True)
    document_type_name = serializers.CharField(source='program_document.document_type.name', read_only=True)

    class Meta:
        model = ApplicationDocument
        fields = ['id', 'user_document', 'user_email', 'program_document', 'document_type_name',
                 'uploaded_at', 'is_verified', 'is_active']
        read_only_fields = ['id']