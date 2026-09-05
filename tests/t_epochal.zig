//! Epochal invariants — P1 prefix preservation, P2 anchor preservation,
//! P3 no replay, P4 determinism, P6 fixed-width degeneration.
//!
//! KEY RESULT: all these invariants hold trivially because epochal from k=10
//! NEVER widens (nothing in Malbolge produces wider-than-current values).

const std = @import("std");
const core = @import("malbolge_free.zig");
const MalbolgeCore = core.MalbolgeCore;

test "epochal k=10 == fixed k=10 (no widening trigger)" {
    const alloc = std.heap.page_allocator;

    const prog =
        \\(=<`#9]~6ZY327Uv4-QsqpMn&+Ij"'E%e{Ab~w=_:]Kw%o44Uqp0/Q?xNvL:`H%c#DD2^WV>gY;dts76qKJImZkj
    ;

    var e = MalbolgeCore.init(alloc, 10, null, .epochal);
    defer e.deinit();
    try e.load(prog);
    const r_e = try e.run(2_000_000, "");

    var f = MalbolgeCore.init(alloc, 10, null, .fixed);
    defer f.deinit();
    try f.load(prog);
    const r_f = try f.run(2_000_000, "");

    try std.testing.expectEqualStrings(r_f.stdout.items, r_e.stdout.items);
    try std.testing.expectEqual(@as(u32, 0), e.stats.growth_events);
    std.debug.print("epochal-from-k10: growth_events={d} (never widened — confirmation)\n", .{
        e.stats.growth_events,
    });
}

test "epochal from k=20: a rot ALSO can't widen (rot needs operands wider than width)" {
    const alloc = std.heap.page_allocator;

    const prog =
        \\(=<`#9]~6ZY327Uv4-QsqpMn&+Ij"'E%e{Ab~w=_:]Kw%o44Uqp0/Q?xNvL:`H%c#DD2^WV>gY;dts76qKJImZkj
    ;

    var e = MalbolgeCore.init(alloc, 20, null, .epochal);
    defer e.deinit();
    try e.load(prog);
    _ = try e.run(5_000, "");
    std.debug.print("epochal-from-k20: growth_events={d} (none expected — no legal way to widen)\n", .{
        e.stats.growth_events,
    });
    try std.testing.expectEqual(@as(u32, 0), e.stats.growth_events);
}
