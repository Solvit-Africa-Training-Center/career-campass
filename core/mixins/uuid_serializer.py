from rest_framework import serializers

class UUIDSerializerMixin:
    """
    A mixin for serializers to handle UUID fields consistently.
    """
    id = serializers.UUIDField(format='hex', read_only=True)
    
    @classmethod
    def setup_eager_loading(cls, queryset):
        """
        Optimize queryset loading by using select_related and prefetch_related.
        Override in subclasses to add specific fields.
        """
        return queryset
