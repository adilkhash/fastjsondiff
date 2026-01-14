const std = @import("std");

/// JSON parsing utilities using std.json.
/// Provides a thin wrapper for consistent error handling.

pub const JsonValue = std.json.Value;
pub const ParseError = error{ InvalidJson, OutOfMemory };

/// Parse a JSON string into a Value tree.
/// Uses arena allocator for all allocations.
pub fn parseJson(input: []const u8, allocator: std.mem.Allocator) ParseError!JsonValue {
    // Handle empty input
    if (input.len == 0) {
        return error.InvalidJson;
    }

    const parsed = std.json.parseFromSlice(
        JsonValue,
        allocator,
        input,
        .{},
    ) catch |err| {
        return switch (err) {
            error.OutOfMemory => error.OutOfMemory,
            else => error.InvalidJson,
        };
    };

    return parsed.value;
}

/// Check if a byte sequence is valid UTF-8.
pub fn isValidUtf8(bytes: []const u8) bool {
    return std.unicode.utf8ValidateSlice(bytes);
}

/// Serialize a JSON value back to a string.
/// Useful for storing old/new values in diff results.
pub fn stringify(json_value: JsonValue, allocator: std.mem.Allocator) ![]const u8 {
    var aw: std.Io.Writer.Allocating = .init(allocator);
    errdefer aw.deinit();
    try std.json.Stringify.value(json_value, .{}, &aw.writer);
    return aw.toOwnedSlice();
}

/// Get a string representation of a JSON value type.
pub fn typeName(value: JsonValue) []const u8 {
    return switch (value) {
        .null => "null",
        .bool => "boolean",
        .integer => "integer",
        .float => "float",
        .string => "string",
        .array => "array",
        .object => "object",
        .number_string => "number",
    };
}

test "parse empty object" {
    var arena = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena.deinit();

    const result = try parseJson("{}", arena.allocator());
    try std.testing.expect(result == .object);
}

test "parse simple object" {
    var arena = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena.deinit();

    const result = try parseJson("{\"a\":1}", arena.allocator());
    try std.testing.expect(result == .object);
    try std.testing.expect(result.object.contains("a"));
}

test "parse array" {
    var arena = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena.deinit();

    const result = try parseJson("[1,2,3]", arena.allocator());
    try std.testing.expect(result == .array);
    try std.testing.expectEqual(@as(usize, 3), result.array.items.len);
}

test "parse invalid json" {
    var arena = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena.deinit();

    const result = parseJson("{invalid}", arena.allocator());
    try std.testing.expectError(error.InvalidJson, result);
}

test "parse empty input" {
    var arena = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena.deinit();

    const result = parseJson("", arena.allocator());
    try std.testing.expectError(error.InvalidJson, result);
}
