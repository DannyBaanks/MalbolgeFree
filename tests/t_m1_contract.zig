//! M1 contract tests: numeric boundary and the canonical EOF value.
const std = @import("std");
const core = @import("malbolge_free");

test "u128 width boundary is explicit" {
    try std.testing.expect(core.pow3(80) < std.math.maxInt(u128));
    try std.testing.expectEqual(std.math.maxInt(u128), core.pow3(81));
}

test "EOF is the canonical Classic byte 0xa8" {
    const alloc = std.testing.allocator;
    var vm = core.MalbolgeCore.initClassic(alloc);
    defer vm.deinit();
    try vm.load("ubO");
    var result = try vm.run(100, &.{});
    defer result.stdout.deinit(alloc);
    // `ubO` is in,out,halt. Canonical Classic assigns a = 3^10-1 = 59048 at EOF,
    // so out emits 59048 mod 256 = 0xa8. Measured 2026-10-17 against
    // reference_interpreter_classic and MALBOLGE/malbolge.py. The old sentinel
    // emitted 0xff here.
    try std.testing.expectEqual(@as(u128, 59048), core.pow3(10) - 1);
    try std.testing.expectEqualStrings("\xa8", result.stdout.items);
}
