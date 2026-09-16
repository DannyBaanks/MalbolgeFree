const std = @import("std");
const bf = @import("bf_interpreter.zig");
const translator = @import("bf_to_ir.zig");
const vm = @import("bf_ir_vm.zig");

fn expectEquivalent(source: []const u8, input: []const u8) !void {
    const allocator = std.testing.allocator;
    var direct = try bf.runWithTrace(source, input, .{ .tape_size = 64 }, allocator, true);
    defer direct.deinit();
    var program = try translator.compile(source, allocator);
    defer program.deinit();
    var lowered = try vm.run(&program, input, .{ .tape_size = 64 }, allocator, true);
    defer lowered.deinit();

    try std.testing.expectEqualSlices(u8, direct.output.items, lowered.output.items);
    try std.testing.expectEqual(direct.steps, lowered.steps);
    try std.testing.expectEqual(direct.pointer, lowered.pointer);
    try std.testing.expectEqual(direct.trace.items.len, lowered.trace.items.len);
    for (direct.trace.items, lowered.trace.items) |a, b| {
        try std.testing.expectEqual(a.op, b.op);
        try std.testing.expectEqual(a.pointer, b.pointer);
        try std.testing.expectEqual(a.cell, b.cell);
        try std.testing.expectEqual(a.input_pos, b.input_pos);
        try std.testing.expectEqual(a.output_len, b.output_len);
    }
}

test "IR preserves nested loop execution" {
    try expectEquivalent(">++[<+>-]<.", &.{});
}

test "IR preserves input and output state" {
    try expectEquivalent(",>,<[->+<]>.,", "AZ");
}

test "IR preserves nontermination limits" {
    const allocator = std.testing.allocator;
    var program = try translator.compile("+[+]", allocator);
    defer program.deinit();
    try std.testing.expectError(bf.Error.MaxStepsExceeded, vm.run(&program, &.{}, .{ .max_steps = 32 }, allocator, false));
}
