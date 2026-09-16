//! M1 contract tests: numeric boundary and EOF normalization.
const std = @import("std");
const core = @import("malbolge_free");

test "u128 width boundary is explicit" {
    try std.testing.expect(core.pow3(80) < std.math.maxInt(u128));
    try std.testing.expectEqual(std.math.maxInt(u128), core.pow3(81));
}

test "EOF is the Classic byte 255" {
    const alloc = std.testing.allocator;
    var vm = core.MalbolgeCore.initClassic(alloc);
    defer vm.deinit();
    try vm.load("ubO");
    var result = try vm.run(100, &.{});
    defer result.stdout.deinit(alloc);
    try std.testing.expectEqualStrings("\xff", result.stdout.items);
}
