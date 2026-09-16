const std = @import("std");
const core = @import("malbolge_free");

test "unshackled k19 profile is explicit and deterministic" {
    var vm = core.MalbolgeCore.initUnshackledK19(std.testing.allocator);
    defer vm.deinit();
    try vm.load("ubO");
    var result = try vm.run(100, "");
    defer result.stdout.deinit(std.testing.allocator);
    try std.testing.expectEqualStrings("HALTED", result.status);
    try std.testing.expectEqual(@as(usize, 1), result.stdout.items.len);
    try std.testing.expectEqual(@as(u128, 3), core.pow3(1));
    try std.testing.expectEqual(@as(u128, 1_162_261_467), core.pow3(19));
}
