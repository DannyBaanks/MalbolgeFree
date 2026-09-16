//! Negative contract tests: invalid source and undersized programs.
const std = @import("std");
const core = @import("malbolge_free");

test "loader rejects non-printable source" {
    var vm = core.MalbolgeCore.initFreeAssisted(std.testing.allocator, 10, null, .fixed);
    defer vm.deinit();
    try std.testing.expectError(error.InvalidSource, vm.load("a\x01"));
}

test "loader rejects programs shorter than two cells" {
    var vm = core.MalbolgeCore.initFreeAssisted(std.testing.allocator, 10, null, .fixed);
    defer vm.deinit();
    try std.testing.expectError(error.ProgramTooShort, vm.load("a"));
}

test "loader rejects printable source with invalid positional opcode" {
    var vm = core.MalbolgeCore.initClassic(std.testing.allocator);
    defer vm.deinit();
    // At source position 0, '!' decodes to 33, which is not one of the
    // eight legal Classic source opcodes.
    try std.testing.expectError(error.InvalidSourceOpcode, vm.load("!!"));
}
