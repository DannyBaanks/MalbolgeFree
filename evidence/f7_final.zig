//! F7 final — O(1) lazy-fill using the 6-periodic crazy chain.
//! New cell():  mem[i] = crazy-fill value, computed from seed (a0, a1) at
//! program_len without touching intermediate cells.
//!
//! Backed by evidence: crazy chain from any seed is 6-periodic from index 1.

const std = @import("std");
const core = @import("malbolge_free.zig");
const MalbolgeCore = core.MalbolgeCore;

pub fn main() !void {
    const alloc = std.heap.page_allocator;
    const src = "('"; // movd movd
    const boundary = std.math.pow(u128, 3, 19); // 1,162,261,467

    std.debug.print("=== F7 witness: src=\"('\" (movd movd) ===\n", .{});
    std.debug.print("3^19 = {d}\n", .{boundary});

    const Cfgs = [_]struct { w: u8, name: []const u8 }{
        .{ .w = 10, .name = "Classic" },
        .{ .w = 19, .name = "Unshackled-like" },
        .{ .w = 20, .name = "Free(K_arbitrary)" },
    };
    std.debug.print("seed_known6 = with periodic lazy fill, all widths: compute amazingly fast\n", .{});
    std.debug.print("(this witnesses what touching a huge address means; not an executable run)\n", .{});

    for (Cfgs) |cfg| {
        var vm = MalbolgeCore.init(alloc, cfg.w, null, .fixed);
        defer vm.deinit();
        try vm.load(src);

        // movd movd: c=0 d=0 -> d=mem[0]='(' (40); c=1 d=41 -> d=mem[41]
        std.debug.print("program width {d}: mem[0]='('={d}; lazy fill starts at idx 2\n", .{ cfg.w, @as(u128, '(') });
        const mem41 = try vm.cell(41);
        std.debug.print("  mem[41] orderly-computed = {d}\n", .{mem41});
        const d_next = mem41;
        std.debug.print("  movd 1 (at c=1) => d := mem[41] = {d}\n", .{d_next});
        if (d_next >= boundary) {
            std.debug.print("  => the next instruction reads mem[d] at d>3^19: LEGAL CROSSING ^ω^\n", .{});
        }
    }
}
