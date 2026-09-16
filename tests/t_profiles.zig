const std = @import("std");
const core = @import("malbolge_free");

test "free-pure treats extension opcode as runtime NOP and keeps encryption" {
    var vm = core.MalbolgeCore.initFreePure(std.testing.allocator, 10, .fixed);
    defer vm.deinit();
    try vm.load("ubO");

    // Inject an extension-valued runtime cell after strict loading. This is
    // a runtime dispatch control, not a legal Classic source fixture.
    try vm.cellWrite(0, 69);
    var result = try vm.run(100, "");
    defer result.stdout.deinit(std.testing.allocator);

    try std.testing.expectEqualStrings("HALTED", result.status);
    try std.testing.expectEqualSlices(u8, &.{0}, result.stdout.items);
    try std.testing.expectEqual(@as(u32, 0), result.assisted_opcodes);
    try std.testing.expect(result.encrypted_cells > 0);
}

test "free-assisted retains the existing extension dispatch" {
    var vm = core.MalbolgeCore.initFreeAssisted(std.testing.allocator, 10, 59049, .fixed);
    defer vm.deinit();
    try vm.load("ubO");
    try vm.cellWrite(0, 69);
    var result = try vm.run(100, "");
    defer result.stdout.deinit(std.testing.allocator);

    try std.testing.expectEqualStrings("HALTED", result.status);
    try std.testing.expectEqualSlices(u8, &.{69}, result.stdout.items);
    try std.testing.expectEqual(@as(u32, 1), result.assisted_opcodes);
}
