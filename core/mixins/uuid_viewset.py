from rest_framework import viewsets, status
from rest_framework.response import Response
from core.utils.uuid_helpers import is_valid_uuid

class InvalidUUIDException(Exception):
    """Exception raised for invalid UUID format."""
    pass

class UUIDViewSetMixin:
    """
    Mixin for ViewSets that use UUID as primary key.
    Adds UUID validation to retrieve, update, partial_update, and destroy methods.
    """
    
    def get_object(self):
        """
        Get the object with UUID validation.
        Raises InvalidUUIDException if UUID format is invalid.
        """
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        pk = self.kwargs.get(lookup_url_kwarg)
        
        if not is_valid_uuid(pk):
            raise InvalidUUIDException("Invalid UUID format")
            
        return super().get_object()
        
    def retrieve(self, request, *args, **kwargs):
        """Retrieve with UUID validation"""
        try:
            orig_obj = self.get_object()
        except InvalidUUIDException:
            return Response({"detail": "Invalid UUID format"}, status=status.HTTP_400_BAD_REQUEST)
        return super().retrieve(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Update with UUID validation"""
        try:
            orig_obj = self.get_object()
        except InvalidUUIDException:
            return Response({"detail": "Invalid UUID format"}, status=status.HTTP_400_BAD_REQUEST)
        return super().update(request, *args, **kwargs)
        
    def partial_update(self, request, *args, **kwargs):
        """Partial update with UUID validation"""
        try:
            orig_obj = self.get_object()
        except InvalidUUIDException:
            return Response({"detail": "Invalid UUID format"}, status=status.HTTP_400_BAD_REQUEST)
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Destroy with UUID validation"""
        try:
            orig_obj = self.get_object()
        except InvalidUUIDException:
            return Response({"detail": "Invalid UUID format"}, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)
    
    def get_queryset(self):
        """
        Optimize loading with eager loading from serializer if available
        """
        queryset = super().get_queryset()
        
        if hasattr(self.serializer_class, 'setup_eager_loading'):
            return self.serializer_class.setup_eager_loading(queryset)
            
        return queryset
