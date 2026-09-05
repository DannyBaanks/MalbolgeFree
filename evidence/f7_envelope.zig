//! F7 — Approach to crossing 3^19: observe reachable address range vs width.
//! Experiment: what the largest address touched by a REAL program is under
//! different widths. Does NOT claim a legal 3^19 crossing; just measures the
//! reachable envelope so far.

const std = @import("std");
const core = @import("malbolge_free.zig");
const MalbolgeCore = core.MalbolgeCore;

const Program = struct {
    name: []const u8,
    src: []const u8,
    width: u8,
    growth: core.GrowthPolicy,
};

const PROGRAMS = [_]Program{
    .{ .name = "hello_k10_fixed", .src = "(=<`#9]~6ZY327Uv4-QsqpMn&+Ij\"'E%e{Ab~w=_:]Kw%o44Uqp0/Q?xNvL:`H%c#DD2^WV>gY;dts76qKJImZkj", .width = 10, .growth = .fixed },
    .{ .name = "hello_k10_pad", .src = "(=<`#9]~6ZY327Uv4-QsqpMn&+Ij\"'E%e{Ab~w=_:]Kw%o44Uqp0/Q?xNvL:`H%c#DD2^WV>gY;dts76qKJImZkj", .width = 10, .growth = .pad_to_padwidth },
    .{ .name = "reproducer_k10_fixed", .src = "bCBA@?>=<;:9876543210/.-,+*)('&%$#\"!~}|{zyxwvutsrqponmlkjihgfedcba`_^]\\[ZYXWVUTS", .width = 10, .growth = .fixed },
};

pub fn main() !void {
    const alloc = std.heap.page_allocator;

    for (PROGRAMS) |p| {
        var vm = MalbolgeCore.init(alloc, p.width, null, p.growth);
        defer vm.deinit();
        try vm.load(p.src);
        const res = try vm.run(2_000_000, "");
        var mv = res.max_value;
        var trits: u8 = 1;
        while (mv >= 3) : (mv /= 3) trits += 1;
        std.debug.print("program={s} width={d} growth={s} status={s} steps={d} max_addr={d} max_value={d} max_value_trits={d} growth_events={d}\n", .{
            p.name,
            p.width,
            @tagName(p.growth),
            res.status,
            res.steps,
            res.max_addr_touched,
            res.max_value,
            trits,
            vm.stats.growth_events,
        });
    }
}
