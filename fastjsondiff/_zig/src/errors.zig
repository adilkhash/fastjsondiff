const std = @import("std");

/// Error codes returned by FFI functions.
pub const ErrorCode = struct {
    pub const OK: c_int = 0;
    pub const INVALID_UTF8_A: c_int = 1;
    pub const INVALID_UTF8_B: c_int = 2;
    pub const INVALID_JSON_A: c_int = 3;
    pub const INVALID_JSON_B: c_int = 4;
    pub const OUT_OF_MEMORY: c_int = 5;
    pub const INDEX_OUT_OF_BOUNDS: c_int = 6;
    pub const NULL_POINTER: c_int = 7;
};

/// Error messages for each error code.
const error_messages = [_][:0]const u8{
    "Success", // OK
    "Invalid UTF-8 in first input", // INVALID_UTF8_A
    "Invalid UTF-8 in second input", // INVALID_UTF8_B
    "Invalid JSON syntax in first input", // INVALID_JSON_A
    "Invalid JSON syntax in second input", // INVALID_JSON_B
    "Out of memory", // OUT_OF_MEMORY
    "Index out of bounds", // INDEX_OUT_OF_BOUNDS
    "Null pointer argument", // NULL_POINTER
};

/// Get human-readable error message for an error code.
pub fn getErrorMessage(code: c_int) [*:0]const u8 {
    const index: usize = @intCast(@max(0, @min(code, @as(c_int, @intCast(error_messages.len - 1)))));
    return error_messages[index].ptr;
}

/// FFI export: Get error message for error code.
pub export fn fjd_error_message(code: c_int) callconv(.c) [*:0]const u8 {
    return getErrorMessage(code);
}

/// Internal error type for Zig code.
pub const DiffError = error{
    InvalidUtf8A,
    InvalidUtf8B,
    InvalidJsonA,
    InvalidJsonB,
    OutOfMemory,
    IndexOutOfBounds,
    NullPointer,
};

/// Convert internal error to FFI error code.
pub fn toErrorCode(err: DiffError) c_int {
    return switch (err) {
        error.InvalidUtf8A => ErrorCode.INVALID_UTF8_A,
        error.InvalidUtf8B => ErrorCode.INVALID_UTF8_B,
        error.InvalidJsonA => ErrorCode.INVALID_JSON_A,
        error.InvalidJsonB => ErrorCode.INVALID_JSON_B,
        error.OutOfMemory => ErrorCode.OUT_OF_MEMORY,
        error.IndexOutOfBounds => ErrorCode.INDEX_OUT_OF_BOUNDS,
        error.NullPointer => ErrorCode.NULL_POINTER,
    };
}

test "error messages" {
    const msg = fjd_error_message(ErrorCode.OK);
    const slice = std.mem.sliceTo(msg, 0);
    try std.testing.expectEqualStrings("Success", slice);
}

test "invalid error code returns valid message" {
    const msg = fjd_error_message(999);
    const slice = std.mem.sliceTo(msg, 0);
    // Should return the last valid message or clamp to valid range
    try std.testing.expect(slice.len > 0);
}
