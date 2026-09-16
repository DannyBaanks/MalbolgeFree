const std = @import("std");
const bf = @import("bf_interpreter.zig");
const translator = @import("bf_to_ir.zig");
const image = @import("bf_ir_image.zig");
const vm = @import("bf_image_vm.zig");

const HELLO_WORLD =
    "++++++++++[>+++++++>++++++++++>+++>+<<<<-]" ++
    ">++.>+.+++++++..+++.>++.<<+++++++++++++++.>.+++." ++
    "------.--------.>+.>.";
const EXPECTED = "Hello World!\n";

fn sha256Hex(bytes: []const u8) [64]u8 {
    var digest: [32]u8 = undefined;
    std.crypto.hash.sha2.Sha256.hash(bytes, &digest, .{});
    return std.fmt.bytesToHex(digest, .lower);
}

test "own BF compiler is an executable Hello World oracle" {
    const allocator = std.testing.allocator;
    var direct = try bf.runWithTrace(HELLO_WORLD, &.{}, .{ .tape_size = 30_000, .max_steps = 10_000_000 }, allocator, true);
    defer direct.deinit();
    var program = try translator.compile(HELLO_WORLD, allocator);
    defer program.deinit();
    const bytes = try image.encode(&program, allocator);
    defer allocator.free(bytes);
    var compiled = try vm.run(bytes, &.{}, .{ .tape_size = 30_000, .max_steps = 10_000_000 }, allocator, true);
    defer compiled.deinit();

    try std.testing.expectEqualSlices(u8, EXPECTED, direct.output.items);
    try std.testing.expectEqualSlices(u8, direct.output.items, compiled.output.items);
    try std.testing.expectEqual(direct.steps, compiled.steps);
    try std.testing.expectEqual(direct.trace.items.len, compiled.trace.items.len);
    for (direct.trace.items, compiled.trace.items) |a, b| {
        try std.testing.expectEqual(a.op, b.op);
        try std.testing.expectEqual(a.pointer, b.pointer);
        try std.testing.expectEqual(a.cell, b.cell);
        try std.testing.expectEqual(a.input_pos, b.input_pos);
        try std.testing.expectEqual(a.output_len, b.output_len);
    }

    const output_hash = sha256Hex(direct.output.items);
    std.debug.print("BF source ops={d} image_bytes={d} steps={d} output_sha256={s}\n", .{
        program.code.items.len, bytes.len, direct.steps, output_hash,
    });
}
