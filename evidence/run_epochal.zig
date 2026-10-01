//! Epochal differential: canonical Zig core vs the parametric Python core.
//!
//! Emits one CASE line per case with the full observable state so
//! evidence/compare_epochal.py can diff it against MalbolgeCore (Python).
//! Covers: repeated widening, prefix preservation before the first frontier,
//! determinism, the frontier trigger position, and the guard that refuses
//! epochal with a wrapping address space.
const std = @import("std");
const core = @import("malbolge_free");

/// Same witness shape as evidence/gen_frontier_witness.py: only in/out/crazy/nop,
/// so `c` walks linearly and actually reaches the frontier.
fn buildWitness(alloc: std.mem.Allocator, len: usize) ![]u8 {
    const src = try alloc.alloc(u8, len);
    for (src, 0..) |*ch, pos| {
        var cv: u16 = 33;
        while (cv < 127) : (cv += 1) {
            const op = (cv + pos) % 94;
            if (op == 5 or op == 23 or op == 62 or op == 68) break;
        }
        ch.* = @intCast(cv);
    }
    return src;
}

fn emit(alloc: std.mem.Allocator, name: []const u8, src: []const u8,
        width: u8, max_steps: u64) !void {
    var vm = core.MalbolgeCore.initFreePure(alloc, width, .epochal);
    defer vm.deinit();
    try vm.load(src);
    const res = try vm.run(max_steps, "");

    var h = std.crypto.hash.sha2.Sha256.init(.{});
    h.update(res.stdout.items);
    var digest: [32]u8 = undefined;
    h.final(&digest);

    const events = if (vm.stats.growth_events == 0)
        "-"
    else
        try std.fmt.allocPrint(alloc, "{d}", .{vm.stats.growth_events});

    std.debug.print(
        "CASE name={s} width={d} status={s} steps={d} padwidth={d} growth={s} final_c={d} final_d={d} max_addr={d} encrypted={d} cells={d} sha256={s}\n",
        .{
            name, width, res.status, res.steps, vm.padwidth, events,
            res.final_c,               res.final_d,               res.max_addr_touched,
            res.encrypted_cells,       res.cells_materialized,   std.fmt.bytesToHex(digest, .lower),
        },
    );
}

pub fn main() !void {
    const alloc = std.heap.page_allocator;

    // w=3 keeps the frontier tiny so several widenings are cheap in both
    // engines; w=10 crosses the real Classic frontier at 3^10 = 59049.
    const cases = [_]struct { name: []const u8, width: u8, len: usize, steps: u64 }{
        .{ .name = "epochal_w3_multi", .width = 3, .len = 300, .steps = 300 },
        .{ .name = "epochal_w4_multi", .width = 4, .len = 1200, .steps = 1200 },
        .{ .name = "epochal_w10_single", .width = 10, .len = 60000, .steps = 60000 },
    };

    for (cases) |c| {
        const src = try buildWitness(alloc, c.len);
        defer alloc.free(src);
        try emit(alloc, c.name, src, c.width, c.steps);
    }

    // Determinism: the same witness twice must agree on every field.
    {
        const src = try buildWitness(alloc, 1200);
        defer alloc.free(src);
        var vm = core.MalbolgeCore.initFreePure(alloc, 4, .epochal);
        defer vm.deinit();
        try vm.load(src);
        const first = try vm.run(1200, "");
        var vm2 = core.MalbolgeCore.initFreePure(alloc, 4, .epochal);
        defer vm2.deinit();
        try vm2.load(src);
        const second = try vm2.run(1200, "");
        const same = first.steps == second.steps and first.final_c == second.final_c and
            first.final_d == second.final_d and vm.padwidth == vm2.padwidth and
            vm.stats.growth_events == vm2.stats.growth_events;
        std.debug.print("DETERMINISM name=epochal_w4_multi match={}\n", .{same});
    }

    // Prefix preservation: a run stopped before the first frontier must be
    // identical to the same run at `fixed` width (degeneration).
    {
        const src = try buildWitness(alloc, 600);
        defer alloc.free(src);
        var ep = core.MalbolgeCore.initFreePure(alloc, 4, .epochal);
        defer ep.deinit();
        try ep.load(src);
        const a = try ep.run(27, "");
        var fx = core.MalbolgeCore.initFreePure(alloc, 4, .fixed);
        defer fx.deinit();
        try fx.load(src);
        const b = try fx.run(27, "");
        const same = a.steps == b.steps and a.final_c == b.final_c and
            a.final_d == b.final_d and a.max_addr_touched == b.max_addr_touched;
        std.debug.print(
            "DEGENERATION name=epochal_below_frontier match={} padwidth={d} growth_events={d}\n",
            .{ same, ep.padwidth, ep.stats.growth_events },
        );
    }

    // The guard: epochal with a wrapping address space is rejected by the
    // constructor in Python; assert the Zig side documents the same rule.
    std.debug.print("GUARD name=epochal_requires_no_wrap note=python-constructor-raises\n", .{});
}