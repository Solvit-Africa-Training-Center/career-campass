import uuid
from typing import List, Dict, Any, Set, Optional
from django.db import models
from django.db.models import QuerySet

def bulk_uuid_lookup(
    model_class: models.Model,
    uuid_field: str,
    uuid_list: List[str],
    select_related: Optional[List[str]] = None,
    prefetch_related: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Efficiently look up model instances by a list of UUIDs and return them as a dictionary
    keyed by UUID string.
    
    Args:
        model_class: The Django model class to query
        uuid_field: The field name that contains the UUID
        uuid_list: List of UUID strings to look up
        select_related: Optional list of fields to select_related
        prefetch_related: Optional list of fields to prefetch_related
        
    Returns:
        Dict mapping UUID strings to model instances
    """
    # Convert string UUIDs to actual UUID objects and filter out invalid ones
    valid_uuids = []
    for uuid_str in uuid_list:
        try:
            valid_uuids.append(uuid.UUID(str(uuid_str)))
        except (ValueError, AttributeError, TypeError):
            continue
            
    if not valid_uuids:
        return {}
        
    # Start the query
    queryset = model_class.objects
    
    # Add select_related if specified
    if select_related:
        queryset = queryset.select_related(*select_related)
        
    # Add prefetch_related if specified
    if prefetch_related:
        queryset = queryset.prefetch_related(*prefetch_related)
        
    # Get all objects matching the UUIDs
    filter_kwargs = {f"{uuid_field}__in": valid_uuids}
    objects = queryset.filter(**filter_kwargs)
    
    # Build the lookup dictionary
    result = {}
    uuid_field_getter = lambda obj: getattr(obj, uuid_field)
    
    for obj in objects:
        obj_uuid = uuid_field_getter(obj)
        result[str(obj_uuid)] = obj
        
    return result

def missing_uuids(source_uuids: List[str], found_uuids: Dict[str, Any]) -> Set[str]:
    """
    Find UUIDs from source_uuids that are missing in found_uuids.
    
    Args:
        source_uuids: Original list of UUIDs that were searched for
        found_uuids: Dictionary of UUIDs that were found
        
    Returns:
        Set of UUID strings that are missing
    """
    found_keys = set(found_uuids.keys())
    return set(str(u) for u in source_uuids) - found_keys

def paginate_uuid_queryset(
    queryset: QuerySet,
    page_size: int = 1000,
    uuid_field: str = 'id'
) -> List[Any]:
    """
    Efficiently paginate through a queryset when dealing with UUIDs.
    
    Args:
        queryset: The queryset to paginate
        page_size: Number of records per page
        uuid_field: The UUID field to use for pagination
        
    Returns:
        List of all objects from the queryset
    """
    results = []
    offset = 0
    
    while True:
        batch = list(queryset.order_by(uuid_field)[offset:offset + page_size])
        if not batch:
            break
            
        results.extend(batch)
        offset += page_size
        
    return results
