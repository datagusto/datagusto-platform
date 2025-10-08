"""
Tests for field path resolution utilities.
"""

import pytest

from app.services.guardrail_evaluation.exceptions import FieldPathResolutionError
from app.services.guardrail_evaluation.field_resolver import (
    parse_field_path,
    resolve_field_value,
)


class TestParseFieldPath:
    """Tests for parse_field_path function."""

    def test_simple_path(self):
        """Test simple dot-separated path."""
        result = parse_field_path("input.query")
        assert result == ["input", "query"]

    def test_single_field(self):
        """Test single field without dots."""
        result = parse_field_path("query")
        assert result == ["query"]

    def test_nested_path(self):
        """Test deeply nested path."""
        result = parse_field_path("data.user.profile.email")
        assert result == ["data", "user", "profile", "email"]

    def test_array_access(self):
        """Test array index notation."""
        result = parse_field_path("items[0]")
        assert result == ["items", 0]

    def test_nested_array(self):
        """Test nested array access."""
        result = parse_field_path("data.users[2].email")
        assert result == ["data", "users", 2, "email"]

    def test_multiple_arrays(self):
        """Test multiple array indices."""
        result = parse_field_path("matrix[0][1]")
        assert result == ["matrix", 0, 1]

    def test_complex_path(self):
        """Test complex path with mixed notation."""
        result = parse_field_path("input.items[0].data.values[3].name")
        assert result == ["input", "items", 0, "data", "values", 3, "name"]

    def test_empty_path_raises_error(self):
        """Test that empty path raises error."""
        with pytest.raises(FieldPathResolutionError) as exc_info:
            parse_field_path("")
        assert "cannot be empty" in str(exc_info.value).lower()

    def test_invalid_characters_raise_error(self):
        """Test that invalid characters raise error."""
        with pytest.raises(FieldPathResolutionError):
            parse_field_path("input.query!")  # Exclamation mark

    def test_field_names_with_underscore(self):
        """Test field names containing underscores."""
        result = parse_field_path("user_data.first_name")
        assert result == ["user_data", "first_name"]

    def test_field_names_with_numbers(self):
        """Test field names containing numbers."""
        result = parse_field_path("field1.value2")
        assert result == ["field1", "value2"]


class TestResolveFieldValue:
    """Tests for resolve_field_value function."""

    def test_simple_dict_access(self):
        """Test simple dictionary key access."""
        data = {"input": {"query": "hello"}}
        result = resolve_field_value(data, "input.query")
        assert result == "hello"

    def test_nested_dict_access(self):
        """Test deeply nested dictionary access."""
        data = {"data": {"user": {"profile": {"email": "test@example.com"}}}}
        result = resolve_field_value(data, "data.user.profile.email")
        assert result == "test@example.com"

    def test_array_access(self):
        """Test array index access."""
        data = {"items": ["foo", "bar", "baz"]}
        result = resolve_field_value(data, "items[1]")
        assert result == "bar"

    def test_dict_in_array(self):
        """Test accessing dictionary inside array."""
        data = {"items": [{"name": "foo"}, {"name": "bar"}]}
        result = resolve_field_value(data, "items[1].name")
        assert result == "bar"

    def test_nested_arrays(self):
        """Test nested array access."""
        data = {"matrix": [[1, 2, 3], [4, 5, 6]]}
        result = resolve_field_value(data, "matrix[1][2]")
        assert result == 6

    def test_complex_nested_structure(self):
        """Test complex nested structure."""
        data = {
            "input": {
                "users": [
                    {"name": "Alice", "emails": ["alice@example.com"]},
                    {"name": "Bob", "emails": ["bob@example.com", "bob2@example.com"]},
                ]
            }
        }
        result = resolve_field_value(data, "input.users[1].emails[1]")
        assert result == "bob2@example.com"

    def test_nonexistent_key_raises_error(self):
        """Test that accessing non-existent key raises error."""
        data = {"input": {"query": "hello"}}
        with pytest.raises(FieldPathResolutionError) as exc_info:
            resolve_field_value(data, "input.unknown")
        assert "not found" in str(exc_info.value).lower()
        assert exc_info.value.segment == "unknown"

    def test_index_out_of_range_raises_error(self):
        """Test that out-of-range index raises error."""
        data = {"items": ["foo", "bar"]}
        with pytest.raises(FieldPathResolutionError) as exc_info:
            resolve_field_value(data, "items[5]")
        assert "out of range" in str(exc_info.value).lower()
        assert exc_info.value.segment == 5

    def test_type_mismatch_dict_on_array(self):
        """Test accessing dict key on array raises error."""
        data = {"items": ["foo", "bar"]}
        with pytest.raises(FieldPathResolutionError) as exc_info:
            resolve_field_value(data, "items.name")
        assert "non-dict" in str(exc_info.value).lower()

    def test_type_mismatch_array_on_dict(self):
        """Test accessing array index on dict raises error."""
        data = {"input": {"query": "hello"}}
        with pytest.raises(FieldPathResolutionError) as exc_info:
            resolve_field_value(data, "input[0]")
        assert "non-list" in str(exc_info.value).lower()

    def test_various_value_types(self):
        """Test that different value types are returned correctly."""
        data = {
            "string": "hello",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "array": [1, 2, 3],
            "object": {"nested": "value"},
        }
        assert resolve_field_value(data, "string") == "hello"
        assert resolve_field_value(data, "number") == 42
        assert resolve_field_value(data, "float") == 3.14
        assert resolve_field_value(data, "boolean") is True
        assert resolve_field_value(data, "null") is None
        assert resolve_field_value(data, "array") == [1, 2, 3]
        assert resolve_field_value(data, "object") == {"nested": "value"}

    def test_empty_string_value(self):
        """Test that empty string values are resolved correctly."""
        data = {"input": {"query": ""}}
        result = resolve_field_value(data, "input.query")
        assert result == ""

    def test_zero_index(self):
        """Test that zero index works correctly."""
        data = {"items": ["first", "second"]}
        result = resolve_field_value(data, "items[0]")
        assert result == "first"
