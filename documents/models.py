from django.db import models
import uuid
from django.conf import settings
from catalog.models import Program
from cloudinary_storage.storage import MediaCloudinaryStorage


class DocumentType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField() 
    is_active=models.BooleanField(default=True)


    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'document_types'
        ordering = ['name']

class UserDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    document_type = models.OneToOneField(DocumentType, on_delete=models.CASCADE)
    file = models.FileField(upload_to="career/documents/", storage=MediaCloudinaryStorage(), null=True, blank=True)
    issued_date = models.DateField()
    expires_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user} - {self.document_type.name}"
    
    class Meta:
        db_table = 'user_documents'
        ordering = ['-issued_date']

class ProgramDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE)
    is_mandatory = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.program} - {self.document_type.name}"
    
    class Meta:
        db_table = 'program_documents'
        unique_together = ['program', 'document_type']

class ApplicationDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_document = models.ForeignKey(UserDocument, on_delete=models.CASCADE)
    program_document = models.ForeignKey(ProgramDocument, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user_document.user} - {self.program_document.document_type.name}"
    
    class Meta:
        db_table = 'application_documents'
        unique_together = ['user_document', 'program_document']
