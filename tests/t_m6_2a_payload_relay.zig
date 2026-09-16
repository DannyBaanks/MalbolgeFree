const std = @import("std");
const core = @import("malbolge_free");

test "M6.2a Malbolge relays one payload byte unchanged" {
    const allocator = std.testing.allocator;
    const payload = "A";
    var machine = core.MalbolgeCore.initClassic(allocator);
    defer machine.deinit();
    try machine.load("ubO");
    var result = try machine.run(100, payload);
    defer result.stdout.deinit(allocator);

    try std.testing.expectEqualStrings("HALTED", result.status);
    try std.testing.expectEqualSlices(u8, payload, result.stdout.items);
}
