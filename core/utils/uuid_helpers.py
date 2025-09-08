import uuid
from typing import Optional, Union, Any, Dict

def is_valid_uuid(val: Any) -> bool:
    """
    Check if a value is a valid UUID.
    
    Args:
        val: The value to check, can be a string or UUID object
        
    Returns:
        bool: True if the value is a valid UUID, False otherwise
    """
    if isinstance(val, uuid.UUID):
        return True
    
    if not isinstance(val, str):
        return False
        
    try:
        uuid.UUID(val)
        return True
    except (ValueError, AttributeError, TypeError):
        return False

def parse_uuid(val: Any) -> Optional[uuid.UUID]:
    """
    Parse a value into a UUID object.
    
    Args:
        val: The value to parse, can be a string or UUID object
        
    Returns:
        Optional[uuid.UUID]: A UUID object or None if parsing failed
    """
    if isinstance(val, uuid.UUID):
        return val
        
    if not isinstance(val, str):
        return None
        
    try:
        return uuid.UUID(val)
    except (ValueError, AttributeError, TypeError):
        return None
        
def uuid_to_str(val: Optional[uuid.UUID]) -> str:
    """
    Convert a UUID to string, handling None values.
    
    Args:
        val: UUID object or None
        
    Returns:
        str: String representation of UUID or empty string if None
    """
    if val is None:
        return ""
    return str(val)
    
def filter_by_uuids(queryset, field_name: str, uuids: list) -> Any:
    """
    Filter a queryset by a list of UUIDs, handling validation.
    
    Args:
        queryset: The queryset to filter
        field_name: The field name to filter on
        uuids: List of UUID strings or objects
        
    Returns:
        QuerySet: Filtered queryset with only valid UUIDs
    """
    valid_uuids = [uuid for uuid in map(parse_uuid, uuids) if uuid is not None]
    if not valid_uuids:
        return queryset.none()
        
    filter_kwargs = {f"{field_name}__in": valid_uuids}
    return queryset.filter(**filter_kwargs)

def format_uuid_for_display(val: Union[uuid.UUID, str], chars: int = 8) -> str:
    """
    Format a UUID for display by showing only the first N characters.
    
    Args:
        val: UUID object or string
        chars: Number of characters to show
        
    Returns:
        str: Formatted UUID string
    """
    if not val:
        return ""
        
    uuid_str = str(val)
    if len(uuid_str) <= chars:
        return uuid_str
        
    return f"{uuid_str[:chars]}..."
