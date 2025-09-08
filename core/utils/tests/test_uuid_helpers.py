import pytest
import uuid
from core.utils.uuid_helpers import (
    is_valid_uuid, 
    parse_uuid, 
    uuid_to_str, 
    filter_by_uuids,
    format_uuid_for_display
)

def test_is_valid_uuid():
    # Test with valid UUID object
    valid_uuid = uuid.uuid4()
    assert is_valid_uuid(valid_uuid) is True
    
    # Test with valid UUID string
    valid_uuid_str = str(valid_uuid)
    assert is_valid_uuid(valid_uuid_str) is True
    
    # Test with invalid UUID string
    assert is_valid_uuid("not-a-uuid") is False
    assert is_valid_uuid("123e4567-e89b-12d3-a456-42661417400") is False  # Too short
    
    # Test with None and other types
    assert is_valid_uuid(None) is False
    assert is_valid_uuid(123) is False
    assert is_valid_uuid({}) is False

def test_parse_uuid():
    # Test with valid UUID object
    valid_uuid = uuid.uuid4()
    assert parse_uuid(valid_uuid) == valid_uuid
    
    # Test with valid UUID string
    valid_uuid_str = str(valid_uuid)
    assert parse_uuid(valid_uuid_str) == valid_uuid
    
    # Test with invalid inputs
    assert parse_uuid("not-a-uuid") is None
    assert parse_uuid(None) is None
    assert parse_uuid(123) is None

def test_uuid_to_str():
    # Test with valid UUID
    valid_uuid = uuid.uuid4()
    assert uuid_to_str(valid_uuid) == str(valid_uuid)
    
    # Test with None
    assert uuid_to_str(None) == ""

def test_format_uuid_for_display():
    test_uuid = uuid.UUID('12345678-1234-5678-1234-567812345678')
    
    # Default format (8 chars)
    assert format_uuid_for_display(test_uuid) == "12345678..."
    
    # Custom format
    assert format_uuid_for_display(test_uuid, 4) == "1234..."
    
    # Full display when requested chars exceed UUID length
    assert format_uuid_for_display(test_uuid, 50) == str(test_uuid)
    
    # Handle None and empty values
    assert format_uuid_for_display(None) == ""
    assert format_uuid_for_display("") == ""
