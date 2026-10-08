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
    if (target < 1 or target > 20) return error.TargetOutOfRange;

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

    var vm = core.MalbolgeCore.initFreePure(alloc, 1, .epochal);
    defer vm.deinit();
    if (cfg.dense) {
        // Dense representation: the materialised range is a flat u32 array, so
        // there is nothing to pre-reserve in the hash map. Reserving here would
        // defeat the whole point (it is ~33 bytes per source cell).
        try vm.enableDenseSource();
        std.debug.print("representation=dense (u32 array, {d} bytes for {d} cells)\n", .{
            (@as(u64, len) + 12) * @sizeOf(u32),
            len + 12,
        });
    } else {
        try vm.mem.ensureTotalCapacity(@intCast(len + 16));
        std.debug.print("reserved capacity={d} (~{d} MiB of key/value/metadata)\n", .{
            vm.mem.capacity(),
            @as(u64, vm.mem.capacity()) * (2 * @sizeOf(u128) + 1) / (1024 * 1024),
        });
    }
    try vm.load(src);

    std.debug.print("LABEL boot_width=1 source_ascii_min=33 boot_word_max=2 source_cells_outside_boot_word={d} classification=PARAMETRIC_ASCII_OUTSIDE_BOOT_WORD\n", .{len});
    var trace = std.ArrayList(core.TraceEvent).empty;
    defer trace.deinit(alloc);
    var res = if (cfg.audit) try vm.runWithTrace(need, "", &trace) else try vm.run(need, "");
    if (cfg.audit) {
        var width: u8 = 1;
        var fetches = [_]u64{0} ** 21;
        var outside_fetch = [_]u64{0} ** 21;
        var encrypted = [_]u64{0} ** 21;
        var outside_encryption = [_]u64{0} ** 21;
        for (trace.items) |event| {
            if (event.c_before >= core.pow3(width) or event.d_before >= core.pow3(width)) width += 1;
            fetches[width] += 1;
            if (event.cell_before >= core.pow3(width)) outside_fetch[width] += 1;
            if (event.encrypted_value) |value| {
                encrypted[width] += 1;
                if (value >= core.pow3(width)) outside_encryption[width] += 1;
            }
        }
        for (1..21) |w| {
            if (fetches[w] != 0) std.debug.print("AUDIT width={d} fetches={d} fetched_cells_outside_word={d} encrypted_cells={d} encryption_results_outside_word={d}\n", .{w, fetches[w], outside_fetch[w], encrypted[w], outside_encryption[w]});
        }
    }
    defer res.stdout.deinit(alloc);

    // Representation-independent view of the same measurement, so a dense run
    // stays comparable with a historical hash-map row.
    const cells: usize = if (vm.dense) |dn| dn.len + vm.mem.count() else vm.mem.count();

    std.debug.print(
        "RESULT target={d} status={s} steps={d} padwidth={d} growth={d} final_c={d} cells={d} capacity={d} stdout_len={d} repr={s}\n",
        .{ target, res.status, res.steps, vm.padwidth, vm.stats.growth_events, res.final_c, cells, vm.mem.capacity(), res.stdout.items.len, if (cfg.dense) "dense" else "hash" },
    );
    var source_hash: [32]u8 = undefined;
    var stdout_hash: [32]u8 = undefined;
    std.crypto.hash.sha2.Sha256.hash(src, &source_hash, .{});
    std.crypto.hash.sha2.Sha256.hash(res.stdout.items, &stdout_hash, .{});
    std.debug.print("HASH source={s} stdout={s} final_d={d} encrypted={d} assisted={d}\n", .{std.fmt.bytesToHex(source_hash, .lower), std.fmt.bytesToHex(stdout_hash, .lower), res.final_d, res.encrypted_cells, res.assisted_opcodes});
    if (vm.padwidth != target or vm.stats.growth_events != target - 1) return error.LadderDidNotReachTarget;
}
