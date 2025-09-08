from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from core.utils.uuid_helpers import is_valid_uuid

def validate_uuid_params(*param_names):
    """
    Decorator to validate UUID parameters in view functions.
    
    Args:
        *param_names: Names of parameters to validate as UUIDs
        
    Returns:
        The decorated function
    
    Example:
        @validate_uuid_params('application_id', 'document_id')
        def my_view(request, application_id, document_id):
            # This will only execute if both IDs are valid UUIDs
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            invalid_params = []
            
            for param_name in param_names:
                if param_name in kwargs:
                    param_value = kwargs.get(param_name)
                    if not is_valid_uuid(param_value):
                        invalid_params.append(param_name)
            
            if invalid_params:
                return Response(
                    {"detail": f"Invalid UUID format for parameters: {', '.join(invalid_params)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator
