//! F7 diagnostic: trace (step, c, d, op, a) for the first N steps.

const std = @import("std");
const core = @import("malbolge_free.zig");
const MalbolgeCore = core.MalbolgeCore;
const crazy = core.crazy;
const _ENC = core._ENC;

pub fn main() !void {
    const alloc = std.heap.page_allocator;
    const src = "('&%$" ++ "z" ** 200;

    var vm = MalbolgeCore.init(alloc, 20, null, .fixed);
    defer vm.deinit();
    try vm.load(src);

    var a: u128 = 0;
    var c: u128 = 0;
    var d: u128 = 0;

    for (0..80) |step| {
        const cell = try vm.cell(c);
        const op = (cell + c) % 94;
        std.debug.print("step={d} c={d} d={d} cell={s} op={d} a={d} max_addr={d}\n", .{
            step, c, d,
            switch (cell) {
                0 => "0",
                1 => "1",
                2 => "2",
                else => fmt: {
                    break :fmt @as([]const u8, "n");
                },
            }, op, a, vm.stats.max_addr,
        });

        switch (op) {
            4 => c = try vm.cell(d),
            5 => {},
            23 => {},
            39 => {
                const v = try vm.cell(d);
                const w = vm.rotWidthFor(v);
                const nv = core.rotate(v, w);
                try vm.cellWrite(d, nv);
                a = nv;
                vm.maybeGrow(a);
            },
            40 => {
                d = try vm.cell(d);
                vm.maybeGrow(d);
            },
            62 => {
                const v = try vm.cell(d);
                const w = switch (vm.growth) {
                    .fixed => vm.width,
                    .pad_to_padwidth => @max(@max(vm.padwidth, core.tritlen(v)), core.tritlen(a)),
                };
                const nv = crazy(@min(a, core.pow3(w) - 1), v, w);
                try vm.cellWrite(d, nv);
                a = nv;
            },
            68 => {},
            81 => {
                std.debug.print("HALT at step {d}\n", .{step});
                break;
            },
            else => {},
        }

        const mc = try vm.cell(c);
        if (mc >= 33 and mc <= 126) {
            const idx: usize = @intCast(mc - 33);
            try vm.cellWrite(c, core.TRANSLATED[idx]);
        }

        c += 1;
        d += 1;
    }
}
