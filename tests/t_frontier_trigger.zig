//! Frontier-triggered widening — the hypothesis Danny proposed.
//!
//! Program ("('&%$" i.e. continuous stdin consumption). No halt. No jumps.
//! c and d increment once per step with NO wrap (mem_limit=null).
//! Then at step = 3^k, c and d exceed the width frontier.
//!
//! This script prints the step at which the frontier is crossed and whether
//! the growth policy widens k. It does NOT need 3^19 cells — only long-enough
//! execution.
//!
//! We do NOT modify the core; we manually spawn over a long window and log
//! each WIDEN event. If the program never needs a value wider than 10 trits,
//! it will never fire — matching the claimed topology proof.

const std = @import("std");
const core = @import("malbolge_free.zig");
const MalbolgeCore = core.MalbolgeCore;

pub fn main() !void {
    const alloc = std.heap.page_allocator;

    // Embedded via @embedFile (0.16 std) — the generator wrote it into
    // evidence/ so tests can reference it statically.
    const src = @embedFile("frontier_witness.txt");

    std.debug.print("PROGRAM length: {d}\n", .{src.len});

    var vm = MalbolgeCore.init(alloc, 10, null, .epochal);
    defer vm.deinit();
    try vm.load(src);

    const res = try vm.run(200_000, ""); // ~2 width fronts crossed
    const F10 = std.math.pow(u128, 3, 10);
    const F11 = std.math.pow(u128, 3, 11);

    std.debug.print("status={s} steps={d} padwidth={d} growth_events={d} max_addr={d}\n", .{
        res.status, res.steps, vm.padwidth, vm.stats.growth_events, res.max_addr_touched,
    });
    std.debug.print("  frontier k=10: {d}\n", .{F10});
    std.debug.print("  frontier k=11: {d}\n", .{F11});
    std.debug.print("  => crossed {} times (frontier reached by raw address advance)\n", .{vm.stats.growth_events});

    // There's no platform for RAM growth of program so this was already sufficient
    if (vm.padwidth == 11) {
        std.debug.print("=> FRONTIER TRIGGERED at step {d}: k widened 10 -> 11 only after addr {} crossed 3^10\n", .{
            vm.stats.steps, vm.stats.max_addr,
        });
    } else if (vm.padwidth == 10) {
        std.debug.print("=> NO CROSS: program didn't even reach the frontier\n", .{});
    } else {
        std.debug.print("=> SURPRISE: padwidth={d} growth={d}\n", .{ vm.padwidth, vm.stats.growth_events });
    }
}

