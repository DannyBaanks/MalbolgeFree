//! M0 closure: EOF trace cases and numeric-precision boundaries.
//!
//! docs/SPEC_V1.md §6 left EOF half-open ("faltan casos adicionales de traza
//! para M2") and §3/§8 left "decisiones de precision numerica" unchecked. This
//! file pins both with executed cases instead of prose.
//!
//! Two precision hazards are pinned AS CURRENT BEHAVIOUR rather than silently
//! fixed, because changing them would alter the public contract:
//!   1. pow3(n) for n >= 81 returns u128 max instead of failing, so a caller can
//!      silently receive a plausible-looking wrong modulus.
//!   2. The 1 <= width <= 80 guard is a std.debug.assert, which ReleaseFast
//!      compiles out.
//! Both are recorded in SPEC_V1 as accepted limitations.
const std = @import("std");
const core = @import("malbolge_free");

/// Smallest printable source char at `position` that decodes to `opcode`.
/// Same rule as the loader: (char + position) % 94 == opcode.
fn opChar(opcode: u8, position: usize) u8 {
    var cv: u16 = 33;
    while (cv < 127) : (cv += 1) {
        if ((cv + position) % 94 == opcode) return @intCast(cv);
    }
    unreachable;
}

fn source(alloc: std.mem.Allocator, ops: []const u8) ![]u8 {
    const out = try alloc.alloc(u8, ops.len);
    for (ops, 0..) |op, i| out[i] = opChar(op, i);
    return out;
}

const IN: u8 = 23;
const OUT: u8 = 5;
const CRAZY: u8 = 62;
const ROT: u8 = 39;
const NOP: u8 = 68;
const HALT: u8 = 81;

fn runClassic(alloc: std.mem.Allocator, ops: []const u8, stdin: []const u8) !core.RunResult {
    const src = try source(alloc, ops);
    defer alloc.free(src);
    var vm = core.MalbolgeCore.initClassic(alloc);
    defer vm.deinit();
    try vm.load(src);
    return vm.run(1000, stdin);
}

fn runTraced(alloc: std.mem.Allocator, ops: []const u8, stdin: []const u8, trace: *std.ArrayList(core.TraceEvent)) !core.RunResult {
    const src = try source(alloc, ops);
    defer alloc.free(src);
    var vm = core.MalbolgeCore.initClassic(alloc);
    defer vm.deinit();
    try vm.load(src);
    return vm.runWithTrace(1000, stdin, trace);
}

/// Canonical EOF value for Classic: Olmstead's 1998 `malbolge.c` assigns
/// `a = 59048` and Iizawa's `fast20.c` assigns `a = END-1`. Both are the
/// all-twos value 3^w-1 of the machine width, never a negative sentinel.
/// Verified 2026-10-17 against `reference_interpreter_classic` (emits 0xa8)
/// and `ISyCo Git/MALBOLGE/malbolge.py` (emits 0xa8) on `in,out,hlt` with an
/// empty stdin; this core used to emit 0xff there.
const CLASSIC_EOF: u128 = 59048; // == 3^10 - 1

test "EOF then out emits the canonical 3^10-1 byte and halts" {
    const alloc = std.testing.allocator;
    var res = try runClassic(alloc, &[_]u8{ IN, OUT, HALT }, "");
    defer res.stdout.deinit(alloc);

    try std.testing.expectEqualStrings("HALTED", res.status);
    try std.testing.expectEqual(@as(usize, 1), res.stdout.items.len);
    try std.testing.expectEqual(core.pow3(10) - 1, CLASSIC_EOF);
    try std.testing.expectEqual(@as(u8, @intCast(CLASSIC_EOF % 256)), res.stdout.items[0]);
    try std.testing.expectEqual(@as(u8, 0xa8), res.stdout.items[0]);
}

test "EOF is sticky: every further in reports the same all-twos value" {
    const alloc = std.testing.allocator;
    var res = try runClassic(alloc, &[_]u8{ IN, OUT, IN, OUT, IN, OUT, HALT }, "");
    defer res.stdout.deinit(alloc);

    try std.testing.expectEqualStrings("HALTED", res.status);
    try std.testing.expectEqual(@as(usize, 3), res.stdout.items.len);
    for (res.stdout.items) |b| try std.testing.expectEqual(@as(u8, 0xa8), b);
}

test "a real byte is not EOF: the same program distinguishes them" {
    const alloc = std.testing.allocator;
    var eof = try runClassic(alloc, &[_]u8{ IN, OUT, HALT }, "");
    defer eof.stdout.deinit(alloc);
    var fed = try runClassic(alloc, &[_]u8{ IN, OUT, HALT }, "A");
    defer fed.stdout.deinit(alloc);

    try std.testing.expectEqual(@as(u8, 0xa8), eof.stdout.items[0]);
    try std.testing.expectEqual(@as(u8, 'A'), fed.stdout.items[0]);
}

test "EOF is the all-twos value, and crazy consumes it as an ordinary operand" {
    const alloc = std.testing.allocator;
    // c and d advance together from 0, so at the crazy step (c == d == 2) the
    // cell read is still the pristine source char at position 2. That makes the
    // expected value computable instead of a magic constant.
    const ops = [_]u8{ IN, NOP, CRAZY, OUT, HALT };
    var res = try runClassic(alloc, &ops, "");
    defer res.stdout.deinit(alloc);

    const w: u8 = 10;
    const modulus_minus_one = core.pow3(w) - 1; // what `in` assigns at EOF
    const mem_at_d = opChar(CRAZY, 2);          // d == c == 2 at that step
    const expected_a = core.crazy(modulus_minus_one, mem_at_d, w);
    try std.testing.expectEqualStrings("HALTED", res.status);
    try std.testing.expectEqual(@as(u8, @intCast(expected_a % 256)), res.stdout.items[0]);
}

test "EOF is visible in the trace as 3^w-1 right after in" {
    const alloc = std.testing.allocator;
    var trace = std.ArrayList(core.TraceEvent).empty;
    defer trace.deinit(alloc);
    var res = try runTraced(alloc, &[_]u8{ IN, OUT, HALT }, "", &trace);
    defer res.stdout.deinit(alloc);

    // step 1 is the in; its a_after must be the canonical all-twos value, and
    // a_before zero.
    try std.testing.expectEqual(@as(usize, 3), trace.items.len);
    try std.testing.expectEqual(@as(u128, 0), trace.items[0].a_before);
    try std.testing.expectEqual(CLASSIC_EOF, trace.items[0].a_after);
}

test "EOF follows the machine width, not a Classic constant" {
    const alloc = std.testing.allocator;
    // free_pure at fixed k=19 is the width Unshackled addresses. Its EOF must
    // be 3^19-1, which is what `fast20.c` (`a = END-1`) produces: measured on
    // this machine that reference prints 0xda, where the old sentinel printed
    // 0xff.
    var vm = core.MalbolgeCore.initFreePure(alloc, 19, .fixed);
    defer vm.deinit();
    const ops = try source(alloc, &[_]u8{ IN, OUT, HALT });
    defer alloc.free(ops);
    try vm.load(ops);
    var res = try vm.run(1000, "");
    defer res.stdout.deinit(alloc);

    try std.testing.expectEqualStrings("HALTED", res.status);
    try std.testing.expectEqual(@as(u8, @intCast((core.pow3(19) - 1) % 256)), res.stdout.items[0]);
    try std.testing.expectEqual(@as(u8, 0xda), res.stdout.items[0]);
}

test "rot after EOF ignores the accumulator, so it is not an EOF path" {
    const alloc = std.testing.allocator;
    // rot reads mem[d], never the accumulator: pins that EOF does not leak into
    // rotate. Same trace as a run fed a real byte, because a is unused.
    var eof = try runClassic(alloc, &[_]u8{ IN, ROT, OUT, HALT }, "");
    defer eof.stdout.deinit(alloc);
    var fed = try runClassic(alloc, &[_]u8{ IN, ROT, OUT, HALT }, "A");
    defer fed.stdout.deinit(alloc);
    try std.testing.expectEqualSlices(u8, eof.stdout.items, fed.stdout.items);
}

// ── numeric precision ────────────────────────────────────────────────────────

/// Reference exponentiation by repeated multiplication. Avoids hand-counted
/// literals: an earlier version of this file asserted 3^20 against a
/// twenty-term product that was really 3^19, which is exactly the kind of
/// transcription error these tests exist to catch.
fn pow3Ref(n: u8) u128 {
    var acc: u128 = 1;
    var i: u8 = 0;
    while (i < n) : (i += 1) acc *= 3;
    return acc;
}

test "pow3 is exact across the supported domain" {
    for ([_]u8{ 0, 1, 2, 10, 19, 20, 26, 40, 79, 80 }) |w| {
        try std.testing.expectEqual(pow3Ref(w), core.pow3(w));
    }
    // Spot values that other documents quote, recomputed rather than trusted.
    try std.testing.expectEqual(@as(u128, 59049), core.pow3(10)); // Classic 3^10
    try std.testing.expectEqual(@as(u128, 1162261467), core.pow3(19)); // 3^19
    try std.testing.expectEqual(@as(u128, 3486784401), core.pow3(20)); // 3^20, last dense-safe
}

test "HAZARD PINNED: pow3 saturates silently past the u128 domain" {
    // Not fixed: changing it would alter the public signature. Pinned so nobody
    // discovers it by accident. pow3(81) is outside the defined domain.
    try std.testing.expectEqual(std.math.maxInt(u128), core.pow3(81));
    try std.testing.expectEqual(std.math.maxInt(u128), core.pow3(200));
}

test "width 80 is accepted and exact; the guard above it is a debug assert" {
    // The 1 <= width <= 80 guard in init() is a std.debug.assert, which
    // ReleaseFast compiles out, so an out-of-domain width cannot be tested by
    // expecting a crash here. What IS testable is the accepted upper bound and
    // its exact modulus. The assert-only guard is recorded in SPEC_V1 as an
    // accepted limitation, together with the pow3 saturation above.
    const alloc = std.testing.allocator;
    var vm = core.MalbolgeCore.init(alloc, 80, core.pow3(80), .fixed);
    defer vm.deinit();
    try std.testing.expectEqual(@as(u8, 80), vm.width);
    var acc: u128 = 1;
    for (0..80) |_| acc *= 3;
    try std.testing.expectEqual(acc, vm.mem_limit.?);
}

test "dense refuses every width the u32 element type cannot represent" {
    const alloc = std.testing.allocator;
    // 3^20 = 3486784401 fits in u32; 3^21 = 10460353203 does not.
    try std.testing.expect(core.pow3(20) <= std.math.maxInt(u32));
    try std.testing.expect(core.pow3(21) > std.math.maxInt(u32));

    for ([_]u8{ 21, 26, 40, 80 }) |w| {
        var vm = core.MalbolgeCore.init(alloc, w, null, .fixed);
        defer vm.deinit();
        try std.testing.expectError(error.DenseRangeTooNarrow, vm.enableDenseSource());
    }
    // ...and accepts the boundary width.
    var ok = core.MalbolgeCore.init(alloc, 20, null, .fixed);
    defer ok.deinit();
    try ok.enableDenseSource();
}

const builtin = @import("builtin");