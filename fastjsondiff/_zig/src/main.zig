const std = @import("std");
const types = @import("types.zig");
const errors = @import("errors.zig");
const memory = @import("memory.zig");
const json_mod = @import("json.zig");
const diff_mod = @import("diff.zig");

pub const FjdOptions = types.FjdOptions;
pub const FjdResult = types.FjdResult;
pub const FjdDiff = types.FjdDiff;
pub const FjdSummary = types.FjdSummary;
pub const FjdMetadata = types.FjdMetadata;
pub const ErrorCode = errors.ErrorCode;

/// Compare two JSON byte strings and return differences.
pub export fn fjd_compare(
    json_a: [*]const u8,
    len_a: usize,
    json_b: [*]const u8,
    len_b: usize,
    options: *const FjdOptions,
    result_out: *?*FjdResult,
) callconv(.C) c_int {
    _ = options; // Will use in future for array_match option

    // Create slices from pointers
    const slice_a = json_a[0..len_a];
    const slice_b = json_b[0..len_b];

    // Validate UTF-8
    if (!std.unicode.utf8ValidateSlice(slice_a)) {
        result_out.* = null;
        return ErrorCode.INVALID_UTF8_A;
    }
    if (!std.unicode.utf8ValidateSlice(slice_b)) {
        result_out.* = null;
        return ErrorCode.INVALID_UTF8_B;
    }

    // Start timing
    const start_time = std.time.nanoTimestamp();

    // Allocate result
    const result_ptr = memory.global_allocator.create(FjdResult) catch {
        result_out.* = null;
        return ErrorCode.OUT_OF_MEMORY;
    };
    result_ptr.* = FjdResult.init(memory.global_allocator);

    // Parse JSON inputs
    const parsed_a = json_mod.parseJson(slice_a, result_ptr.arena.allocator()) catch |err| {
        result_ptr.deinit();
        memory.global_allocator.destroy(result_ptr);
        result_out.* = null;
        return switch (err) {
            error.InvalidJson => ErrorCode.INVALID_JSON_A,
            error.OutOfMemory => ErrorCode.OUT_OF_MEMORY,
        };
    };

    const parsed_b = json_mod.parseJson(slice_b, result_ptr.arena.allocator()) catch |err| {
        result_ptr.deinit();
        memory.global_allocator.destroy(result_ptr);
        result_out.* = null;
        return switch (err) {
            error.InvalidJson => ErrorCode.INVALID_JSON_B,
            error.OutOfMemory => ErrorCode.OUT_OF_MEMORY,
        };
    };

    // Perform diff
    diff_mod.compareValues(result_ptr, parsed_a, parsed_b, "root", 0) catch |err| {
        result_ptr.deinit();
        memory.global_allocator.destroy(result_ptr);
        result_out.* = null;
        return switch (err) {
            error.OutOfMemory => ErrorCode.OUT_OF_MEMORY,
        };
    };

    // Record timing
    const end_time = std.time.nanoTimestamp();
    result_ptr.metadata.duration_ns = @intCast(end_time - start_time);

    result_out.* = result_ptr;
    return ErrorCode.OK;
}

/// Get the number of differences in a result.
pub export fn fjd_result_get_count(result: ?*const FjdResult) callconv(.C) usize {
    if (result) |r| {
        return r.count();
    }
    return 0;
}

/// Get difference at specified index.
pub export fn fjd_result_get_diff(
    result: ?*FjdResult,
    index: usize,
    diff_out: *FjdDiff,
) callconv(.C) c_int {
    if (result == null) {
        return ErrorCode.NULL_POINTER;
    }

    const r = result.?;
    const diff = r.getDiff(index) catch {
        return ErrorCode.INDEX_OUT_OF_BOUNDS;
    };

    diff_out.* = diff.*;
    return ErrorCode.OK;
}

/// Get summary of differences.
pub export fn fjd_result_get_summary(
    result: ?*const FjdResult,
    summary_out: *FjdSummary,
) callconv(.C) void {
    if (result) |r| {
        summary_out.* = r.summary;
    } else {
        summary_out.* = FjdSummary{};
    }
}

/// Get metadata about the comparison.
pub export fn fjd_result_get_metadata(
    result: ?*const FjdResult,
    metadata_out: *FjdMetadata,
) callconv(.C) void {
    if (result) |r| {
        metadata_out.* = r.metadata;
    } else {
        metadata_out.* = FjdMetadata{};
    }
}

/// Free a result and all associated memory.
pub export fn fjd_result_free(result: ?*FjdResult) callconv(.C) void {
    if (result) |r| {
        r.deinit();
        memory.global_allocator.destroy(r);
    }
}

// Re-export error message function
pub const fjd_error_message = errors.fjd_error_message;

// Include tests from other modules
test {
    _ = @import("types.zig");
    _ = @import("errors.zig");
    _ = @import("memory.zig");
    _ = @import("json.zig");
    _ = @import("diff.zig");
}

test "basic comparison via FFI" {
    const json_a = "{}";
    const json_b = "{\"a\":1}";
    var options = FjdOptions{};
    var result: ?*FjdResult = null;

    const code = fjd_compare(
        json_a.ptr,
        json_a.len,
        json_b.ptr,
        json_b.len,
        &options,
        &result,
    );

    try std.testing.expectEqual(ErrorCode.OK, code);
    try std.testing.expect(result != null);
    defer fjd_result_free(result);

    try std.testing.expectEqual(@as(usize, 1), fjd_result_get_count(result));
}
