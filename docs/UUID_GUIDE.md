# UUID Implementation Guide

## Overview

This project uses UUIDs extensively for primary keys and cross-service references. This document explains the UUID implementation and best practices for working with UUIDs in the Career-Compass project.

## Why UUIDs?

We use UUIDs (Universally Unique Identifiers) instead of auto-incrementing integers for several reasons:

1. **Distributed Systems**: UUIDs allow for distributed generation of IDs without coordination
2. **Microservice Architecture**: UUIDs make cross-service references easier without tight coupling
3. **Security**: UUIDs don't reveal information about record count or creation order
4. **Scalability**: UUIDs allow for horizontal scaling with multiple database instances

## UUID Implementation

### Models

All primary key fields use UUIDs with `uuid4()` as the default generator:

```python
class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # other fields...
```

### Cross-Service References

For references between services, we use `UUIDField` without a foreign key constraint:

```python
class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_id = models.UUIDField(
        help_text="UUID reference to a student in the accounts service",
        db_index=True
    )
    # other fields...
```

### Serializers

We use the `UUIDSerializerMixin` to format UUIDs consistently in API responses:

```python
class ApplicationSerializer(UUIDSerializerMixin, serializers.ModelSerializer):
    id = serializers.UUIDField(format='hex', read_only=True)
    # other fields...
```

### ViewSets

We use the `UUIDViewSetMixin` to validate UUIDs in API requests:

```python
class ApplicationViewSet(UUIDViewSetMixin, viewsets.ViewSet):
    # ViewSet implementation...
```

## UUID Utilities

We provide several utility functions for working with UUIDs in `core/utils/uuid_helpers.py`:

### Validation

```python
# Check if a value is a valid UUID
is_valid_uuid("550e8400-e29b-41d4-a716-446655440000")  # Returns True
is_valid_uuid("not-a-uuid")  # Returns False
```

### Parsing

```python
# Parse a string into a UUID object
uuid_obj = parse_uuid("550e8400-e29b-41d4-a716-446655440000")
```

### Conversion

```python
# Convert a UUID to a string
uuid_str = uuid_to_str(uuid_obj)
```

### Generation

```python
# Generate a new UUID
new_uuid = generate_uuid()
```

### Display Formatting

```python
# Format a UUID for display (showing first 8 chars)
short_uuid = format_uuid_for_display(uuid_obj)  # "550e8400..."
```

### Bulk Validation

```python
# Validate a list of UUIDs and return only valid ones
valid_uuids = validate_uuid_list(["550e8400-e29b-41d4-a716-446655440000", "not-a-uuid"])
```

### QuerySet Filtering

```python
# Filter a queryset by a list of UUIDs
filtered_qs = filter_by_uuids(Application.objects.all(), "student_id", uuid_list)
```

## Best Practices

### 1. Always Validate UUIDs

Always validate UUIDs coming from user input or external sources:

```python
if not is_valid_uuid(user_input_uuid):
    return Response({"error": "Invalid UUID format"}, status=400)
```

### 2. Use UUID Serializer Fields

Use the `UUIDRelatedField` for cross-service references:

```python
class ApplicationCreateSerializer(serializers.Serializer):
    program_id = UUIDRelatedField(
        related_model="Program",
        service_name="catalog"
    )
```

### 3. Add Database Indexes

Always add database indexes to UUID fields used for filtering or joining:

```python
class Meta:
    indexes = [
        models.Index(fields=["student_id"]),
    ]
```

### 4. Format UUIDs Consistently

Use consistent formatting for UUIDs in API responses:

```python
# In serializers
id = serializers.UUIDField(format='hex')
```

### 5. Use UUID Decorators

Use the `validate_uuid_params` decorator for view functions:

```python
@validate_uuid_params('application_id', 'document_id')
def my_view(request, application_id, document_id):
    # This will only execute if both IDs are valid UUIDs
    pass
```

### 6. Handle UUID Errors Gracefully

Provide meaningful error messages when UUID validation fails:

```python
try:
    uuid_obj = parse_uuid(input_value)
    if uuid_obj is None:
        return Response({"error": "Invalid UUID format"}, status=400)
except Exception:
    return Response({"error": "Error processing UUID"}, status=400)
```

## Performance Considerations

While UUIDs offer many benefits, they come with some performance trade-offs:

1. **Size**: UUIDs are 16 bytes compared to 4 bytes for integers
2. **Indexing**: UUIDs are more expensive to index due to their size
3. **Randomness**: UUID v4 values are random which can lead to B-tree index fragmentation

To mitigate these issues:

1. Use proper database indexes on UUID fields
2. Consider using UUID v1 for time-ordered UUIDs if needed
3. In high-volume tables, consider using a secondary integer index for internal operations

## Testing UUID Functionality

To test UUID functionality, use:

```python
import uuid
from core.utils.uuid_helpers import is_valid_uuid, parse_uuid

# Test UUID validation
assert is_valid_uuid(uuid.uuid4())
assert not is_valid_uuid("not-a-uuid")

# Test UUID parsing
uuid_str = "550e8400-e29b-41d4-a716-446655440000"
assert parse_uuid(uuid_str) == uuid.UUID(uuid_str)
assert parse_uuid("not-a-uuid") is None
```

## Conclusion

Using UUIDs throughout the system provides flexibility and scalability benefits, especially in a microservice architecture where services need to reference each other's data without tight coupling. The provided utilities make working with UUIDs easier and more consistent across the codebase.
