//! F7c — the moment of crossing. Instrument step-by-step: print state when
//! growth_events increments (i.e., when the width widens).

const std = @import("std");
const core = @import("malbolge_free.zig");
const MalbolgeCore = core.MalbolgeCore;

pub fn main() !void {
    const alloc = std.heap.page_allocator;

const src = @embedFile("frontier_witness.txt");

    var vm = MalbolgeCore.init(alloc, 10, null, .epochal);
    defer vm.deinit();
    try vm.load(src);

    var a: u128 = 0;
    var c: u128 = 0;
    var d: u128 = 0;
    const MAX: u64 = 200_000;

    var steps: u64 = 0;
    var widen_events: u32 = 0;
    var crosses: [10]u64 = undefined;
    var cross_n: usize = 0;


    while (steps < MAX) {
        steps += 1;

        // manually perform cell read (bypass the .run loop)
        const cell = try vm.cell(if (vm.mem_limit) |lim| c % lim else c);
        const op = (cell + c) % 94;

        switch (op) {
            4 => {},
            5 => {},
            23 => a = 255, // EOF sentinel as byte
            39 => {
                const v = try vm.cell(if (vm.mem_limit) |lim| d % lim else d);
                const w = vm.rotWidthFor(v);
                const nv = core.rotate(v, w);
                try vm.cellWrite(if (vm.mem_limit) |lim| d % lim else d, nv);
                a = nv;
            },
            40 => {
                const dd = if (vm.mem_limit) |lim| d % lim else d;
                d = try vm.cell(dd);
            },
            62 => {},
            68 => {},
            81 => break,
            else => {},
        }

        const old_w = vm.padwidth;
        vm.frontierTrigger(c, d);
        if (vm.padwidth != old_w) {
            widen_events += 1;
            crosses[cross_n] = steps;
            cross_n += 1;
            std.debug.print("WIDEN step={d} c={d} d={d} old_w={d} new_w={d}\n", .{
                steps, c, d, old_w, vm.padwidth,
            });
        }

        c += 1; d += 1;
    }

    std.debug.print("run status: steps={d} widen_events={d} at steps {any}\n", .{
        steps, widen_events, crosses[0..widen_events],
    });
    std.debug.print("final padwidth={d}\n", .{vm.padwidth});
}
