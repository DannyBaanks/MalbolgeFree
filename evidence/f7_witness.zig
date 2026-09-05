//! F7 — CONFIRMED WITNESS. "opchin movd chain" lands d=1743392169.
//! Verified Python-side (f7_python_check.py) -> we now prove same run on Zig
//! core, which is exactly what run() does. No host intervention.

const std = @import("std");
const core = @import("malbolge_free.zig");
const MalbolgeCore = core.MalbolgeCore;

pub fn main() !void {
    const alloc = std.heap.page_allocator;
    const src = "('&%";
    const boundary = std.math.pow(u128, 3, 19);

    const Cfgs = [_]struct { w: u8, g: core.GrowthPolicy, name: []const u8 }{
        .{ .w = 10, .g = .fixed, .name = "k10_fixed" },
        .{ .w = 20, .g = .fixed, .name = "k20_fixed" },
        .{ .w = 20, .g = .pad_to_padwidth, .name = "k20_pad" },
    };

    for (Cfgs) |cfg| {
        var vm = MalbolgeCore.init(alloc, cfg.w, null, cfg.g);
        defer vm.deinit();
        try vm.load(src);
        const res = try vm.run(50, "");
        std.debug.print("cfg={s} status={s} steps={d} max_addr={d} >3^19={} max_value={d}\n", .{
            cfg.name, res.status, res.steps, res.max_addr_touched,
            res.max_addr_touched > boundary, res.max_value,
        });
    }
}
