"""Pytest configuration and shared fixtures for fastjsondiff tests."""

import json
import pytest


@pytest.fixture
def empty_object():
    """Empty JSON object."""
    return "{}"


@pytest.fixture
def empty_array():
    """Empty JSON array."""
    return "[]"


@pytest.fixture
def simple_object():
    """Simple JSON object with primitive values."""
    return json.dumps({"name": "Alice", "age": 30, "active": True})


@pytest.fixture
def simple_object_modified():
    """Simple JSON object with one changed value."""
    return json.dumps({"name": "Alice", "age": 31, "active": True})


@pytest.fixture
def nested_object():
    """Nested JSON object."""
    return json.dumps({
        "user": {
            "name": "Alice",
            "profile": {
                "email": "alice@example.com",
                "settings": {
                    "theme": "dark",
                    "notifications": True
                }
            }
        }
    })


@pytest.fixture
def nested_object_modified():
    """Nested JSON object with deep change."""
    return json.dumps({
        "user": {
            "name": "Alice",
            "profile": {
                "email": "alice@example.com",
                "settings": {
                    "theme": "light",  # Changed
                    "notifications": True
                }
            }
        }
    })


@pytest.fixture
def array_of_objects():
    """Array containing objects."""
    return json.dumps([
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
        {"id": 3, "name": "Charlie"}
    ])


@pytest.fixture
def array_of_objects_modified():
    """Array with one object changed."""
    return json.dumps([
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Robert"},  # Changed
        {"id": 3, "name": "Charlie"}
    ])


def generate_large_json(size_kb: int) -> str:
    """Generate a JSON payload of approximately the specified size in KB."""
    # Each item is roughly 50 bytes
    items_needed = (size_kb * 1024) // 50
    data = {
        "items": [
            {"id": i, "name": f"Item {i}", "value": i * 1.5}
            for i in range(items_needed)
        ]
    }
    return json.dumps(data)


@pytest.fixture
def json_1kb():
    """~1KB JSON payload."""
    return generate_large_json(1)


@pytest.fixture
def json_100kb():
    """~100KB JSON payload."""
    return generate_large_json(100)


@pytest.fixture
def json_1mb():
    """~1MB JSON payload."""
    return generate_large_json(1024)
