//! Quine-under-epochal differential.
//!
//! Question: does `epochal` agree with Classic on a program that survives
//! longer than the Classic frontier `3^10 = 59049`? The F9 witnesses are
//! synthetic and stop at 190 000 steps; a self-reproducing program is a harder
//! input because its design depends on revisiting its own cells.
//!
//! Three profiles, one program, two budgets:
//!   classic     width 10, mem_limit = 3^10 (addresses wrap)  == Malbolge
//!   pure_fixed  width 10, mem_limit = null (no wrap, no growth)
//!   epochal     width 10, mem_limit = null (no wrap, widen at the frontier)
//!
//! `pure_fixed` is the decomposition control: it separates "no wrap" from
//! "growth", so a divergence is not blamed on the wrong mechanism.
//!
//! Pass 1 compares per-step traces below the trace budget; pass 2 compares
//! stdout at the (larger) stdout budget without keeping traces. Reads only:
//! it writes no file and mutates nothing in src/.
const std = @import("std");
const core = @import("malbolge_free");

fn shaHex(bytes: []const u8) [64]u8 {
    var h = std.crypto.hash.sha2.Sha256.init(.{});
    h.update(bytes);
    var digest: [32]u8 = undefined;
    h.final(&digest);
    return std.fmt.bytesToHex(digest, .lower);
}

const Profile = enum { classic, pure_fixed, epochal };

const Out = struct {
    status: []const u8,
    steps: u64,
    padwidth: u8,
    growth_events: u32,
    final_c: u128,
    final_d: u128,
    max_addr: u128,
    cells: u32,
    stdout: []const u8,
};

fn newVm(comptime p: Profile, alloc: std.mem.Allocator) core.MalbolgeCore {
    return switch (p) {
        .classic => core.MalbolgeCore.initClassic(alloc),
        .pure_fixed => core.MalbolgeCore.initFreePure(alloc, 10, .fixed),
        .epochal => core.MalbolgeCore.initFreePure(alloc, 10, .epochal),
    };
}

/// Addressed image taken BEFORE execution, on a throwaway vm so the run
/// observables (max_addr_touched, cells_materialized) stay pristine.
/// `load` ignores mem_limit, so the STORED image is profile-independent by
/// construction; only the ADDRESSED image can differ — which is what turns a
/// divergence into an addressing effect rather than a load effect.
fn imageProbe(comptime p: Profile, alloc: std.mem.Allocator, src: []const u8) !struct {
    stored_sha: [64]u8,
    addressed_sha: [64]u8,
    values: []const u128,
    program_len: u128,
} {
    var vm = newVm(p, alloc);
    try vm.load(src);
    const n = vm.program_len + 12;
    // The probe allocates one slot per source cell; a program longer than the
    // address space of usize is not a thing this driver will ever see.
    const vals = try alloc.alloc(u128, @intCast(n));
    var stored = std.crypto.hash.sha2.Sha256.init(.{});
    var addressed = std.crypto.hash.sha2.Sha256.init(.{});
    var i: u128 = 0;
    while (i < n) : (i += 1) {
        const s = vm.mem.get(i) orelse 0xFFFF_FFFF_FFFF_FFFF;
        const v = try vm.cell(i);
        vals[@intCast(i)] = v;
        stored.update(&std.mem.toBytes(s));
        addressed.update(&std.mem.toBytes(v));
    }
    var sd: [32]u8 = undefined;
    var ad: [32]u8 = undefined;
    stored.final(&sd);
    addressed.final(&ad);
    return .{
        .stored_sha = std.fmt.bytesToHex(sd, .lower),
        .addressed_sha = std.fmt.bytesToHex(ad, .lower),
        .values = vals,
        .program_len = vm.program_len,
    };
}

fn firstDiffIndex(a: []const u128, b: []const u128) ?usize {
    const n = @min(a.len, b.len);
    var i: usize = 0;
    while (i < n) : (i += 1) if (a[i] != b[i]) return i;
    if (a.len != b.len) return n;
    return null;
}

/// One run, traces optional. The arena owns every buffer.
fn exec(comptime p: Profile, alloc: std.mem.Allocator, src: []const u8,
        budget: u64, want_trace: bool) !struct { out: Out, trace: std.ArrayList(core.TraceEvent) } {
    var vm = newVm(p, alloc);
    try vm.load(src);
    var trace: std.ArrayList(core.TraceEvent) = .empty;
    const res = if (want_trace)
        try vm.runWithTrace(budget, "", &trace)
    else
        try vm.run(budget, "");
    const bytes = try alloc.dupe(u8, res.stdout.items);
    return .{
        .out = .{
            .status = res.status,
            .steps = res.steps,
            .padwidth = vm.padwidth,
            .growth_events = vm.stats.growth_events,
            .final_c = res.final_c,
            .final_d = res.final_d,
            .max_addr = res.max_addr_touched,
            .cells = res.cells_materialized,
            .stdout = bytes,
        },
        .trace = trace,
    };
}

fn report(comptime name: []const u8, src: []const u8, o: Out) void {
    std.debug.print(
        "RUN prof={s} status={s} steps={d} padwidth={d} growth_events={d} final_c={d} " ++
            "final_d={d} max_addr={d} cells={d} stdout_len={d} stdout_sha={s} source_eq_stdout={}\n",
        .{ name, o.status, o.steps, o.padwidth, o.growth_events, o.final_c, o.final_d,
            o.max_addr, o.cells, o.stdout.len, shaHex(o.stdout),
            o.stdout.len == src.len and std.mem.eql(u8, o.stdout, src) },
    );
}

fn firstDiffStep(a: []const core.TraceEvent, b: []const core.TraceEvent,
                 comptime field: []const u8) ?u64 {
    const n = @min(a.len, b.len);
    var i: usize = 0;
    while (i < n) : (i += 1) {
        if (@field(a[i], field) != @field(b[i], field)) return a[i].step;
    }
    // Same prefix, different lengths: the shorter run stopped first.
    if (a.len != b.len) return n + 1;
    return null;
}

fn firstByteDiff(a: []const u8, b: []const u8) ?usize {
    const n = @min(a.len, b.len);
    var i: usize = 0;
    while (i < n) : (i += 1) if (a[i] != b[i]) return i;
    if (a.len != b.len) return n;
    return null;
}

pub fn main(init: std.process.Init) !void {
    const alloc = init.arena.allocator();
    var args = try std.process.Args.Iterator.initAllocator(init.minimal.args, alloc);
    _ = args.next();
    const program_path = args.next() orelse return error.MissingProgram;
    const trace_budget = try std.fmt.parseInt(u64, args.next() orelse return error.MissingBudget, 10);
    const stdout_budget = try std.fmt.parseInt(u64, args.next() orelse return error.MissingBudget, 10);

    const src = try std.Io.Dir.cwd().readFileAlloc(init.io, program_path, alloc, .unlimited);

    // ---- pre-execution images -----------------------------------------------
    const img_c = try imageProbe(.classic, alloc, src);
    const img_f = try imageProbe(.pure_fixed, alloc, src);
    const img_e = try imageProbe(.epochal, alloc, src);
    std.debug.print("IMAGE stored_sha classic={s} pure_fixed={s} epochal={s}\n",
        .{ img_c.stored_sha, img_f.stored_sha, img_e.stored_sha });
    std.debug.print("IMAGE addressed_sha classic={s} pure_fixed={s} epochal={s} program_len={d}\n",
        .{ img_c.addressed_sha, img_f.addressed_sha, img_e.addressed_sha, img_c.program_len });
    std.debug.print("IMAGE addressed_first_diff classic_vs_pure_fixed={?d} " ++
        "classic_vs_epochal={?d} pure_fixed_vs_epochal={?d}\n",
        .{ firstDiffIndex(img_c.values, img_f.values),
           firstDiffIndex(img_c.values, img_e.values),
           firstDiffIndex(img_f.values, img_e.values) });

    // ---- pass 1: per-step traces (each event is ~200 bytes, keep it bounded) --
    const c1 = try exec(.classic, alloc, src, trace_budget, true);
    const f1 = try exec(.pure_fixed, alloc, src, trace_budget, true);
    const e1 = try exec(.epochal, alloc, src, trace_budget, true);

    std.debug.print("PASS trace budget={d} src_bytes={d} src_sha={s}\n",
        .{ trace_budget, src.len, shaHex(src) });
    report("classic", src, c1.out);
    report("pure_fixed", src, f1.out);
    report("epochal", src, e1.out);
    inline for (.{ "op", "a_after", "c_after", "d_after", "cell_before" }) |f| {
        std.debug.print(
            "DIFF_TRACE field={s} classic_vs_epochal={?d} classic_vs_pure_fixed={?d} pure_fixed_vs_epochal={?d}\n",
            .{ f, firstDiffStep(c1.trace.items, e1.trace.items, f),
               firstDiffStep(c1.trace.items, f1.trace.items, f),
               firstDiffStep(f1.trace.items, e1.trace.items, f) });
    }
    std.debug.print("DIFF_TRACE field=stdout_prefix_len classic_vs_epochal={?d} classic_vs_pure_fixed={?d}\n",
        .{ firstByteDiff(c1.out.stdout, e1.out.stdout), firstByteDiff(c1.out.stdout, f1.out.stdout) });

    // ---- pass 2: stdout only, larger budget ---------------------------------
    if (stdout_budget != trace_budget) {
        const c2 = try exec(.classic, alloc, src, stdout_budget, false);
        const f2 = try exec(.pure_fixed, alloc, src, stdout_budget, false);
        const e2 = try exec(.epochal, alloc, src, stdout_budget, false);

        std.debug.print("PASS stdout budget={d}\n", .{stdout_budget});
        report("classic", src, c2.out);
        report("pure_fixed", src, f2.out);
        report("epochal", src, e2.out);
        std.debug.print(
            "DIFF_STDOUT first_byte classic_vs_epochal={?d} classic_vs_pure_fixed={?d} pure_fixed_vs_epochal={?d}\n",
            .{ firstByteDiff(c2.out.stdout, e2.out.stdout), firstByteDiff(c2.out.stdout, f2.out.stdout),
               firstByteDiff(f2.out.stdout, e2.out.stdout) });
        std.debug.print("WIDEN epochal_events_at_stdout_budget={d} final_padwidth={d}\n",
            .{ e2.out.growth_events, e2.out.padwidth });
    }
}
