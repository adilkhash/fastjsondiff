const std = @import("std");
const types = @import("types.zig");
const json_mod = @import("json.zig");

const FjdResult = types.FjdResult;
const Difference = types.Difference;
const DiffType = types.DiffType;
const JsonValue = json_mod.JsonValue;

pub const CompareError = error{OutOfMemory};

/// Compare two JSON values and record differences.
/// Recursively traverses nested structures.
pub fn compareValues(
    result: *FjdResult,
    a: JsonValue,
    b: JsonValue,
    path: []const u8,
    depth: u32,
) CompareError!void {
    // Update metadata
    result.metadata.paths_compared += 1;
    if (depth > result.metadata.max_depth) {
        result.metadata.max_depth = depth;
    }

    // Check if types differ
    if (@intFromEnum(a) != @intFromEnum(b)) {
        // Type mismatch - record as change
        try recordChange(result, path, a, b);
        return;
    }

    // Same type - compare values
    switch (a) {
        .null => {
            // Both null, no difference
        },
        .bool => |bool_a| {
            const bool_b = b.bool;
            if (bool_a != bool_b) {
                try recordChange(result, path, a, b);
            }
        },
        .integer => |int_a| {
            const int_b = b.integer;
            if (int_a != int_b) {
                try recordChange(result, path, a, b);
            }
        },
        .float => |float_a| {
            const float_b = b.float;
            if (float_a != float_b) {
                try recordChange(result, path, a, b);
            }
        },
        .number_string => |num_a| {
            const num_b = b.number_string;
            if (!std.mem.eql(u8, num_a, num_b)) {
                try recordChange(result, path, a, b);
            }
        },
        .string => |str_a| {
            const str_b = b.string;
            if (!std.mem.eql(u8, str_a, str_b)) {
                try recordChange(result, path, a, b);
            }
        },
        .array => |arr_a| {
            const arr_b = b.array;
            try compareArrays(result, arr_a.items, arr_b.items, path, depth);
        },
        .object => |obj_a| {
            const obj_b = b.object;
            try compareObjects(result, obj_a, obj_b, path, depth);
        },
    }
}

/// Compare two arrays element by element (index-based).
fn compareArrays(
    result: *FjdResult,
    arr_a: []const JsonValue,
    arr_b: []const JsonValue,
    path: []const u8,
    depth: u32,
) CompareError!void {
    const allocator = result.arena.allocator();
    const max_len = @max(arr_a.len, arr_b.len);

    for (0..max_len) |i| {
        // Build path with array index: path[i]
        const index_path = std.fmt.allocPrint(allocator, "{s}[{d}]", .{ path, i }) catch {
            return error.OutOfMemory;
        };

        if (i < arr_a.len and i < arr_b.len) {
            // Both have element at this index
            try compareValues(result, arr_a[i], arr_b[i], index_path, depth + 1);
        } else if (i < arr_a.len) {
            // Element removed (only in A)
            try recordRemoved(result, index_path, arr_a[i]);
        } else {
            // Element added (only in B)
            try recordAdded(result, index_path, arr_b[i]);
        }
    }
}

/// Compare two objects key by key.
fn compareObjects(
    result: *FjdResult,
    obj_a: std.json.ObjectMap,
    obj_b: std.json.ObjectMap,
    path: []const u8,
    depth: u32,
) CompareError!void {
    const allocator = result.arena.allocator();

    // Check all keys in A
    var iter_a = obj_a.iterator();
    while (iter_a.next()) |entry| {
        const key = entry.key_ptr.*;
        const key_path = buildKeyPath(allocator, path, key) catch {
            return error.OutOfMemory;
        };

        if (obj_b.get(key)) |value_b| {
            // Key exists in both
            try compareValues(result, entry.value_ptr.*, value_b, key_path, depth + 1);
        } else {
            // Key removed (only in A)
            try recordRemoved(result, key_path, entry.value_ptr.*);
        }
    }

    // Check for keys only in B (added)
    var iter_b = obj_b.iterator();
    while (iter_b.next()) |entry| {
        const key = entry.key_ptr.*;
        if (!obj_a.contains(key)) {
            const key_path = buildKeyPath(allocator, path, key) catch {
                return error.OutOfMemory;
            };
            try recordAdded(result, key_path, entry.value_ptr.*);
        }
    }
}

/// Build a path string for an object key.
fn buildKeyPath(allocator: std.mem.Allocator, path: []const u8, key: []const u8) ![]const u8 {
    // Use dot notation: path.key
    return std.fmt.allocPrint(allocator, "{s}.{s}", .{ path, key });
}

/// Record a changed value.
fn recordChange(result: *FjdResult, path: []const u8, old: JsonValue, new: JsonValue) CompareError!void {
    const allocator = result.arena.allocator();

    const old_str = json_mod.stringify(old, allocator) catch {
        return error.OutOfMemory;
    };
    const new_str = json_mod.stringify(new, allocator) catch {
        return error.OutOfMemory;
    };
    const path_copy = allocator.dupe(u8, path) catch {
        return error.OutOfMemory;
    };

    result.addDifference(.{
        .diff_type = DiffType.CHANGED,
        .path = path_copy,
        .old_value = old_str,
        .new_value = new_str,
    }) catch {
        return error.OutOfMemory;
    };
}

/// Record an added value.
fn recordAdded(result: *FjdResult, path: []const u8, value: JsonValue) CompareError!void {
    const allocator = result.arena.allocator();

    const value_str = json_mod.stringify(value, allocator) catch {
        return error.OutOfMemory;
    };
    const path_copy = allocator.dupe(u8, path) catch {
        return error.OutOfMemory;
    };

    result.addDifference(.{
        .diff_type = DiffType.ADDED,
        .path = path_copy,
        .old_value = null,
        .new_value = value_str,
    }) catch {
        return error.OutOfMemory;
    };
}

/// Record a removed value.
fn recordRemoved(result: *FjdResult, path: []const u8, value: JsonValue) CompareError!void {
    const allocator = result.arena.allocator();

    const value_str = json_mod.stringify(value, allocator) catch {
        return error.OutOfMemory;
    };
    const path_copy = allocator.dupe(u8, path) catch {
        return error.OutOfMemory;
    };

    result.addDifference(.{
        .diff_type = DiffType.REMOVED,
        .path = path_copy,
        .old_value = value_str,
        .new_value = null,
    }) catch {
        return error.OutOfMemory;
    };
}

test "compare identical objects" {
    var arena = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena.deinit();

    const a = try json_mod.parseJson("{\"a\":1}", arena.allocator());
    const b = try json_mod.parseJson("{\"a\":1}", arena.allocator());

    var result = FjdResult.init(std.testing.allocator);
        defer result.deinit();

    try compareValues(&result, a, b, "root", 0);
    try std.testing.expectEqual(@as(usize, 0), result.count());
}

test "detect changed value" {
    var arena = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena.deinit();

    const a = try json_mod.parseJson("{\"a\":1}", arena.allocator());
    const b = try json_mod.parseJson("{\"a\":2}", arena.allocator());

    var result = FjdResult.init(std.testing.allocator);
        defer result.deinit();

    try compareValues(&result, a, b, "root", 0);
    try std.testing.expectEqual(@as(usize, 1), result.count());
    try std.testing.expectEqual(@as(u32, 1), result.summary.changed);
}

test "detect added key" {
    var arena = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena.deinit();

    const a = try json_mod.parseJson("{}", arena.allocator());
    const b = try json_mod.parseJson("{\"a\":1}", arena.allocator());

    var result = FjdResult.init(std.testing.allocator);
        defer result.deinit();

    try compareValues(&result, a, b, "root", 0);
    try std.testing.expectEqual(@as(usize, 1), result.count());
    try std.testing.expectEqual(@as(u32, 1), result.summary.added);
}

test "detect removed key" {
    var arena = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena.deinit();

    const a = try json_mod.parseJson("{\"a\":1}", arena.allocator());
    const b = try json_mod.parseJson("{}", arena.allocator());

    var result = FjdResult.init(std.testing.allocator);
        defer result.deinit();

    try compareValues(&result, a, b, "root", 0);
    try std.testing.expectEqual(@as(usize, 1), result.count());
    try std.testing.expectEqual(@as(u32, 1), result.summary.removed);
}

test "compare arrays" {
    var arena = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena.deinit();

    const a = try json_mod.parseJson("[1,2,3]", arena.allocator());
    const b = try json_mod.parseJson("[1,2,4]", arena.allocator());

    var result = FjdResult.init(std.testing.allocator);
        defer result.deinit();

    try compareValues(&result, a, b, "root", 0);
    try std.testing.expectEqual(@as(usize, 1), result.count());
    try std.testing.expectEqual(@as(u32, 1), result.summary.changed);
}
