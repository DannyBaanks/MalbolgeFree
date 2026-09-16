const std = @import("std");
const translator = @import("bf_to_ir.zig");
const image = @import("bf_ir_image.zig");

test "IR image is versioned, deterministic, and carries jump metadata" {
    const allocator = std.testing.allocator;
    var program = try translator.compile("+[.-]", allocator);
    defer program.deinit();
    const first = try image.encode(&program, allocator);
    defer allocator.free(first);
    const second = try image.encode(&program, allocator);
    defer allocator.free(second);

    try std.testing.expectEqualSlices(u8, "BFIR1", first[0..5]);
    try std.testing.expectEqualSlices(u8, first, second);
    try std.testing.expectEqual(@as(u8, 7), first[21]);
    try std.testing.expectEqual(@as(u8, 1), first[22]);
    try std.testing.expectEqual(@as(u32, 4), std.mem.readInt(u32, first[25..29], .little));
}

test "IR image refuses malformed IR" {
    const allocator = std.testing.allocator;
    var program = try translator.compile("[]", allocator);
    defer program.deinit();
    program.code.items[0].target = null;
    try std.testing.expectError(translator.Error.MissingJumpTarget, image.encode(&program, allocator));
}
