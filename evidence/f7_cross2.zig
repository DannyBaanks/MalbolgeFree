//! F7 v2 — two-phase crossing:
//!
//!   Step 0 (c=0): movd — d = mem[0] = '(' = 40
//!   Step 1 (c=1, d=41): movd — d = mem[41]   <- lazy-filled under width=k
//!   Step 2 (c=2, d=bigger): movd — READ at address d  <-- THE CROSSING
//!
//! If k=20, mem[41] can be up to 3^20 ints; the read at step 2 touches
//! address > 3^19. No host mutation, no fixtures — just executing the
//! loadable Malbolge program against legal crazy-fill.

const std = @import("std");
const core = @import("malbolge_free.zig");
const MalbolgeCore = core.MalbolgeCore;

pub fn main() !void {
    const alloc = std.heap.page_allocator;
    // Found by evidence/find_movd_chain.py:
    //   c=0: movd (40 = '(')
    //   c=1: movd (39 = '\'')
    //   c=2: rot  (39 at pos 2 needs cell 37 = '%')  -> forces a READ at huge d
    //   c=3: hlt  (81 at pos 3 needs cell 78 = 'N')
    const src = "('%N";

    const configs = [_]struct { w: u8, name: []const u8 }{
        .{ .w = 10, .name = "k10_classic_wrap" },
        .{ .w = 20, .name = "k20_free" },
    };
    for (configs) |cfg| {
        var vm = MalbolgeCore.init(alloc, cfg.w, null, .fixed);
        defer vm.deinit();
        try vm.load(src);
        const res = try vm.run(100, "");
        const boundary = std.math.pow(u128, 3, 19);
        std.debug.print("cfg={s} status={s} steps={d} max_addr={d} 3^19={d} crossed={} max_value={d}\n", .{
            cfg.name,
            res.status,
            res.steps,
            res.max_addr_touched,
            boundary,
            res.max_addr_touched >= boundary,
            res.max_value,
        });
    }
}
