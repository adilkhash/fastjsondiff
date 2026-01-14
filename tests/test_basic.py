"""
Tests for basic JSON comparison functionality (User Story 1).

These tests verify the core comparison capabilities:
- Comparing identical JSON objects
- Detecting changed values
- Detecting added keys
- Detecting removed keys
- Detecting array element changes (index-based)
"""

import pytest
import fastjsondiff
from fastjsondiff import DiffType, InvalidJsonError


class TestIdenticalJson:
    """Tests for comparing identical JSON objects."""

    def test_identical_empty_objects(self):
        """Empty objects should produce no differences."""
        result = fastjsondiff.compare("{}", "{}")
        assert len(result) == 0
        assert result.summary.total == 0

    def test_identical_simple_objects(self):
        """Identical simple objects should produce no differences."""
        json_a = '{"name": "test", "value": 42}'
        json_b = '{"name": "test", "value": 42}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 0

    def test_identical_nested_objects(self):
        """Identical nested objects should produce no differences."""
        json_a = '{"user": {"name": "alice", "age": 30}}'
        json_b = '{"user": {"name": "alice", "age": 30}}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 0

    def test_identical_arrays(self):
        """Identical arrays should produce no differences."""
        json_a = '[1, 2, 3, 4, 5]'
        json_b = '[1, 2, 3, 4, 5]'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 0

    def test_identical_complex_structure(self):
        """Complex identical structures should produce no differences."""
        json_a = '{"items": [{"id": 1, "tags": ["a", "b"]}, {"id": 2, "tags": ["c"]}]}'
        json_b = '{"items": [{"id": 1, "tags": ["a", "b"]}, {"id": 2, "tags": ["c"]}]}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 0


class TestChangedValues:
    """Tests for detecting changed values."""

    def test_changed_string_value(self):
        """Detect when a string value changes."""
        json_a = '{"name": "old"}'
        json_b = '{"name": "new"}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.summary.changed == 1
        diff = result[0]
        assert diff.type == DiffType.CHANGED
        assert "name" in diff.path

    def test_changed_number_value(self):
        """Detect when a number value changes."""
        json_a = '{"count": 10}'
        json_b = '{"count": 20}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.summary.changed == 1

    def test_changed_boolean_value(self):
        """Detect when a boolean value changes."""
        json_a = '{"active": true}'
        json_b = '{"active": false}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.summary.changed == 1

    def test_changed_null_to_value(self):
        """Detect when null changes to a value."""
        json_a = '{"data": null}'
        json_b = '{"data": "value"}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.summary.changed == 1

    def test_changed_value_to_null(self):
        """Detect when a value changes to null."""
        json_a = '{"data": "value"}'
        json_b = '{"data": null}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.summary.changed == 1

    def test_changed_type(self):
        """Detect when a value's type changes."""
        json_a = '{"data": 42}'
        json_b = '{"data": "42"}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.summary.changed == 1


class TestAddedKeys:
    """Tests for detecting added keys."""

    def test_added_single_key(self):
        """Detect when a single key is added."""
        json_a = '{}'
        json_b = '{"new_key": "value"}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.summary.added == 1
        diff = result[0]
        assert diff.type == DiffType.ADDED
        assert "new_key" in diff.path

    def test_added_multiple_keys(self):
        """Detect when multiple keys are added."""
        json_a = '{"existing": 1}'
        json_b = '{"existing": 1, "new1": 2, "new2": 3}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 2
        assert result.summary.added == 2

    def test_added_nested_key(self):
        """Detect when a key is added in a nested object."""
        json_a = '{"user": {"name": "alice"}}'
        json_b = '{"user": {"name": "alice", "age": 30}}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.summary.added == 1


class TestRemovedKeys:
    """Tests for detecting removed keys."""

    def test_removed_single_key(self):
        """Detect when a single key is removed."""
        json_a = '{"old_key": "value"}'
        json_b = '{}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.summary.removed == 1
        diff = result[0]
        assert diff.type == DiffType.REMOVED
        assert "old_key" in diff.path

    def test_removed_multiple_keys(self):
        """Detect when multiple keys are removed."""
        json_a = '{"keep": 1, "remove1": 2, "remove2": 3}'
        json_b = '{"keep": 1}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 2
        assert result.summary.removed == 2

    def test_removed_nested_key(self):
        """Detect when a key is removed from a nested object."""
        json_a = '{"user": {"name": "alice", "age": 30}}'
        json_b = '{"user": {"name": "alice"}}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.summary.removed == 1


class TestArrayChanges:
    """Tests for detecting array element changes (index-based)."""

    def test_array_element_changed(self):
        """Detect when an array element's value changes."""
        json_a = '[1, 2, 3]'
        json_b = '[1, 2, 99]'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.summary.changed == 1
        assert "[2]" in result[0].path

    def test_array_element_added(self):
        """Detect when an element is appended to an array."""
        json_a = '[1, 2]'
        json_b = '[1, 2, 3]'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.summary.added == 1
        assert "[2]" in result[0].path

    def test_array_element_removed(self):
        """Detect when an element is removed from an array."""
        json_a = '[1, 2, 3]'
        json_b = '[1, 2]'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.summary.removed == 1

    def test_array_multiple_changes(self):
        """Detect multiple changes in an array."""
        json_a = '[1, 2, 3, 4]'
        json_b = '[1, 99, 3]'
        result = fastjsondiff.compare(json_a, json_b)
        # Element at index 1 changed, element at index 3 removed
        assert len(result) == 2

    def test_array_of_objects_changed(self):
        """Detect changes in an array of objects."""
        json_a = '[{"id": 1}, {"id": 2}]'
        json_b = '[{"id": 1}, {"id": 3}]'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.summary.changed == 1


class TestInputHandling:
    """Tests for input type handling and validation."""

    def test_string_input(self):
        """Accept string input."""
        result = fastjsondiff.compare('{"a": 1}', '{"a": 2}')
        assert len(result) == 1

    def test_bytes_input(self):
        """Accept bytes input."""
        result = fastjsondiff.compare(b'{"a": 1}', b'{"a": 2}')
        assert len(result) == 1

    def test_mixed_input_types(self):
        """Accept mixed string and bytes input."""
        result = fastjsondiff.compare('{"a": 1}', b'{"a": 2}')
        assert len(result) == 1

    def test_invalid_json_first_input(self):
        """Raise InvalidJsonError for invalid JSON in first input."""
        with pytest.raises(InvalidJsonError):
            fastjsondiff.compare('{invalid}', '{}')

    def test_invalid_json_second_input(self):
        """Raise InvalidJsonError for invalid JSON in second input."""
        with pytest.raises(InvalidJsonError):
            fastjsondiff.compare('{}', '{invalid}')

    def test_empty_string_input(self):
        """Raise InvalidJsonError for empty string input."""
        with pytest.raises(InvalidJsonError):
            fastjsondiff.compare('', '{}')

    def test_invalid_type_first_input(self):
        """Raise TypeError for invalid type in first input."""
        with pytest.raises(TypeError):
            fastjsondiff.compare(123, '{}')

    def test_invalid_type_second_input(self):
        """Raise TypeError for invalid type in second input."""
        with pytest.raises(TypeError):
            fastjsondiff.compare('{}', 123)


class TestResultObject:
    """Tests for DiffResult object behavior."""

    def test_len_returns_difference_count(self):
        """len() returns number of differences."""
        result = fastjsondiff.compare('{"a": 1}', '{"a": 2, "b": 3}')
        # One changed + one added
        assert len(result) == 2

    def test_bool_true_when_differences_exist(self):
        """bool() is True when differences exist."""
        result = fastjsondiff.compare('{"a": 1}', '{"a": 2}')
        assert bool(result) is True

    def test_bool_false_when_no_differences(self):
        """bool() is False when no differences exist."""
        result = fastjsondiff.compare('{}', '{}')
        assert bool(result) is False

    def test_iteration_over_differences(self):
        """Can iterate over differences."""
        result = fastjsondiff.compare('{}', '{"a": 1, "b": 2}')
        diffs = list(result)
        assert len(diffs) == 2

    def test_index_access(self):
        """Can access differences by index."""
        result = fastjsondiff.compare('{}', '{"a": 1}')
        diff = result[0]
        assert diff.type == DiffType.ADDED

    def test_summary_totals(self):
        """Summary provides correct totals."""
        json_a = '{"remove": 1, "change": 2}'
        json_b = '{"change": 99, "add": 3}'
        result = fastjsondiff.compare(json_a, json_b)
        assert result.summary.added == 1
        assert result.summary.removed == 1
        assert result.summary.changed == 1
        assert result.summary.total == 3

    def test_filter_by_type(self):
        """Can filter differences by type."""
        json_a = '{"remove": 1, "change": 2}'
        json_b = '{"change": 99, "add": 3}'
        result = fastjsondiff.compare(json_a, json_b)
        added = result.filter(DiffType.ADDED)
        assert len(added) == 1
        removed = result.filter(DiffType.REMOVED)
        assert len(removed) == 1

    def test_metadata_populated(self):
        """Metadata is populated after comparison."""
        result = fastjsondiff.compare('{"a": 1}', '{"a": 2}')
        assert result.metadata.paths_compared > 0
        assert result.metadata.duration_ms >= 0

    def test_to_dict_serialization(self):
        """Can serialize result to dictionary."""
        result = fastjsondiff.compare('{"a": 1}', '{"a": 2}')
        data = result.to_dict()
        assert "differences" in data
        assert "summary" in data
        assert "metadata" in data

    def test_to_json_serialization(self):
        """Can serialize result to JSON string."""
        result = fastjsondiff.compare('{"a": 1}', '{"a": 2}')
        json_str = result.to_json()
        assert isinstance(json_str, str)
        import json
        data = json.loads(json_str)
        assert "differences" in data
