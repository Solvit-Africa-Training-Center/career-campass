from rest_framework import serializers

class AttachDocumentIn(serializers.Serializer):
    doc_type_id = serializers.UUIDField()
    student_document_id = serializers.UUIDField()
