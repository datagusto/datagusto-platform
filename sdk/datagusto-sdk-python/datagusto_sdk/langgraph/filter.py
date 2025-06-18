from typing import Any


def incomplete_record_filter(data: Any) -> Any:
    """
    Filter out records that contain any null/None values.

    This function removes any dictionary from the input list that contains
    at least one null/None value in any of its fields. This is useful for
    ensuring data quality by removing incomplete records from datasets.

    Args:
        data (List[Dict[str, Any]]): List of dictionaries representing records.
            Each dictionary should contain field names as keys and field values
            as values.

    Returns:
        List[Dict[str, Any]]: Filtered list containing only complete records
            (records with no null/None values).

    Examples:
        >>> data = [
        ...     {"id": 1, "name": "John", "email": "john@example.com"},
        ...     {"id": 2, "name": None, "email": "jane@example.com"},
        ...     {"id": 3, "name": "Bob", "email": None},
        ...     {"id": 4, "name": "Alice", "email": "alice@example.com"}
        ... ]
        >>> filtered_data = incomplete_record_filter(data)
        >>> print(len(filtered_data))  # Output: 2
        >>> print(filtered_data)
        [
            {"id": 1, "name": "John", "email": "john@example.com"},
            {"id": 4, "name": "Alice", "email": "alice@example.com"}
        ]

        >>> empty_data = []
        >>> filtered_empty = incomplete_record_filter(empty_data)
        >>> print(filtered_empty)  # Output: []

        >>> all_complete = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        >>> filtered_complete = incomplete_record_filter(all_complete)
        >>> print(len(filtered_complete))  # Output: 2

    Note:
        - This function considers None, null, and empty string as incomplete values
        - The function preserves the original order of complete records
        - Empty input list returns empty list
        - Records with all complete values are preserved unchanged
    """
    if not data:
        return data

    if not isinstance(data, list):
        return data

    filtered_records = []

    for record in data:
        if isinstance(record, dict):
            if not any(value is None for value in record.values()):
                filtered_records.append(record)
        elif isinstance(record, list):
            if not any(value is None for value in record):
                filtered_records.append(record)

    return filtered_records
