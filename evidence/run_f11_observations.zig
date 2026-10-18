//! F11 observations: the value `in` assigns at end of input, and the first step
//! at which an address reaches the Classic frontier, for each profile.
//!
//! Why this driver exists as its own file: the EOF rule in both cores is
//! `3^padwidth - 1` (HONESTY_LEDGER entry 24), and `padwidth` is a *variable*
//! under `epochal`. So end-of-input has to return a different value once the
//! machine has widened, and that has to be MEASURED rather than inferred from
//! the source line. `run_quine_epochal.zig` compares whole runs and traces; it
//! never reports an individual `in` event, which is the observable needed here.
//!
//! One program, three profiles, one bounded budget:
//!   classic     width 10, mem_limit = 3^10 (addresses wrap)  == Malbolge
//!   pure_fixed  width 10, mem_limit = null (no wrap, no growth)
//!   epochal     width 10, mem_limit = null (no wrap, widen at the frontier)
//!
//! Reads only: writes no file, mutates nothing in src/.
const std = @import("std");
const core = @import("malbolge_free");

fn shaHex(bytes: []const u8) [64]u8 {
    var h = std.crypto.hash.sha2.Sha256.init(.{});
    h.update(bytes);
    var digest: [32]u8 = undefined;
    h.final(&digest);
    return std.fmt.bytesToHex(digest, .lower);
}

fn pow3(n: u8) u128 {
    var v: u128 = 1;
    var i: u8 = 0;
    while (i < n) : (i += 1) v *= 3;
    return v;
}

const Profile = enum { classic, pure_fixed, epochal };

fn newVm(comptime p: Profile, alloc: std.mem.Allocator) core.MalbolgeCore {
    return switch (p) {
        .classic => core.MalbolgeCore.initClassic(alloc),
        .pure_fixed => core.MalbolgeCore.initFreePure(alloc, 10, .fixed),
        .epochal => core.MalbolgeCore.initFreePure(alloc, 10, .epochal),
    };
}

pub fn main(init: std.process.Init) !void {
    const alloc = init.arena.allocator();
    var args = try std.process.Args.Iterator.initAllocator(init.minimal.args, alloc);
    _ = args.next();
    const program_path = args.next() orelse return error.MissingProgram;
    const budget: u64 = if (args.next()) |raw|
        try std.fmt.parseInt(u64, raw, 10)
    else
        60_000;

    const src = try std.Io.Dir.cwd().readFileAlloc(init.io, program_path, alloc, .unlimited);
    std.debug.print("PROG bytes={d} sha={s} budget={d}\n", .{ src.len, shaHex(src), budget });

    inline for (.{ .classic, .pure_fixed, .epochal }) |p| {
        const name = @tagName(p);
        var vm = newVm(p, alloc);
        try vm.load(src);
        var trace: std.ArrayList(core.TraceEvent) = .empty;
        const res = try vm.runWithTrace(budget, "", &trace);

        std.debug.print(
            \\RUN prof={s} status={s} steps={d} padwidth={d} growth={d} max_addr={d} cells={d} stdout_len={d} stdout_sha={s}
            \\
        , .{
            name,
            res.status,
            res.steps,
            vm.padwidth,
            vm.stats.growth_events,
            res.max_addr_touched,
            res.cells_materialized,
            res.stdout.items.len,
            shaHex(res.stdout.items),
        });

        var in_events: u32 = 0;
        var first_frontier: ?u64 = null;
        for (trace.items) |ev| {
            if (ev.op == 23) {
                in_events += 1;
                std.debug.print("IN prof={s} step={d} a_after={d}\n", .{ name, ev.step, ev.a_after });
            }
            if (first_frontier == null and
                (ev.c_after >= pow3(10) or ev.d_after >= pow3(10)))
            {
                first_frontier = ev.step;
            }
        }
        std.debug.print(
            \\OBS prof={s} in_events={d} first_addr_ge_3pow10_step={?d} trace_events={d}
            \\
        , .{ name, in_events, first_frontier, trace.items.len });
    }
}
