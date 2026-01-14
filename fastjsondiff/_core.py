"""
Low-level FFI wrapper for the Zig core library.

This module handles loading the compiled Zig shared library and
provides Python bindings to the C ABI functions exported by the core.
"""

import ctypes
import os
import sys
from pathlib import Path
from typing import Optional

# FFI type definitions matching Zig structs
class FjdOptions(ctypes.Structure):
    """Comparison options passed to Zig core."""
    _fields_ = [
        ("array_match", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 7),
    ]


class FjdSummary(ctypes.Structure):
    """Summary counts returned from Zig core."""
    _fields_ = [
        ("added", ctypes.c_uint32),
        ("removed", ctypes.c_uint32),
        ("changed", ctypes.c_uint32),
        ("_reserved", ctypes.c_uint32),
    ]


class FjdMetadata(ctypes.Structure):
    """Comparison metadata returned from Zig core."""
    _fields_ = [
        ("paths_compared", ctypes.c_uint64),
        ("max_depth", ctypes.c_uint32),
        ("_reserved", ctypes.c_uint32),
        ("duration_ns", ctypes.c_uint64),
    ]


class FjdDiff(ctypes.Structure):
    """Single difference returned from Zig core."""
    _fields_ = [
        ("diff_type", ctypes.c_uint8),
        ("_pad", ctypes.c_uint8 * 7),
        ("path", ctypes.c_char_p),
        ("old_value", ctypes.c_char_p),
        ("new_value", ctypes.c_char_p),
    ]


# Opaque pointer to result handle
class FjdResult(ctypes.Structure):
    """Opaque handle to comparison result."""
    pass


FjdResultPtr = ctypes.POINTER(FjdResult)


# Error codes
FJD_OK = 0
FJD_ERR_INVALID_UTF8_A = 1
FJD_ERR_INVALID_UTF8_B = 2
FJD_ERR_INVALID_JSON_A = 3
FJD_ERR_INVALID_JSON_B = 4
FJD_ERR_OUT_OF_MEMORY = 5
FJD_ERR_INDEX_OUT_OF_BOUNDS = 6
FJD_ERR_NULL_POINTER = 7


def _find_library() -> Optional[Path]:
    """Find the compiled Zig shared library."""
    # Look for library in package directory
    pkg_dir = Path(__file__).parent

    if sys.platform == "win32":
        lib_name = "fastjsondiff_core.dll"
    elif sys.platform == "darwin":
        lib_name = "libfastjsondiff_core.dylib"
    else:
        lib_name = "libfastjsondiff_core.so"

    lib_path = pkg_dir / lib_name
    if lib_path.exists():
        return lib_path

    # Also check zig-out directory during development
    zig_out = pkg_dir / "_zig" / "zig-out" / "lib" / lib_name
    if zig_out.exists():
        return zig_out

    # On Windows, DLLs are placed in bin/ directory
    zig_out_bin = pkg_dir / "_zig" / "zig-out" / "bin" / lib_name
    if zig_out_bin.exists():
        return zig_out_bin

    return None


def _load_library():
    """Load the Zig shared library and set up function signatures."""
    lib_path = _find_library()
    if lib_path is None:
        raise ImportError(
            "Could not find fastjsondiff_core library. "
            "Please run 'zig build' in fastjsondiff/_zig/ first."
        )

    lib = ctypes.CDLL(str(lib_path))

    # fjd_compare
    lib.fjd_compare.argtypes = [
        ctypes.c_char_p,  # json_a
        ctypes.c_size_t,  # len_a
        ctypes.c_char_p,  # json_b
        ctypes.c_size_t,  # len_b
        ctypes.POINTER(FjdOptions),  # options
        ctypes.POINTER(FjdResultPtr),  # result_out
    ]
    lib.fjd_compare.restype = ctypes.c_int

    # fjd_result_get_count
    lib.fjd_result_get_count.argtypes = [FjdResultPtr]
    lib.fjd_result_get_count.restype = ctypes.c_size_t

    # fjd_result_get_diff
    lib.fjd_result_get_diff.argtypes = [
        FjdResultPtr,
        ctypes.c_size_t,
        ctypes.POINTER(FjdDiff),
    ]
    lib.fjd_result_get_diff.restype = ctypes.c_int

    # fjd_result_get_summary
    lib.fjd_result_get_summary.argtypes = [
        FjdResultPtr,
        ctypes.POINTER(FjdSummary),
    ]
    lib.fjd_result_get_summary.restype = None

    # fjd_result_get_metadata
    lib.fjd_result_get_metadata.argtypes = [
        FjdResultPtr,
        ctypes.POINTER(FjdMetadata),
    ]
    lib.fjd_result_get_metadata.restype = None

    # fjd_result_free
    lib.fjd_result_free.argtypes = [FjdResultPtr]
    lib.fjd_result_free.restype = None

    # fjd_error_message
    lib.fjd_error_message.argtypes = [ctypes.c_int]
    lib.fjd_error_message.restype = ctypes.c_char_p

    return lib


# Lazy-loaded library instance
_lib = None


def get_library():
    """Get the loaded library instance."""
    global _lib
    if _lib is None:
        _lib = _load_library()
    return _lib
