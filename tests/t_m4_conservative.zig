//! M4: epochal is a conservative extension of fixed execution.
const std = @import("std");
const core = @import("malbolge_free");

const PROG =
    \\(=<`#9]~6ZY327Uv4-QsqpMn&+Ij"'E%e{Ab~w=_:]Kw%o44Uqp0/Q?xNvL:`H%c#DD2^WV>gY;dts76qKJImZkj
;

test "epochal degenerates to fixed before a frontier" {
    const alloc = std.testing.allocator;
    var fixed = core.MalbolgeCore.initFreePure(alloc, 10, .fixed);
    defer fixed.deinit();
    try fixed.load(PROG);
    var epochal = core.MalbolgeCore.initFreePure(alloc, 10, .epochal);
    defer epochal.deinit();
    try epochal.load(PROG);

    var fixed_result = try fixed.run(5_000, "");
    defer fixed_result.stdout.deinit(alloc);
    var epochal_result = try epochal.run(5_000, "");
    defer epochal_result.stdout.deinit(alloc);

    try std.testing.expectEqualStrings(fixed_result.stdout.items, epochal_result.stdout.items);
    try std.testing.expectEqual(fixed_result.steps, epochal_result.steps);
    try std.testing.expectEqual(@as(u32, 0), epochal.stats.growth_events);
}

test "frontier trigger preserves an existing memory cell" {
    const alloc = std.testing.allocator;
    var vm = core.MalbolgeCore.initFreeAssisted(alloc, 10, null, .epochal);
    defer vm.deinit();
    try vm.load("(!#");
    try vm.mem.put(100, 424242);
    const before = vm.mem.get(100).?;

    vm.frontierTrigger(59049, 59049);

    try std.testing.expectEqual(@as(u8, 11), vm.padwidth);
    try std.testing.expectEqual(@as(u32, 1), vm.stats.growth_events);
    try std.testing.expectEqual(before, vm.mem.get(100).?);
}

test "same epochal source is deterministic" {
    const alloc = std.testing.allocator;
    var first = core.MalbolgeCore.initFreePure(alloc, 10, .epochal);
    defer first.deinit();
    try first.load(PROG);
    var second = core.MalbolgeCore.initFreePure(alloc, 10, .epochal);
    defer second.deinit();
    try second.load(PROG);

    var r1 = try first.run(5_000, "");
    defer r1.stdout.deinit(alloc);
    var r2 = try second.run(5_000, "");
    defer r2.stdout.deinit(alloc);

    try std.testing.expectEqual(r1.steps, r2.steps);
    try std.testing.expectEqualStrings(r1.stdout.items, r2.stdout.items);
    try std.testing.expectEqual(first.padwidth, second.padwidth);
    try std.testing.expectEqual(first.stats.growth_events, second.stats.growth_events);
}
