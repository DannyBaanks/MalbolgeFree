//! Free-pure vertical slice: nontrivial computation using only the eight Classic
//! opcodes, with automodification active and no auxiliary ISA.
//!
//! This is the M4 gate of ROADMAP_MALBOLGE_VERDADERO: until now the only
//! demonstrated backend was `free-assisted` (opcodes 69-79 plus
//! `lock_noencrypt`), which is a different machine. Everything below runs in
//! `free_pure`, where 69-79 are runtime NOPs and encryption stays on.
//!
//! The fixture was found by exhaustive deterministic enumeration, not by hand.
//! Acceptance criteria, each asserted explicitly:
//!   1. input is actually read          (op 23 in the trace)
//!   2. a ternary mutation happens      (op 62 or 39 in the trace)
//!   3. output happens                  (op 5 in the trace)
//!   4. the output depends on the input (distinct stdout for two inputs)
//!   5. assisted_opcode_count == 0      (no 69-79 executed)
//!   6. lock_noencrypt == false         (automodification stayed enabled)
//!   7. encrypted_cells > 0             (self-modification really occurred)
//!   8. free_pure before any frontier is identical to Classic
//!   9. a frontier is crossed without the auxiliary ISA
const std = @import("std");
const mb = @import("malbolge_free");
const hell = @import("hell");

const FIXTURE = @embedFile("fixtures/free_pure/vertical_slice.hell");

const Slice = struct {
    status: []const u8,
    steps: u64,
    out: []u8,
    assisted: u32,
    encrypted: u32,
    padwidth: u8,
    lock_noencrypt: bool,
    ops: std.AutoHashMap(u8, u32),
};

fn emitFixture(alloc: std.mem.Allocator) ![]u8 {
    var parser = hell.Parser.init(FIXTURE);
    var program = try parser.parse(alloc);
    defer program.deinit(alloc);
    var layout = try hell.resolveLayout(&program, alloc);
    defer layout.deinit(alloc);
    var emitted = try hell.emit(&layout, alloc);
    defer emitted.deinit(alloc);
    return alloc.dupe(u8, emitted.slice());
}

fn runSlice(alloc: std.mem.Allocator, src: []const u8, input: []const u8) !Slice {
    var vm = mb.MalbolgeCore.initFreePure(alloc, 10, .fixed);
    defer vm.deinit();
    try vm.load(src);
    var trace = std.ArrayList(mb.TraceEvent).empty;
    defer trace.deinit(alloc);
    var res = try vm.runWithTrace(500, input, &trace);
    defer res.stdout.deinit(alloc);

    var ops = std.AutoHashMap(u8, u32).init(alloc);
    for (trace.items) |e| {
        const gop = try ops.getOrPut(@intCast(e.op));
        if (!gop.found_existing) gop.value_ptr.* = 0;
        gop.value_ptr.* += 1;
    }
    return .{
        .status = res.status,
        .steps = res.steps,
        .out = try alloc.dupe(u8, res.stdout.items),
        .assisted = res.assisted_opcodes,
        .encrypted = res.encrypted_cells,
        .padwidth = vm.padwidth,
        .lock_noencrypt = vm.lock_noencrypt,
        .ops = ops,
    };
}

fn freeSlice(s: *Slice, alloc: std.mem.Allocator) void {
    alloc.free(s.out);
    s.ops.deinit();
}

test "free-pure vertical slice: state-dependent output with only Classic opcodes" {
    const alloc = std.testing.allocator;
    const src = try emitFixture(alloc);
    defer alloc.free(src);

    // Two different inputs must produce different observable output.
    var a = try runSlice(alloc, src, &[_]u8{0x00});
    defer freeSlice(&a, alloc);
    var b = try runSlice(alloc, src, &[_]u8{0xff});
    defer freeSlice(&b, alloc);

    // 1-3: the program really does input -> mutate -> output.
    for ([_]Slice{ a, b }) |s| {
        try std.testing.expect(s.ops.get(23) != null); // in
        try std.testing.expect(s.ops.get(62) != null or s.ops.get(39) != null); // crazy or rot
        try std.testing.expect(s.ops.get(5) != null); // out
        try std.testing.expectEqualStrings("HALTED", s.status);
    }
    // 4: the control flow is input-dependent, observable in stdout.
    try std.testing.expect(!std.mem.eql(u8, a.out, b.out));
    try std.testing.expect(a.out.len > 0 and b.out.len > 0);

    // 5-7: no auxiliary ISA, automodification on, and it really self-modified.
    for ([_]Slice{ a, b }) |s| {
        try std.testing.expectEqual(@as(u32, 0), s.assisted);
        try std.testing.expect(!s.lock_noencrypt);
        try std.testing.expect(s.encrypted > 0);
    }

    // Determinism: the same input twice must agree byte for byte.
    var again = try runSlice(alloc, src, &[_]u8{0xff});
    defer freeSlice(&again, alloc);
    try std.testing.expectEqualSlices(u8, b.out, again.out);
    try std.testing.expectEqual(b.steps, again.steps);
}

test "free_pure before any frontier is identical to Classic" {
    const alloc = std.testing.allocator;
    const src = try emitFixture(alloc);
    defer alloc.free(src);

    var pure = mb.MalbolgeCore.initFreePure(alloc, 10, .fixed);
    defer pure.deinit();
    try pure.load(src);
    var tp = std.ArrayList(mb.TraceEvent).empty;
    defer tp.deinit(alloc);
    var rp = try pure.runWithTrace(500, &[_]u8{0x41}, &tp);
    defer rp.stdout.deinit(alloc);

    var classic = mb.MalbolgeCore.initClassic(alloc);
    defer classic.deinit();
    try classic.load(src);
    var tc = std.ArrayList(mb.TraceEvent).empty;
    defer tc.deinit(alloc);
    var rc = try classic.runWithTrace(500, &[_]u8{0x41}, &tc);
    defer rc.stdout.deinit(alloc);

    // No widening can happen in 155 steps at w=10 (frontier is 3^10), so the two
    // profiles must be the same machine here.
    try std.testing.expectEqual(rp.steps, rc.steps);
    try std.testing.expectEqualSlices(u8, rp.stdout.items, rc.stdout.items);
    try std.testing.expectEqual(tp.items.len, tc.items.len);
    for (tp.items, tc.items) |x, y| {
        try std.testing.expectEqual(x.step, y.step);
        try std.testing.expectEqual(x.op, y.op);
        try std.testing.expectEqual(x.a_after, y.a_after);
        try std.testing.expectEqual(x.c_after, y.c_after);
        try std.testing.expectEqual(x.d_after, y.d_after);
    }
}

test "a frontier is crossed with no auxiliary ISA" {
    const alloc = std.testing.allocator;
    // Same witness shape as the ladder: only in/out/crazy/nop, so c walks
    // linearly past 3^10 and the epochal trigger fires once.
    const len: usize = 60000;
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

    var vm = mb.MalbolgeCore.initFreePure(alloc, 10, .epochal);
    defer vm.deinit();
    try vm.load(src);
    var res = try vm.run(60000, "");
    defer res.stdout.deinit(alloc);

    try std.testing.expectEqual(@as(u8, 11), vm.padwidth); // crossed 10 -> 11
    try std.testing.expectEqual(@as(u32, 1), vm.stats.growth_events);
    try std.testing.expectEqual(@as(u32, 0), res.assisted_opcodes); // still pure
    try std.testing.expect(!vm.lock_noencrypt);
    try std.testing.expect(res.encrypted_cells > 0);
}