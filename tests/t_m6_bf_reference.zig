const std = @import("std");
const bf = @import("bf_interpreter.zig");

test "reference preserves loops, state, and trace" {
    const allocator = std.testing.allocator;
    var result = try bf.runWithTrace(">++[<+>-]<.", &.{}, .{ .tape_size = 8 }, allocator, true);
    defer result.deinit();

    try std.testing.expectEqualSlices(u8, &.{ 2 }, result.output.items);
    try std.testing.expectEqual(@as(usize, 0), result.pointer);
    try std.testing.expectEqual(@as(u64, 16), result.steps);
    try std.testing.expectEqual(@as(usize, 16), result.trace.items.len);
    try std.testing.expectEqual(@as(u8, '.'), result.trace.items[15].op);
}

test "reference defines EOF and pointer errors" {
    const allocator = std.testing.allocator;
    var eof = try bf.runWithTrace(",.", &.{}, .{}, allocator, false);
    defer eof.deinit();
    try std.testing.expectEqualSlices(u8, &.{0}, eof.output.items);
    try std.testing.expectError(bf.Error.PointerOutOfBounds, bf.runWithTrace("<", &.{}, .{}, allocator, false));
}
