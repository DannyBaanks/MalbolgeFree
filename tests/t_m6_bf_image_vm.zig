const std = @import("std");
const bf = @import("bf_interpreter.zig");
const translator = @import("bf_to_ir.zig");
const image = @import("bf_ir_image.zig");
const vm = @import("bf_image_vm.zig");

test "BFIR1 VM preserves BF behavior and trace" {
    const allocator = std.testing.allocator;
    const source = ",>,<[->+<]>.,";
    var program = try translator.compile(source, allocator);
    defer program.deinit();
    const bytes = try image.encode(&program, allocator);
    defer allocator.free(bytes);

    var direct = try bf.runWithTrace(source, "AZ", .{ .tape_size = 64 }, allocator, true);
    defer direct.deinit();
    var loaded = try vm.run(bytes, "AZ", .{ .tape_size = 64 }, allocator, true);
    defer loaded.deinit();

    try std.testing.expectEqualSlices(u8, direct.output.items, loaded.output.items);
    try std.testing.expectEqual(direct.steps, loaded.steps);
    try std.testing.expectEqual(direct.trace.items.len, loaded.trace.items.len);
    for (direct.trace.items, loaded.trace.items) |a, b| {
        try std.testing.expectEqual(a.op, b.op);
        try std.testing.expectEqual(a.pointer, b.pointer);
        try std.testing.expectEqual(a.cell, b.cell);
        try std.testing.expectEqual(a.input_pos, b.input_pos);
        try std.testing.expectEqual(a.output_len, b.output_len);
    }
}

test "BFIR1 VM rejects invalid image headers" {
    const allocator = std.testing.allocator;
    try std.testing.expectError(image.Error.InvalidHeader, vm.run("nope", &.{}, .{}, allocator, false));
}
