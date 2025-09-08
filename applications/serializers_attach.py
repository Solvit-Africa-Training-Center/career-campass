from rest_framework import serializers

from rest_framework import serializers
from core.utils.serializer_fields import UUIDRelatedField

class AttachDocumentIn(serializers.Serializer):
    doc_type_id = UUIDRelatedField(
        help_text="UUID of the document type",
        related_model="DocumentType",
        service_name="catalog"
    )
    student_document_id = UUIDRelatedField(
        help_text="UUID of the student document",
        related_model="StudentDocument",
        service_name="documents"
    )
