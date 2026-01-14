const std = @import("std");
const types = @import("types.zig");

/// Result serialization and path building utilities.

/// Path builder for JSON paths.
/// Supports both dot notation (obj.key) and bracket notation (arr[0]).
pub const PathBuilder = struct {
    allocator: std.mem.Allocator,
    buffer: std.ArrayList(u8),

    pub fn init(allocator: std.mem.Allocator) PathBuilder {
        return .{
            .allocator = allocator,
            .buffer = std.ArrayList(u8).init(allocator),
        };
    }

    pub fn deinit(self: *PathBuilder) void {
        self.buffer.deinit();
    }

    /// Start a new path from root.
    pub fn root(self: *PathBuilder) !void {
        self.buffer.clearRetainingCapacity();
        try self.buffer.appendSlice("root");
    }

    /// Append an object key using dot notation.
    pub fn appendKey(self: *PathBuilder, key: []const u8) !void {
        try self.buffer.append('.');
        try self.buffer.appendSlice(key);
    }

    /// Append an array index using bracket notation.
    pub fn appendIndex(self: *PathBuilder, index: usize) !void {
        try self.buffer.append('[');
        try std.fmt.formatInt(index, 10, .lower, .{}, self.buffer.writer());
        try self.buffer.append(']');
    }

    /// Get the current path as a string.
    pub fn getPath(self: *PathBuilder) []const u8 {
        return self.buffer.items;
    }

    /// Get a copy of the current path.
    pub fn copyPath(self: *PathBuilder) ![]const u8 {
        return self.allocator.dupe(u8, self.buffer.items);
    }
};

/// Build a full path string from components.
pub fn buildPath(allocator: std.mem.Allocator, base: []const u8, key: []const u8) ![]const u8 {
    return std.fmt.allocPrint(allocator, "{s}.{s}", .{ base, key });
}

/// Build a path with array index.
pub fn buildArrayPath(allocator: std.mem.Allocator, base: []const u8, index: usize) ![]const u8 {
    return std.fmt.allocPrint(allocator, "{s}[{d}]", .{ base, index });
}

/// Parse a path string into components.
pub const PathComponent = union(enum) {
    key: []const u8,
    index: usize,
};

pub fn parsePath(allocator: std.mem.Allocator, path: []const u8) !std.ArrayList(PathComponent) {
    var components = std.ArrayList(PathComponent).init(allocator);
    errdefer components.deinit();

    var i: usize = 0;
    var start: usize = 0;

    while (i < path.len) {
        const c = path[i];

        if (c == '.') {
            if (i > start) {
                try components.append(.{ .key = path[start..i] });
            }
            start = i + 1;
        } else if (c == '[') {
            if (i > start) {
                try components.append(.{ .key = path[start..i] });
            }
            // Find closing bracket
            const bracket_start = i + 1;
            while (i < path.len and path[i] != ']') : (i += 1) {}
            if (i < path.len) {
                const index_str = path[bracket_start..i];
                const index = std.fmt.parseInt(usize, index_str, 10) catch 0;
                try components.append(.{ .index = index });
            }
            start = i + 1;
        }

        i += 1;
    }

    // Handle remaining part
    if (start < path.len) {
        try components.append(.{ .key = path[start..] });
    }

    return components;
}

test "PathBuilder basic usage" {
    var builder = PathBuilder.init(std.testing.allocator);
    defer builder.deinit();

    try builder.root();
    try builder.appendKey("user");
    try builder.appendKey("name");

    try std.testing.expectEqualStrings("root.user.name", builder.getPath());
}

test "PathBuilder with array" {
    var builder = PathBuilder.init(std.testing.allocator);
    defer builder.deinit();

    try builder.root();
    try builder.appendKey("items");
    try builder.appendIndex(0);
    try builder.appendKey("id");

    try std.testing.expectEqualStrings("root.items[0].id", builder.getPath());
}

test "buildPath" {
    const path = try buildPath(std.testing.allocator, "root", "key");
    defer std.testing.allocator.free(path);
    try std.testing.expectEqualStrings("root.key", path);
}

test "buildArrayPath" {
    const path = try buildArrayPath(std.testing.allocator, "root.items", 5);
    defer std.testing.allocator.free(path);
    try std.testing.expectEqualStrings("root.items[5]", path);
}
