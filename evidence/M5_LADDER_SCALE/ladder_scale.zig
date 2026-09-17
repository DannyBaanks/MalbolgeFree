//! M5 scale probe: how far does the epochal ladder climb on a real machine?
//!
//! Builds the same kind of witness as evidence/gen_frontier_witness.py (only
//! in/out/crazy/nop at every position, so `c` walks linearly), long enough for
//! `c` to reach 3^(target-1), and runs it on the REAL VM loop (`vm.run`), not a
//! hand-stepped loop. The target width comes from the `ladder_cfg` module,
//! which run_ladder_scale.py writes.
//!
//! Memory is the limit, not time: every executed cell is encrypted and stored
//! in the core's hash map. The table is reserved up front so it never doubles
//! while running (a resize would briefly hold the old and the new table).
const std = @import("std");
const core = @import("malbolge_free");
const cfg = @import("ladder_cfg");

pub fn main() !void {
    const alloc = std.heap.smp_allocator;
    const target: u8 = cfg.target_w;
    if (target < 11 or target > 30) return error.TargetOutOfRange;

    // The widening to `target` happens at the step where c = 3^(target-1).
    const need: u64 = @intCast(core.pow3(target - 1) + 1);
    const len: usize = @intCast(need + 1000);

    const src = try alloc.alloc(u8, len);
    defer alloc.free(src);
    for (src, 0..) |*ch, pos| {
        var cv: u16 = 33;
        while (cv < 127) : (cv += 1) {
            const op = (cv + pos) % 94;
            if (op == 5 or op == 23 or op == 62 or op == 68) break;
        }
        ch.* = @intCast(cv);
    }

    var vm = core.MalbolgeCore.initFreePure(alloc, 10, .epochal);
    defer vm.deinit();
    try vm.mem.ensureTotalCapacity(@intCast(len + 16));
    std.debug.print("reserved capacity={d} (~{d} MiB of key/value/metadata)\n", .{
        vm.mem.capacity(),
        @as(u64, vm.mem.capacity()) * (2 * @sizeOf(u128) + 1) / (1024 * 1024),
    });
    try vm.load(src);

    var res = try vm.run(need, "");
    defer res.stdout.deinit(alloc);

    std.debug.print(
        "RESULT target={d} status={s} steps={d} padwidth={d} growth={d} final_c={d} cells={d} capacity={d} stdout_len={d}\n",
        .{ target, res.status, res.steps, vm.padwidth, vm.stats.growth_events, res.final_c, vm.mem.count(), vm.mem.capacity(), res.stdout.items.len },
    );
    if (vm.padwidth != target or vm.stats.growth_events != target - 10) return error.LadderDidNotReachTarget;
}
