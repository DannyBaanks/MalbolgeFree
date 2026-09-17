//! M5 on the real VM loop: the witness run through `vm.run` (not a
//! hand-stepped loop) widens exactly twice, 10 -> 11 -> 12.
const std = @import("std");
const core = @import("malbolge_free");

test "full VM run crosses 10 -> 11 -> 12" {
    const alloc = std.testing.allocator;
    const src = @embedFile("frontier_witness.txt");
    var vm = core.MalbolgeCore.initFreePure(alloc, 10, .epochal);
    defer vm.deinit();
    try vm.load(src);
    var res = try vm.run(190_000, "");
    defer res.stdout.deinit(alloc);

    try std.testing.expectEqualStrings("MAX_STEPS", res.status);
    try std.testing.expectEqual(@as(u64, 190_000), res.steps);
    try std.testing.expectEqual(@as(u128, 190_000), res.final_c);
    try std.testing.expectEqual(@as(u8, 12), vm.padwidth);
    try std.testing.expectEqual(@as(u32, 2), vm.stats.growth_events);
}

test "full VM run stops at 11 before the second frontier" {
    const alloc = std.testing.allocator;
    const src = @embedFile("frontier_witness.txt");
    var vm = core.MalbolgeCore.initFreePure(alloc, 10, .epochal);
    defer vm.deinit();
    try vm.load(src);
    // Step 177148 is the one where c = 3^11; stop just before it.
    var res = try vm.run(177_147, "");
    defer res.stdout.deinit(alloc);

    try std.testing.expectEqual(@as(u8, 11), vm.padwidth);
    try std.testing.expectEqual(@as(u32, 1), vm.stats.growth_events);
}
