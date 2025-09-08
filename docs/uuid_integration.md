# UUID Integration Across Career Compass

This document describes how UUIDs are integrated across all components of the Career Compass platform.

## Architecture Overview

The Career Compass platform uses UUIDs as primary keys throughout the system for several key benefits:

1. **Global Uniqueness**: UUIDs ensure uniqueness across distributed systems
2. **Security**: Non-sequential IDs prevent enumeration attacks
3. **Scalability**: UUIDs allow client-side ID generation and distributed systems
4. **Consistency**: Uniform approach to identifiers across services

## Implementation Components

### 1. Core Mixins

#### UUIDModelMixin (`core/mixins/uuid_model.py`)
- Provides a consistent way to add UUID as primary key to models
- Used as a base class for models that need UUID primary keys

#### UUIDSerializerMixin (`core/mixins/uuid_serializer.py`)
- Standardizes serialization of UUID fields
- Adds optimization methods for eager loading related objects
- Ensures consistent formatting of UUIDs in API responses

#### UUIDViewSetMixin (`core/mixins/uuid_viewset.py`)
- Adds automatic UUID validation to ViewSet actions
- Provides consistent error responses for invalid UUIDs
- Includes optimization for loading related objects

### 2. Utility Functions

#### UUID Helper Functions (`core/utils/uuid_helpers.py`)
- `is_valid_uuid()`: Validates UUID format
- `parse_uuid()`: Safely converts strings to UUID objects
- `uuid_to_str()`: Converts UUIDs to strings with None handling
- `filter_by_uuids()`: Filters querysets by UUID lists
- `format_uuid_for_display()`: Formats UUIDs for UI display

#### Bulk Operations (`core/utils/bulk_operations.py`)
- `bulk_uuid_lookup()`: Efficiently retrieves multiple objects by UUID
- `missing_uuids()`: Identifies missing UUIDs in result sets
- `paginate_uuid_queryset()`: Optimized pagination for UUID-based models

#### View Decorators (`core/utils/view_decorators.py`)
- `validate_uuid_params()`: Validates UUID parameters in views

#### Serializer Fields (`core/utils/serializer_fields.py`)
- `UUIDRelatedField`: Enhanced UUID field for cross-service references

### 3. Module Integration

#### Applications Module
- Uses UUIDs for application IDs, document IDs, and references
- Integrated with UUIDViewSetMixin for API validation
- Uses UUIDSerializerMixin for consistent serialization
- References external entities via UUID fields with validation

#### Catalog Module
- Institution, Program, and ProgramIntake use UUIDs
- ViewSets inherit from UUIDViewSetMixin
- Serializers use UUIDSerializerMixin
- Optimized database queries with proper indexing

## Database Considerations

### Indexing Strategy
- All UUID fields that are used for lookups are indexed
- Compound indexes for common query patterns (e.g., student_id + status)
- Explicit db_index=True for UUID foreign key references

### Performance Optimizations
- Eager loading with select_related and prefetch_related
- Batch operations for bulk UUID lookups
- Pagination optimized for UUID-based sorting

## API Standards

### Request Handling
- UUID path parameters are automatically validated
- Clear error messages for invalid UUIDs
- Standard format for UUID parameters (no dashes in URLs)

### Response Formatting
- UUIDs returned in hex format without dashes
- Consistent field naming for UUID references (entity_id)
- Documentation includes UUID format expectations

## Testing

Test cases cover:
- UUID validation functions
- Serialization of UUID fields
- API endpoints with UUID parameters
- Error cases with invalid UUIDs

## Future Enhancements

Planned improvements:
- UUID-based ETags for HTTP caching
- UUID-based pagination tokens
- Metrics for UUID-related query performance
- PostgreSQL uuid-ossp extension for better performance

## Using UUIDs in New Components

When adding new models:
1. Use UUIDModelMixin for new models that should have UUID primary keys
2. Add proper DB indexes for UUID fields used in lookups
3. Use UUIDSerializerMixin for serializers
4. Use UUIDViewSetMixin for viewsets
5. Use UUIDRelatedField for cross-service references
6. Document UUID relationships in model help_text
