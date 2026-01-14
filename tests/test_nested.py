"""
Tests for nested JSON structure comparison (User Story 2).

These tests verify deep nesting capabilities:
- Nested object comparison with full path reporting
- Arrays containing objects
- Deeply nested structures (10+ levels)
"""

import pytest
import fastjsondiff
from fastjsondiff import DiffType


class TestNestedObjects:
    """Tests for nested object comparison."""

    def test_nested_object_change(self):
        """Detect change in nested object with full path."""
        json_a = '{"user": {"name": "alice"}}'
        json_b = '{"user": {"name": "bob"}}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.summary.changed == 1
        # Path should include both levels
        assert "user" in result[0].path
        assert "name" in result[0].path

    def test_deeply_nested_change(self):
        """Detect change in deeply nested structure."""
        json_a = '{"level1": {"level2": {"level3": {"value": 1}}}}'
        json_b = '{"level1": {"level2": {"level3": {"value": 2}}}}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        path = result[0].path
        assert "level1" in path
        assert "level2" in path
        assert "level3" in path
        assert "value" in path

    def test_nested_key_added(self):
        """Detect added key in nested object."""
        json_a = '{"config": {"debug": true}}'
        json_b = '{"config": {"debug": true, "verbose": false}}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.summary.added == 1
        assert "verbose" in result[0].path

    def test_nested_key_removed(self):
        """Detect removed key in nested object."""
        json_a = '{"config": {"debug": true, "verbose": false}}'
        json_b = '{"config": {"debug": true}}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.summary.removed == 1

    def test_multiple_nested_changes(self):
        """Detect multiple changes across nested structure."""
        json_a = '{"user": {"name": "alice", "age": 30}, "settings": {"theme": "light"}}'
        json_b = '{"user": {"name": "bob", "age": 30}, "settings": {"theme": "dark"}}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 2
        assert result.summary.changed == 2


class TestArraysWithObjects:
    """Tests for arrays containing objects."""

    def test_array_object_change(self):
        """Detect change in object within array."""
        json_a = '[{"id": 1, "name": "first"}]'
        json_b = '[{"id": 1, "name": "updated"}]'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        # Path should include array index and key
        assert "[0]" in result[0].path
        assert "name" in result[0].path

    def test_array_nested_object_change(self):
        """Detect change in nested object within array."""
        json_a = '[{"data": {"value": 1}}]'
        json_b = '[{"data": {"value": 2}}]'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        path = result[0].path
        assert "[0]" in path
        assert "data" in path
        assert "value" in path

    def test_multiple_objects_in_array(self):
        """Detect changes across multiple objects in array."""
        json_a = '[{"id": 1}, {"id": 2}, {"id": 3}]'
        json_b = '[{"id": 1}, {"id": 99}, {"id": 3}]'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert "[1]" in result[0].path

    def test_object_added_to_array(self):
        """Detect object added to array."""
        json_a = '[{"id": 1}]'
        json_b = '[{"id": 1}, {"id": 2}]'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.summary.added == 1
        assert "[1]" in result[0].path

    def test_object_removed_from_array(self):
        """Detect object removed from array."""
        json_a = '[{"id": 1}, {"id": 2}]'
        json_b = '[{"id": 1}]'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.summary.removed == 1


class TestDeeplyNestedStructures:
    """Tests for deeply nested structures (10+ levels)."""

    def test_10_levels_deep(self):
        """Handle structure nested 10 levels deep."""
        # Build 10-level nested structure
        json_a = '{"l1":{"l2":{"l3":{"l4":{"l5":{"l6":{"l7":{"l8":{"l9":{"l10":{"value":1}}}}}}}}}}}'
        json_b = '{"l1":{"l2":{"l3":{"l4":{"l5":{"l6":{"l7":{"l8":{"l9":{"l10":{"value":2}}}}}}}}}}}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.metadata.max_depth >= 10

    def test_15_levels_deep(self):
        """Handle structure nested 15 levels deep."""
        # Build 15-level nested structure
        json_a = '{"a":{"b":{"c":{"d":{"e":{"f":{"g":{"h":{"i":{"j":{"k":{"l":{"m":{"n":{"o":1}}}}}}}}}}}}}}}'
        json_b = '{"a":{"b":{"c":{"d":{"e":{"f":{"g":{"h":{"i":{"j":{"k":{"l":{"m":{"n":{"o":2}}}}}}}}}}}}}}}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        assert result.metadata.max_depth >= 15

    def test_mixed_deep_nesting(self):
        """Handle mixed arrays and objects deeply nested."""
        json_a = '{"data": [{"items": [{"nested": {"value": 1}}]}]}'
        json_b = '{"data": [{"items": [{"nested": {"value": 2}}]}]}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 1
        path = result[0].path
        assert "data" in path
        assert "[0]" in path
        assert "items" in path
        assert "nested" in path
        assert "value" in path

    def test_identical_deep_structure(self):
        """Identical deep structures produce no differences."""
        json_a = '{"l1":{"l2":{"l3":{"l4":{"l5":{"value":"same"}}}}}}'
        json_b = '{"l1":{"l2":{"l3":{"l4":{"l5":{"value":"same"}}}}}}'
        result = fastjsondiff.compare(json_a, json_b)
        assert len(result) == 0


class TestPathFormat:
    """Tests for correct path formatting."""

    def test_object_path_dot_notation(self):
        """Object keys use dot notation."""
        json_a = '{"a": {"b": 1}}'
        json_b = '{"a": {"b": 2}}'
        result = fastjsondiff.compare(json_a, json_b)
        # Path should be root.a.b
        path = result[0].path
        assert ".a" in path or "a." in path
        assert ".b" in path or "b" in path

    def test_array_path_bracket_notation(self):
        """Array indices use bracket notation."""
        json_a = '{"items": [1, 2]}'
        json_b = '{"items": [1, 99]}'
        result = fastjsondiff.compare(json_a, json_b)
        # Path should include bracket notation for array index
        assert "[1]" in result[0].path

    def test_mixed_path_notation(self):
        """Mixed structures use correct notation."""
        json_a = '{"data": [{"value": 1}]}'
        json_b = '{"data": [{"value": 2}]}'
        result = fastjsondiff.compare(json_a, json_b)
        path = result[0].path
        # Should have dot for object keys and brackets for array
        assert "data" in path
        assert "[0]" in path
        assert "value" in path


class TestMetadata:
    """Tests for metadata tracking during nested comparison."""

    def test_paths_compared_increases_with_depth(self):
        """More nested structure means more paths compared."""
        shallow = '{"a": 1}'
        deep = '{"a": {"b": {"c": 1}}}'

        result_shallow = fastjsondiff.compare(shallow, shallow)
        result_deep = fastjsondiff.compare(deep, deep)

        assert result_deep.metadata.paths_compared > result_shallow.metadata.paths_compared

    def test_max_depth_tracked(self):
        """Max depth is correctly tracked."""
        json_a = '{"level1": {"level2": {"level3": 1}}}'
        json_b = '{"level1": {"level2": {"level3": 2}}}'
        result = fastjsondiff.compare(json_a, json_b)
        # root -> level1 -> level2 -> level3 = depth 3
        assert result.metadata.max_depth >= 3
