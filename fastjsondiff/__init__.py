"""
fastjsondiff - High-performance JSON comparison library.

A Python library for comparing JSON payloads with a Zig-powered core
for maximum speed. Provides O(n) time complexity where n = total nodes.

Example:
    >>> import fastjsondiff
    >>> result = fastjsondiff.compare('{"a": 1}', '{"a": 2}')
    >>> len(result)
    1
    >>> result.differences[0].type
    <DiffType.CHANGED: 'changed'>
"""

__version__ = "0.1.0"
__all__ = [
    "compare",
    "compare_files",
    "DiffResult",
    "Difference",
    "DiffType",
    "DiffSummary",
    "DiffMetadata",
    "InvalidJsonError",
]

from fastjsondiff.models import (
    DiffResult,
    Difference,
    DiffType,
    DiffSummary,
    DiffMetadata,
    InvalidJsonError,
)
from fastjsondiff._core import (
    get_library,
    FjdOptions,
    FjdSummary,
    FjdMetadata,
    FjdDiff,
    FjdResultPtr,
    FJD_OK,
    FJD_ERR_INVALID_UTF8_A,
    FJD_ERR_INVALID_UTF8_B,
    FJD_ERR_INVALID_JSON_A,
    FJD_ERR_INVALID_JSON_B,
    FJD_ERR_OUT_OF_MEMORY,
)
import ctypes


def compare(a, b, *, array_match="index"):
    """
    Compare two JSON payloads and return their differences.

    Args:
        a: First JSON input (string or bytes)
        b: Second JSON input (string or bytes)
        array_match: Array comparison strategy
            - "index": Compare by position (default, O(n))

    Returns:
        DiffResult containing all differences found

    Raises:
        InvalidJsonError: If either input is not valid JSON
        UnicodeDecodeError: If input is not valid UTF-8
        MemoryError: If memory allocation fails

    Time Complexity: O(n) where n = total nodes in both inputs
    Space Complexity: O(n) for result storage
    """
    # Convert inputs to bytes
    if isinstance(a, str):
        bytes_a = a.encode("utf-8")
    elif isinstance(a, bytes):
        bytes_a = a
    else:
        raise TypeError(f"Expected str or bytes for first argument, got {type(a).__name__}")

    if isinstance(b, str):
        bytes_b = b.encode("utf-8")
    elif isinstance(b, bytes):
        bytes_b = b
    else:
        raise TypeError(f"Expected str or bytes for second argument, got {type(b).__name__}")

    # Set up options
    options = FjdOptions()
    if array_match == "index":
        options.array_match = 0
    elif array_match == "id":
        options.array_match = 1
    else:
        raise ValueError(f"Invalid array_match value: {array_match!r}")

    # Call Zig core
    lib = get_library()
    result_ptr = FjdResultPtr()

    error_code = lib.fjd_compare(
        bytes_a,
        len(bytes_a),
        bytes_b,
        len(bytes_b),
        ctypes.byref(options),
        ctypes.byref(result_ptr),
    )

    # Handle errors
    if error_code != FJD_OK:
        if error_code == FJD_ERR_INVALID_UTF8_A:
            raise UnicodeDecodeError("utf-8", bytes_a, 0, len(bytes_a), "invalid UTF-8 in first input")
        elif error_code == FJD_ERR_INVALID_UTF8_B:
            raise UnicodeDecodeError("utf-8", bytes_b, 0, len(bytes_b), "invalid UTF-8 in second input")
        elif error_code == FJD_ERR_INVALID_JSON_A:
            raise InvalidJsonError("Invalid JSON in first input")
        elif error_code == FJD_ERR_INVALID_JSON_B:
            raise InvalidJsonError("Invalid JSON in second input")
        elif error_code == FJD_ERR_OUT_OF_MEMORY:
            raise MemoryError("Out of memory during comparison")
        else:
            raise RuntimeError(f"Zig core error: {error_code}")

    try:
        # Get summary
        summary_c = FjdSummary()
        lib.fjd_result_get_summary(result_ptr, ctypes.byref(summary_c))
        summary = DiffSummary(
            added=summary_c.added,
            removed=summary_c.removed,
            changed=summary_c.changed,
        )

        # Get metadata
        metadata_c = FjdMetadata()
        lib.fjd_result_get_metadata(result_ptr, ctypes.byref(metadata_c))
        metadata = DiffMetadata(
            paths_compared=metadata_c.paths_compared,
            max_depth=metadata_c.max_depth,
            duration_ms=metadata_c.duration_ns / 1_000_000,
        )

        # Get differences
        count = lib.fjd_result_get_count(result_ptr)
        differences = []

        for i in range(count):
            diff_c = FjdDiff()
            err = lib.fjd_result_get_diff(result_ptr, i, ctypes.byref(diff_c))
            if err != FJD_OK:
                continue

            # Map diff_type to DiffType enum
            if diff_c.diff_type == 0:
                diff_type = DiffType.ADDED
            elif diff_c.diff_type == 1:
                diff_type = DiffType.REMOVED
            else:
                diff_type = DiffType.CHANGED

            # Decode strings
            path = diff_c.path.decode("utf-8") if diff_c.path else ""
            old_value = diff_c.old_value.decode("utf-8") if diff_c.old_value else None
            new_value = diff_c.new_value.decode("utf-8") if diff_c.new_value else None

            differences.append(Difference(
                type=diff_type,
                path=path,
                old_value=old_value,
                new_value=new_value,
            ))

        return DiffResult(
            differences=differences,
            summary=summary,
            metadata=metadata,
        )

    finally:
        # Always free the result
        lib.fjd_result_free(result_ptr)


def compare_files(path_a, path_b, *, array_match="index", encoding="utf-8"):
    """
    Compare two JSON files.

    Args:
        path_a: Path to first JSON file
        path_b: Path to second JSON file
        array_match: Array comparison strategy (see compare())
        encoding: File encoding (default: utf-8)

    Returns:
        DiffResult containing all differences found

    Raises:
        FileNotFoundError: If either file doesn't exist
        InvalidJsonError: If either file contains invalid JSON
        UnicodeDecodeError: If file content doesn't match encoding
    """
    from pathlib import Path

    path_a = Path(path_a)
    path_b = Path(path_b)

    if not path_a.exists():
        raise FileNotFoundError(f"File not found: {path_a}")
    if not path_b.exists():
        raise FileNotFoundError(f"File not found: {path_b}")

    content_a = path_a.read_text(encoding=encoding)
    content_b = path_b.read_text(encoding=encoding)

    return compare(content_a, content_b, array_match=array_match)
