from rest_framework import serializers
from core.utils.uuid_helpers import is_valid_uuid, parse_uuid

class UUIDRelatedField(serializers.UUIDField):
    """
    A custom field for UUID relationships that provides better validation and error messages.
    
    This field can be used when dealing with cross-service UUID references.
    """
    
    def __init__(self, **kwargs):
        self.related_model = kwargs.pop('related_model', None)
        self.service_name = kwargs.pop('service_name', None)
        self.allow_null = kwargs.pop('allow_null', False)
        super().__init__(**kwargs)
    
    def to_internal_value(self, data):
        """
        Validate and convert the input value to a UUID instance.
        """
        if data is None and self.allow_null:
            return None
            
        uuid_value = parse_uuid(data)
        if uuid_value is None:
            raise serializers.ValidationError(
                f"Invalid UUID format: '{data}'"
            )
        return uuid_value
    
    def to_representation(self, value):
        """
        Convert UUID to string representation.
        """
        if value is None:
            return None
        return str(value)
    
    def get_error_detail(self):
        """
        Return a more helpful error message.
        """
        related_info = ""
        if self.related_model:
            related_info += f" for {self.related_model}"
        if self.service_name:
            related_info += f" in the {self.service_name} service"
            
        return f"Must be a valid UUID{related_info}"
