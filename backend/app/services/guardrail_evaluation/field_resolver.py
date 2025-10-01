"""
Field path resolution utilities for guardrail evaluation.

This module provides functionality to resolve field paths like "input.items[0].name"
in nested data structures. It supports dot notation for object access and bracket
notation for array indexing.

Supported syntax:
    - Dot notation: "input.query" accesses data["input"]["query"]
    - Array access: "items[0]" accesses data["items"][0]
    - Combined: "data.users[2].email" accesses data["data"]["users"][2]["email"]
    - Nested arrays: "matrix[0][1]" accesses data["matrix"][0][1]

Examples:
    >>> data = {"input": {"query": "hello", "items": [{"name": "foo"}]}}
    >>> resolve_field_value(data, "input.query")
    'hello'
    >>> resolve_field_value(data, "input.items[0].name")
    'foo'

Limitations:
    - Does not support JSONPath advanced features (wildcards, filters, etc.)
    - Array indices must be non-negative integers
    - Field names cannot contain dots or brackets
"""

import re
from typing import Any

from app.services.guardrail_evaluation.exceptions import FieldPathResolutionError


def parse_field_path(path: str) -> list[str | int]:
    """
    Parse field path into list of segments.

    Converts a field path string like "input.items[0].name" into a list
    of path segments: ["input", "items", 0, "name"]

    Args:
        path: Field path string (e.g., "input.query", "items[0].name")

    Returns:
        List of path segments (strings for keys, ints for array indices)

    Raises:
        FieldPathResolutionError: If path syntax is invalid

    Examples:
        >>> parse_field_path("input.query")
        ['input', 'query']
        >>> parse_field_path("items[0]")
        ['items', 0]
        >>> parse_field_path("data.users[2].email")
        ['data', 'users', 2, 'email']
        >>> parse_field_path("matrix[0][1]")
        ['matrix', 0, 1]
    """
    if not path:
        raise FieldPathResolutionError("Path cannot be empty", path)

    segments: list[str | int] = []

    # Regular expression to match path segments:
    # - Field names: alphanumeric and underscore, starting with letter/underscore
    # - Array indices: [0], [123], etc.
    pattern = r"([a-zA-Z_][a-zA-Z0-9_]*)|(\[\d+\])"

    # Find all matches
    matches = re.finditer(pattern, path)
    matched_text = ""

    for match in matches:
        matched_text += match.group()
        if match.group(1):  # Field name
            segments.append(match.group(1))
        elif match.group(2):  # Array index [n]
            index_str = match.group(2)[1:-1]  # Remove [ and ]
            segments.append(int(index_str))

    # Validate that we matched the entire path
    # Remove dots from path for comparison
    path_without_dots = path.replace(".", "")
    if matched_text != path_without_dots:
        raise FieldPathResolutionError(
            f"Invalid path syntax: unexpected characters in path",
            path,
        )

    if not segments:
        raise FieldPathResolutionError("Path contains no valid segments", path)

    return segments


def resolve_field_value(data: dict | list, path: str) -> Any:
    """
    Resolve field value from data using field path.

    Traverses nested data structure following the path segments to retrieve
    the final value.

    Args:
        data: Data structure to traverse (dict or list)
        path: Field path string (e.g., "input.query")

    Returns:
        Value at the specified path

    Raises:
        FieldPathResolutionError: If path cannot be resolved

    Examples:
        >>> data = {"input": {"query": "hello"}}
        >>> resolve_field_value(data, "input.query")
        'hello'
        >>> data = {"items": [{"name": "foo"}, {"name": "bar"}]}
        >>> resolve_field_value(data, "items[1].name")
        'bar'
    """
    segments = parse_field_path(path)
    current_value: Any = data

    for i, segment in enumerate(segments):
        try:
            if isinstance(segment, str):
                # Dictionary key access
                if not isinstance(current_value, dict):
                    raise FieldPathResolutionError(
                        f"Cannot access key '{segment}' on non-dict type {type(current_value).__name__}",
                        path,
                        segment,
                    )
                if segment not in current_value:
                    raise FieldPathResolutionError(
                        f"Key '{segment}' not found in object",
                        path,
                        segment,
                    )
                current_value = current_value[segment]

            elif isinstance(segment, int):
                # Array index access
                if not isinstance(current_value, list):
                    raise FieldPathResolutionError(
                        f"Cannot access index {segment} on non-list type {type(current_value).__name__}",
                        path,
                        segment,
                    )
                if segment < 0:
                    raise FieldPathResolutionError(
                        f"Negative array indices are not supported",
                        path,
                        segment,
                    )
                if segment >= len(current_value):
                    raise FieldPathResolutionError(
                        f"Array index {segment} out of range (length: {len(current_value)})",
                        path,
                        segment,
                    )
                current_value = current_value[segment]

        except FieldPathResolutionError:
            raise
        except Exception as e:
            raise FieldPathResolutionError(
                f"Unexpected error resolving path: {str(e)}",
                path,
                segment,
            )

    return current_value


__all__ = [
    "parse_field_path",
    "resolve_field_value",
]
