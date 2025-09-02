from rest_framework import status
from rest_framework.response import Response

class SoftDeleteMixin:
    """
    Replace hard delete with soft delete (set is_active=False).
    Works for all models with is_active field.
    """
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if hasattr(instance, "is_active"):
            instance.is_active = False
            instance.save()
            return Response({"detail": "Object soft deleted."}, status=status.HTTP_204_NO_CONTENT)
        return super().destroy(request, *args, **kwargs)
