//! Confirm the epochal trigger fires when c crosses 3^k. Use a program that
//! avoids halt for ~3^10+20 steps — simplest: one infinite-loop nixen.
//! We bypassed encoding noise using NJ-style infinite loop:
//!   pos0: '(' — op40 movd
//!   oversize washer: we only care about crossing 3^k = 59049 steps.

const std = @import("std");
const core = @import("malbolge_free.zig");
const MalbolgeCore = core.MalbolgeCore;

pub fn main() !void {
    const alloc = std.heap.page_allocator;

    // Sufficient: c keeps incrementing. encoder pattern: position0='(' op40 movd
    // lets d jump to a gigantic lazy value which on next movd content rewrites
    // cell but d keeps ascending.

    const src = "(" ++ "z" ** 200;
    var vm = MalbolgeCore.init(alloc, 10, null, .epochal);
    defer vm.deinit();
    try vm.load(src);
    const res = try vm.run(60_000, "");
    const b10 = std.math.pow(u128, 3, 10);
    std.debug.print("status={s} steps={d} growth_events={d} padwidth={d} max_addr={d} boundary={d}\n", .{
        res.status, res.steps, vm.stats.growth_events, vm.padwidth, res.max_addr_touched, b10,
    });
    if (vm.padwidth == 11) {
        std.debug.print("=> EPOCHAL WIDENED at the 3^10 frontier.\n", .{});
    } else {
        std.debug.print("=> no crossing: max_addr={d} < {d}\n", .{res.max_addr_touched, b10});
    }
}
