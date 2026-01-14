const std = @import("std");

/// Memory management utilities for the JSON diff library.
/// Uses arena allocation for efficient bulk allocation and deallocation.

/// Global allocator for result objects.
/// Uses the C allocator for compatibility with Python FFI.
pub const global_allocator = std.heap.c_allocator;

/// Create a new arena allocator backed by the global allocator.
pub fn createArena() std.heap.ArenaAllocator {
    return std.heap.ArenaAllocator.init(global_allocator);
}

/// Duplicate a slice into arena-owned memory.
pub fn dupeSlice(arena: *std.heap.ArenaAllocator, slice: []const u8) ![]const u8 {
    return arena.allocator().dupe(u8, slice);
}

/// Duplicate a slice into arena-owned memory with null terminator.
pub fn dupeSliceZ(arena: *std.heap.ArenaAllocator, slice: []const u8) ![:0]const u8 {
    return arena.allocator().dupeZ(u8, slice);
}

/// Statistics about memory usage (for debugging/metrics).
pub const MemoryStats = struct {
    total_allocated: usize = 0,
    peak_allocated: usize = 0,
    allocation_count: usize = 0,
};

test "arena allocation" {
    var arena = createArena();
    defer arena.deinit();

    const data = try dupeSlice(&arena, "test string");
    try std.testing.expectEqualStrings("test string", data);
}

test "arena null-terminated duplication" {
    var arena = createArena();
    defer arena.deinit();

    const data_z = try dupeSliceZ(&arena, "test");
    try std.testing.expectEqualStrings("test", data_z);
}
