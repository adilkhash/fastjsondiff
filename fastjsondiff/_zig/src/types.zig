const std = @import("std");

/// Comparison options passed from Python.
pub const FjdOptions = extern struct {
    /// Array matching strategy: 0=index, 1=id
    array_match: u8 = 0,
    /// Reserved for future options
    reserved: [7]u8 = [_]u8{0} ** 7,
};

/// Summary counts of differences.
pub const FjdSummary = extern struct {
    added: u32 = 0,
    removed: u32 = 0,
    changed: u32 = 0,
    _reserved: u32 = 0,
};

/// Metadata about the comparison operation.
pub const FjdMetadata = extern struct {
    paths_compared: u64 = 0,
    max_depth: u32 = 0,
    _reserved: u32 = 0,
    duration_ns: u64 = 0,
};

/// Single difference in the comparison result.
pub const FjdDiff = extern struct {
    /// Difference type: 0=added, 1=removed, 2=changed
    diff_type: u8,
    /// Padding for alignment
    _pad: [7]u8 = [_]u8{0} ** 7,
    /// JSON path (null-terminated UTF-8)
    path: [*:0]const u8,
    /// Old value as JSON string (null for added)
    old_value: ?[*:0]const u8,
    /// New value as JSON string (null for removed)
    new_value: ?[*:0]const u8,
};

/// Difference types enum values
pub const DiffType = struct {
    pub const ADDED: u8 = 0;
    pub const REMOVED: u8 = 1;
    pub const CHANGED: u8 = 2;
};

/// Internal difference representation with owned strings.
pub const Difference = struct {
    diff_type: u8,
    path: []const u8,
    old_value: ?[]const u8,
    new_value: ?[]const u8,

    pub fn toExtern(self: Difference, allocator: std.mem.Allocator) !FjdDiff {
        // Create null-terminated strings
        const path_z = try allocator.dupeZ(u8, self.path);

        var old_z: ?[*:0]const u8 = null;
        if (self.old_value) |old| {
            old_z = try allocator.dupeZ(u8, old);
        }

        var new_z: ?[*:0]const u8 = null;
        if (self.new_value) |new| {
            new_z = try allocator.dupeZ(u8, new);
        }

        return FjdDiff{
            .diff_type = self.diff_type,
            .path = path_z,
            .old_value = old_z,
            .new_value = new_z,
        };
    }
};

/// Opaque result handle containing comparison results.
pub const FjdResult = struct {
    /// Arena allocator owning all memory for this result
    arena: std.heap.ArenaAllocator,
    /// Array of differences (stored as a slice, managed by arena)
    differences_items: []Difference = &[_]Difference{},
    differences_capacity: usize = 0,
    /// Pre-computed extern diffs for FFI access
    extern_diffs: ?[]FjdDiff = null,
    /// Summary counts
    summary: FjdSummary = .{},
    /// Comparison metadata
    metadata: FjdMetadata = .{},

    pub fn init(backing_allocator: std.mem.Allocator) FjdResult {
        return .{
            .arena = std.heap.ArenaAllocator.init(backing_allocator),
        };
    }

    pub fn deinit(self: *FjdResult) void {
        self.arena.deinit();
    }

    pub fn addDifference(self: *FjdResult, diff: Difference) !void {
        const allocator = self.arena.allocator();
        const len = self.differences_items.len;

        // Grow if needed
        if (len >= self.differences_capacity) {
            const new_cap = if (self.differences_capacity == 0) 8 else self.differences_capacity * 2;
            const new_items = try allocator.alloc(Difference, new_cap);

            // Copy old items
            if (len > 0) {
                @memcpy(new_items[0..len], self.differences_items);
            }

            self.differences_items = new_items[0..len];
            self.differences_capacity = new_cap;
        }

        // Append item (we need to extend the slice within the allocated capacity)
        const items_ptr: [*]Difference = @ptrCast(self.differences_items.ptr);
        items_ptr[len] = diff;
        self.differences_items = items_ptr[0 .. len + 1];

        // Update summary
        switch (diff.diff_type) {
            DiffType.ADDED => self.summary.added += 1,
            DiffType.REMOVED => self.summary.removed += 1,
            DiffType.CHANGED => self.summary.changed += 1,
            else => {},
        }
    }

    /// Prepare extern diffs for FFI access (called once before first access)
    pub fn prepareExternDiffs(self: *FjdResult) !void {
        if (self.extern_diffs != null) return;

        const allocator = self.arena.allocator();
        const extern_list = try allocator.alloc(FjdDiff, self.differences_items.len);

        for (self.differences_items, 0..) |diff, i| {
            extern_list[i] = try diff.toExtern(allocator);
        }

        self.extern_diffs = extern_list;
    }

    pub fn count(self: *const FjdResult) usize {
        return self.differences_items.len;
    }

    pub fn getDiff(self: *FjdResult, index: usize) !*const FjdDiff {
        if (self.extern_diffs == null) {
            try self.prepareExternDiffs();
        }

        if (index >= self.extern_diffs.?.len) {
            return error.IndexOutOfBounds;
        }

        return &self.extern_diffs.?[index];
    }
};

test "FjdOptions default" {
    const opts = FjdOptions{};
    try std.testing.expectEqual(@as(u8, 0), opts.array_match);
}

test "FjdResult basic operations" {
    var result = FjdResult.init(std.testing.allocator);
    defer result.deinit();

    try result.addDifference(.{
        .diff_type = DiffType.ADDED,
        .path = "root.test",
        .old_value = null,
        .new_value = "value",
    });

    try std.testing.expectEqual(@as(usize, 1), result.count());
    try std.testing.expectEqual(@as(u32, 1), result.summary.added);
}
