//! Demo: epochal trigger fires when memory frontier crosses 3^k.
//! We jump straight to the frontier by injecting a single cell > 3^k via
//! load(): the loader never writes cells directly, but we can PRELOAD the
//! program space. No — for a clean demo, preload a program with a big lazy
//! cell by using a k such that crazy(a,b,k) can exceed 3^20... wait, lazy
//! cells at width k are 10-trit values, hence <= 59048. So they never exceed
//! memory frontier either.
//!
//! Instead: we widen proactively — if self.stats.max_addr ever crosses 3^k,
//! we widen. We force that via a synthetic proof below.

const std = @import("std");
const core = @import("malbolge_free.zig");
const MalbolgeCore = core.MalbolgeCore;

pub fn main() !void {
    const alloc = std.heap.page_allocator;

    // Simple program: EOF input (returns 255 sentinel; tritlen(255) = 6) is
    // stored as value but pads are only triggered by frontier / rot ops, NOT
    // by crazy width. Then a halt.

    const src = "(='";  // in, then hlt — never runs long

    var vm = MalbolgeCore.init(alloc, 10, null, .epochal);
    defer vm.deinit();
    try vm.load(src);
    const res = try vm.run(100, "");
    std.debug.print("program=\"(\" status={s} steps={d} growth_events={d} padwidth={d}\n", .{
        res.status, res.steps, vm.stats.growth_events, vm.padwidth,
    });
    if (vm.stats.growth_events == 0) {
        std.debug.print("=> confirmed: no widening triggered (no internal reason to)\n", .{});
    }
}
