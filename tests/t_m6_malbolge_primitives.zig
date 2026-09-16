const std = @import("std");
const core = @import("malbolge_free");

test "Malbolge control artifact exercises input and output" {
    const allocator = std.testing.allocator;
    var machine = core.MalbolgeCore.initClassic(allocator);
    defer machine.deinit();
    try machine.load("ubO");
    var result = try machine.run(100, "Z");
    defer result.stdout.deinit(allocator);

    try std.testing.expectEqualStrings("HALTED", result.status);
    try std.testing.expectEqualSlices(u8, "Z", result.stdout.items);
    try std.testing.expect(result.steps > 0);
}
