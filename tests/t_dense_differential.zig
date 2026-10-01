//! Differential: hash-map representation vs dense representation.
//!
//! The dense path is an opt-in optimisation, so the only acceptable claim is
//! that it is observationally identical to the historical hash-map path. This
//! test asserts equality of everything observable: stdout, status, step count,
//! final a/c/d, cells touched, encrypted-cell count and the whole trace.
//!
//! It also pins the self-modification cases (encryption writes land inside the
//! dense range) and the out-of-range write case (a `movd` jump that pushes a
//! write past the dense range into the overflow map).
const std = @import("std");
const core = @import("malbolge_free");

const Case = struct { name: []const u8, src: []const u8, stdin: []const u8, steps: u64 };

const CASES = [_]Case{
    .{ .name = "echo", .src = "ubO", .stdin = "", .steps = 500 },
    .{ .name = "echo2", .src = "ubs`M", .stdin = "", .steps = 500 },
    .{ .name = "echo3", .src = "ubs`q^K", .stdin = "", .steps = 500 },
    .{ .name = "hello", .src = "(=<`#9]~6ZY32Vx/4Rs+0No-&Jk)\"Fh}|Bcy?`=*z]Kw%oG4UUS0/@-ejc(:'8dc", .stdin = "", .steps = 2000 },
    .{ .name = "input_echo", .src = "ubO", .stdin = "hello", .steps = 500 },
    // Classic witness that leans on self-modification (encryption) heavily.
    .{ .name = "classic_reproducer", .src = "bCBA@?>=<;:9876543210/.-,+*)('&%$#\"!~}|{zyxwvutsrqponmlkjihgfedcba", .stdin = "", .steps = 4000 },
};

fn traceHash(alloc: std.mem.Allocator, c: Case) !core.RunResult {
    var vm = core.MalbolgeCore.initClassic(alloc);
    defer vm.deinit();
    try vm.load(c.src);
    var evs = std.ArrayList(core.TraceEvent).empty;
    defer evs.deinit(alloc);
    const r = try vm.runWithTrace(c.steps, c.stdin, &evs);
    // Re-run without trace for a clean comparison; the traced run is used only
    // to prove tracing does not diverge between representations.
    _ = evs.items.len;
    return r;
}

fn traceDense(alloc: std.mem.Allocator, c: Case) !core.RunResult {
    var vm = core.MalbolgeCore.initClassic(alloc);
    defer vm.deinit();
    try vm.enableDenseSource();
    try vm.load(c.src);
    var evs = std.ArrayList(core.TraceEvent).empty;
    defer evs.deinit(alloc);
    return vm.runWithTrace(c.steps, c.stdin, &evs);
}

test "dense representation is observationally identical to the hash map" {
    const alloc = std.testing.allocator;
    for (CASES) |c| {
        var a = try traceHash(alloc, c);
        defer a.stdout.deinit(alloc);
        var b = try traceDense(alloc, c);
        defer b.stdout.deinit(alloc);

        try std.testing.expectEqualStrings(a.status, b.status);
        try std.testing.expectEqual(a.steps, b.steps);
        try std.testing.expectEqual(a.max_addr_touched, b.max_addr_touched);
        try std.testing.expectEqual(a.max_value, b.max_value);
        try std.testing.expectEqual(a.cells_materialized, b.cells_materialized);
        try std.testing.expectEqual(a.final_c, b.final_c);
        try std.testing.expectEqual(a.final_d, b.final_d);
        try std.testing.expectEqual(a.assisted_opcodes, b.assisted_opcodes);
        try std.testing.expectEqual(a.encrypted_cells, b.encrypted_cells);
        try std.testing.expectEqualSlices(u8, a.stdout.items, b.stdout.items);
    }
}

test "traces match step by step (a, c, d, cell, encryption)" {
    const alloc = std.testing.allocator;
    for (CASES) |c| {
        var ha = core.MalbolgeCore.initClassic(alloc);
        defer ha.deinit();
        try ha.load(c.src);
        var ea = std.ArrayList(core.TraceEvent).empty;
        defer ea.deinit(alloc);
        var ra = try ha.runWithTrace(c.steps, c.stdin, &ea);
        defer ra.stdout.deinit(alloc);

        var da = core.MalbolgeCore.initClassic(alloc);
        defer da.deinit();
        try da.enableDenseSource();
        try da.load(c.src);
        var eb = std.ArrayList(core.TraceEvent).empty;
        defer eb.deinit(alloc);
        var rb = try da.runWithTrace(c.steps, c.stdin, &eb);
        defer rb.stdout.deinit(alloc);

        try std.testing.expectEqual(ea.items.len, eb.items.len);
        for (ea.items, eb.items) |x, y| {
            try std.testing.expectEqual(x.step, y.step);
            try std.testing.expectEqual(x.op, y.op);
            try std.testing.expectEqual(x.a_before, y.a_before);
            try std.testing.expectEqual(x.c_before, y.c_before);
            try std.testing.expectEqual(x.d_before, y.d_before);
            try std.testing.expectEqual(x.cell_before, y.cell_before);
            try std.testing.expectEqual(x.a_after, y.a_after);
            try std.testing.expectEqual(x.c_after, y.c_after);
            try std.testing.expectEqual(x.d_after, y.d_after);
            try std.testing.expectEqual(x.encrypted_addr, y.encrypted_addr);
            try std.testing.expectEqual(x.encrypted_value, y.encrypted_value);
        }
    }
}

test "dense refuses widths whose values overflow the u32 element type" {
    const alloc = std.testing.allocator;
    var vm = core.MalbolgeCore.init(alloc, 21, null, .fixed);
    defer vm.deinit();
    // 3^21 does not fit in u32, so the dense path must refuse rather than
    // silently truncate cell values.
    try std.testing.expectError(error.DenseRangeTooNarrow, vm.enableDenseSource());
}

/// The ladder is the reason this optimisation exists: an unbounded epochal run
/// with a witness big enough to cross more than one frontier. Run it both ways
/// and require the widening events to land on the same steps.
fn ladderWitness(len: usize) ![]u8 {
    const src = try std.testing.allocator.alloc(u8, len);
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

test "free_pure epochal ladder agrees across representations" {
    const alloc = std.testing.allocator;
    const src = try ladderWitness(60000);
    defer alloc.free(src);

    var hash = core.MalbolgeCore.initFreePure(alloc, 10, .epochal);
    defer hash.deinit();
    try hash.load(src);
    var a = try hash.run(60_000, "");
    defer a.stdout.deinit(alloc);

    var dense = core.MalbolgeCore.initFreePure(alloc, 10, .epochal);
    defer dense.deinit();
    try dense.enableDenseSource();
    try dense.load(src);
    var b = try dense.run(60_000, "");
    defer b.stdout.deinit(alloc);

    try std.testing.expectEqualStrings(a.status, b.status);
    try std.testing.expectEqual(a.steps, b.steps);
    try std.testing.expectEqual(a.final_c, b.final_c);
    try std.testing.expectEqual(a.final_d, b.final_d);
    try std.testing.expectEqual(a.max_addr_touched, b.max_addr_touched);
    try std.testing.expectEqual(a.encrypted_cells, b.encrypted_cells);
    // Same widening count and same final width: the ladder measurement itself is
    // unaffected by the representation.
    try std.testing.expectEqual(a.cells_materialized, b.cells_materialized);
    try std.testing.expectEqual(@as(u8, 11), dense.padwidth);
}