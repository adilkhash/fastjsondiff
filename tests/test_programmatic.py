"""
Tests for programmatic result access (User Story 4).

These tests verify the API for accessing comparison results:
- Iteration over differences
- Filtering by difference type
- Serialization to dict/JSON
- File comparison functionality
"""

import json
import tempfile
from pathlib import Path
import pytest
import fastjsondiff
from fastjsondiff import DiffType, DiffResult, Difference, DiffSummary, DiffMetadata


class TestDifferenceAccess:
    """Tests for accessing individual differences."""

    def test_access_by_index(self):
        """Access differences by index."""
        result = fastjsondiff.compare('{}', '{"a": 1, "b": 2}')
        assert len(result) == 2
        diff0 = result[0]
        diff1 = result[1]
        assert isinstance(diff0, Difference)
        assert isinstance(diff1, Difference)

    def test_negative_index(self):
        """Access differences by negative index."""
        result = fastjsondiff.compare('{}', '{"a": 1, "b": 2}')
        last = result[-1]
        assert isinstance(last, Difference)

    def test_index_out_of_range(self):
        """IndexError for out-of-range index."""
        result = fastjsondiff.compare('{}', '{"a": 1}')
        with pytest.raises(IndexError):
            _ = result[10]

    def test_slice_access(self):
        """Slice access for differences."""
        result = fastjsondiff.compare('{}', '{"a": 1, "b": 2, "c": 3}')
        sliced = result.differences[0:2]
        assert len(sliced) == 2


class TestIteration:
    """Tests for iterating over differences."""

    def test_for_loop_iteration(self):
        """Iterate over differences with for loop."""
        result = fastjsondiff.compare('{}', '{"a": 1, "b": 2}')
        count = 0
        for diff in result:
            count += 1
            assert isinstance(diff, Difference)
        assert count == 2

    def test_list_conversion(self):
        """Convert to list."""
        result = fastjsondiff.compare('{}', '{"a": 1, "b": 2}')
        diff_list = list(result)
        assert len(diff_list) == 2

    def test_comprehension(self):
        """Use in list comprehension."""
        result = fastjsondiff.compare('{}', '{"a": 1, "b": 2}')
        paths = [d.path for d in result]
        assert len(paths) == 2


class TestFiltering:
    """Tests for filtering differences by type."""

    def test_filter_added(self):
        """Filter only added differences."""
        json_a = '{"keep": 1}'
        json_b = '{"keep": 1, "added": 2}'
        result = fastjsondiff.compare(json_a, json_b)
        added = result.filter(DiffType.ADDED)
        assert len(added) == 1
        assert all(d.type == DiffType.ADDED for d in added)

    def test_filter_removed(self):
        """Filter only removed differences."""
        json_a = '{"keep": 1, "removed": 2}'
        json_b = '{"keep": 1}'
        result = fastjsondiff.compare(json_a, json_b)
        removed = result.filter(DiffType.REMOVED)
        assert len(removed) == 1
        assert all(d.type == DiffType.REMOVED for d in removed)

    def test_filter_changed(self):
        """Filter only changed differences."""
        json_a = '{"value": 1}'
        json_b = '{"value": 2}'
        result = fastjsondiff.compare(json_a, json_b)
        changed = result.filter(DiffType.CHANGED)
        assert len(changed) == 1
        assert all(d.type == DiffType.CHANGED for d in changed)

    def test_filter_none_returns_all(self):
        """Filter with None returns all differences."""
        json_a = '{"remove": 1, "change": 2}'
        json_b = '{"change": 99, "add": 3}'
        result = fastjsondiff.compare(json_a, json_b)
        all_diffs = result.filter(None)
        assert len(all_diffs) == 3

    def test_filter_mixed(self):
        """Filter from mixed result."""
        json_a = '{"remove": 1, "change": 2}'
        json_b = '{"change": 99, "add": 3}'
        result = fastjsondiff.compare(json_a, json_b)

        added = result.filter(DiffType.ADDED)
        removed = result.filter(DiffType.REMOVED)
        changed = result.filter(DiffType.CHANGED)

        assert len(added) == 1
        assert len(removed) == 1
        assert len(changed) == 1


class TestSerialization:
    """Tests for serialization capabilities."""

    def test_to_dict(self):
        """Serialize result to dictionary."""
        result = fastjsondiff.compare('{"a": 1}', '{"a": 2}')
        data = result.to_dict()

        assert "differences" in data
        assert "summary" in data
        assert "metadata" in data
        assert isinstance(data["differences"], list)

    def test_to_json(self):
        """Serialize result to JSON string."""
        result = fastjsondiff.compare('{"a": 1}', '{"a": 2}')
        json_str = result.to_json()

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert "differences" in parsed

    def test_to_json_with_indent(self):
        """Serialize result to indented JSON."""
        result = fastjsondiff.compare('{"a": 1}', '{"a": 2}')
        json_str = result.to_json(indent=2)

        assert "\n" in json_str  # Indented JSON has newlines
        parsed = json.loads(json_str)
        assert "differences" in parsed

    def test_difference_to_dict(self):
        """Serialize individual difference to dictionary."""
        result = fastjsondiff.compare('{"a": 1}', '{"a": 2}')
        diff = result[0]
        data = diff.to_dict()

        assert "type" in data
        assert "path" in data
        assert data["type"] == "changed"

    def test_summary_to_dict(self):
        """Serialize summary to dictionary."""
        result = fastjsondiff.compare('{"remove": 1}', '{"add": 2}')
        data = result.summary.to_dict()

        assert "added" in data
        assert "removed" in data
        assert "changed" in data
        assert "total" in data

    def test_metadata_to_dict(self):
        """Serialize metadata to dictionary."""
        result = fastjsondiff.compare('{"a": 1}', '{"a": 2}')
        data = result.metadata.to_dict()

        assert "paths_compared" in data
        assert "max_depth" in data
        assert "duration_ms" in data


class TestFileComparison:
    """Tests for compare_files function."""

    def test_compare_identical_files(self):
        """Compare identical JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_a = Path(tmpdir) / "a.json"
            file_b = Path(tmpdir) / "b.json"

            file_a.write_text('{"name": "test"}')
            file_b.write_text('{"name": "test"}')

            result = fastjsondiff.compare_files(file_a, file_b)
            assert len(result) == 0

    def test_compare_different_files(self):
        """Compare different JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_a = Path(tmpdir) / "a.json"
            file_b = Path(tmpdir) / "b.json"

            file_a.write_text('{"name": "old"}')
            file_b.write_text('{"name": "new"}')

            result = fastjsondiff.compare_files(file_a, file_b)
            assert len(result) == 1
            assert result.summary.changed == 1

    def test_file_not_found_first(self):
        """FileNotFoundError for missing first file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_b = Path(tmpdir) / "b.json"
            file_b.write_text('{}')

            with pytest.raises(FileNotFoundError):
                fastjsondiff.compare_files(
                    Path(tmpdir) / "nonexistent.json",
                    file_b
                )

    def test_file_not_found_second(self):
        """FileNotFoundError for missing second file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_a = Path(tmpdir) / "a.json"
            file_a.write_text('{}')

            with pytest.raises(FileNotFoundError):
                fastjsondiff.compare_files(
                    file_a,
                    Path(tmpdir) / "nonexistent.json"
                )

    def test_compare_files_with_path_strings(self):
        """Accept string paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_a = Path(tmpdir) / "a.json"
            file_b = Path(tmpdir) / "b.json"

            file_a.write_text('{}')
            file_b.write_text('{"a": 1}')

            result = fastjsondiff.compare_files(str(file_a), str(file_b))
            assert len(result) == 1


class TestDifferenceProperties:
    """Tests for Difference object properties."""

    def test_added_difference_properties(self):
        """Added difference has correct properties."""
        result = fastjsondiff.compare('{}', '{"new": "value"}')
        diff = result[0]

        assert diff.type == DiffType.ADDED
        assert "new" in diff.path
        assert diff.old_value is None
        assert diff.new_value is not None

    def test_removed_difference_properties(self):
        """Removed difference has correct properties."""
        result = fastjsondiff.compare('{"old": "value"}', '{}')
        diff = result[0]

        assert diff.type == DiffType.REMOVED
        assert "old" in diff.path
        assert diff.old_value is not None
        assert diff.new_value is None

    def test_changed_difference_properties(self):
        """Changed difference has correct properties."""
        result = fastjsondiff.compare('{"key": "old"}', '{"key": "new"}')
        diff = result[0]

        assert diff.type == DiffType.CHANGED
        assert "key" in diff.path
        assert diff.old_value is not None
        assert diff.new_value is not None

    def test_difference_repr(self):
        """Difference has useful repr."""
        result = fastjsondiff.compare('{"a": 1}', '{"a": 2}')
        diff = result[0]
        repr_str = repr(diff)

        assert "Difference" in repr_str
        assert "changed" in repr_str


class TestSummaryProperties:
    """Tests for DiffSummary properties."""

    def test_summary_total(self):
        """Summary total is sum of all types."""
        json_a = '{"remove": 1, "change": 2}'
        json_b = '{"change": 99, "add": 3}'
        result = fastjsondiff.compare(json_a, json_b)

        assert result.summary.added == 1
        assert result.summary.removed == 1
        assert result.summary.changed == 1
        assert result.summary.total == 3

    def test_empty_summary(self):
        """Empty result has zero summary."""
        result = fastjsondiff.compare('{}', '{}')

        assert result.summary.added == 0
        assert result.summary.removed == 0
        assert result.summary.changed == 0
        assert result.summary.total == 0


class TestMetadataProperties:
    """Tests for DiffMetadata properties."""

    def test_paths_compared(self):
        """Metadata tracks paths compared."""
        result = fastjsondiff.compare('{"a": {"b": 1}}', '{"a": {"b": 2}}')
        assert result.metadata.paths_compared > 0

    def test_max_depth(self):
        """Metadata tracks max depth."""
        result = fastjsondiff.compare('{"a": {"b": {"c": 1}}}', '{"a": {"b": {"c": 2}}}')
        assert result.metadata.max_depth >= 3

    def test_duration(self):
        """Metadata tracks duration."""
        result = fastjsondiff.compare('{"a": 1}', '{"a": 2}')
        assert result.metadata.duration_ms >= 0


class TestResultBooleanBehavior:
    """Tests for result boolean behavior."""

    def test_truthy_when_differences(self):
        """Result is truthy when differences exist."""
        result = fastjsondiff.compare('{"a": 1}', '{"a": 2}')
        assert result  # truthy
        assert bool(result) is True

    def test_falsy_when_no_differences(self):
        """Result is falsy when no differences."""
        result = fastjsondiff.compare('{}', '{}')
        assert not result  # falsy
        assert bool(result) is False

    def test_use_in_if_statement(self):
        """Can use result in if statement."""
        result = fastjsondiff.compare('{"a": 1}', '{"a": 2}')
        if result:
            passed = True
        else:
            passed = False
        assert passed

    def test_use_in_conditional_expression(self):
        """Can use result in conditional expression."""
        result = fastjsondiff.compare('{}', '{}')
        message = "different" if result else "same"
        assert message == "same"
