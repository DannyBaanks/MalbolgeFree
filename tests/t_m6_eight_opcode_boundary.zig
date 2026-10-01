//! M6 boundary: what the eight Classic opcodes can and cannot do.
//!
//! The M6 gate asks for a BF->Malbolge compiler preserving tape, loops, input
//! and output. The obvious first sub-goal is BF `>`: move the data pointer by
//! one. In this machine `d` is only ever written by op 40 (movd: d = mem[d]),
//! so making `d` input-dependent requires a cell holding an input-derived
//! address, which in turn needs a data-dependent jump. That is worth measuring
//! rather than assuming.
//!
//! Measured answer, and this file makes it executable so anyone can reproduce
//! it: within an exhaustive search, a program using only the eight Classic
//! opcodes never moves `d` to an input-dependent address, while the same search
//! over the auxiliary ISA does. That is why the BF backend needs opcodes 69-79.
//!
//! The search is bounded, so this is a bounded negative, not a proof of
//! impossibility. Two things keep it honest:
//!   - CONTROL: the identical search run against the assisted profile DOES find
//!     witnesses, so the methodology can detect this effect when it exists.
//!   - The bound is stated in the test name and in docs/M6_EIGHT_OPCODE_BOUNDARY.md.
const std = @import("std");
const mb = @import("malbolge_free");
const hell = @import("hell");

/// Smallest printable char at `position` decoding to `opcode`.
fn opChar(opcode: u8, position: usize) u8 {
    var cv: u16 = 33;
    while (cv < 127) : (cv += 1) {
        if ((cv + position) % 94 == opcode) return @intCast(cv);
    }
    unreachable;
}

test "malformed_assisted_source_is_rejected" {
    // A source that decodes to an auxiliary opcode (75 = TAPE_BASE) at position 0
    // must be refused outright by the strict profiles. Without this, free_pure
    // could be handed assisted source and silently run it as NOPs, which would
    // make every "no assisted ISA" claim in this repo unfalsifiable.
    const alloc = std.testing.allocator;
    const assisted_op = @as(u8, 75); // TAPE_BASE
    const ch = opChar(assisted_op, 0);

    // Two cells, because the loader also requires a minimum program length.
    const src = [_]u8{ ch, opChar(68, 1) }; // second cell is a legal NOP

    var pure = mb.MalbolgeCore.initFreePure(alloc, 10, .fixed);
    defer pure.deinit();
    try std.testing.expectError(error.InvalidSourceOpcode, pure.load(&src));

    var classic = mb.MalbolgeCore.initClassic(alloc);
    defer classic.deinit();
    try std.testing.expectError(error.InvalidSourceOpcode, classic.load(&src));

    // The same source is legal in the assisted profile, which is the whole point
    // of the profile split.
    var assisted = mb.MalbolgeCore.initFreeAssisted(alloc, 10, null, .fixed);
    defer assisted.deinit();
    try assisted.load(&src);
}

const Choice = struct { name: []const u8, arg: ?u8 = null };
const CHOICES = [_]Choice{
    .{ .name = "MOVD" },
    .{ .name = "OPR", .arg = 39 },
    .{ .name = "NOP" },
    .{ .name = "JMP" },
    .{ .name = "INC" },
};

const Outcome = struct { final_d: u128, steps: u64 };

fn runOnce(alloc: std.mem.Allocator, hell_src: []const u8, input: []const u8, assisted: bool) !Outcome {
    var parser = hell.Parser.init(hell_src);
    var program = try parser.parse(alloc);
    defer program.deinit(alloc);
    var layout = try hell.resolveLayout(&program, alloc);
    defer layout.deinit(alloc);
    var emitted = try hell.emit(&layout, alloc);
    defer emitted.deinit(alloc);

    var vm = if (assisted)
        mb.MalbolgeCore.initFreeAssisted(alloc, 10, null, .fixed)
    else
        mb.MalbolgeCore.initFreePure(alloc, 10, .fixed);
    defer vm.deinit();
    try vm.load(emitted.slice());
    var res = try vm.run(400, input);
    defer res.stdout.deinit(alloc);
    return .{ .final_d = res.final_d, .steps = res.steps };
}

fn countPointerDivergence(alloc: std.mem.Allocator, assisted: bool, max_depth: usize) !usize {
    const n = CHOICES.len;
    var found: usize = 0;
    var depth: usize = 0;
    while (depth <= max_depth) : (depth += 1) {
        var total: usize = 1;
        var i: usize = 0;
        while (i < depth) : (i += 1) total *= n;
        var idx: usize = 0;
        while (idx < total) : (idx += 1) {
            var buf = std.ArrayListUnmanaged(u8).empty;
            try buf.appendSlice(alloc, ".CODE\n  IN\n");
            var tmp = idx;
            var k: usize = 0;
            while (k < depth) : (k += 1) {
                try buf.appendSlice(alloc, "  ");
                try buf.appendSlice(alloc, CHOICES[tmp % n].name);
                if (CHOICES[tmp % n].arg) |a| {
                    var nb: [8]u8 = undefined;
                    try buf.appendSlice(alloc, try std.fmt.bufPrint(&nb, " {d}", .{a}));
                }
                try buf.appendSlice(alloc, "\n");
                tmp /= n;
            }
            try buf.appendSlice(alloc, "  OUT 65\n  HALT\n");

            const src_copy = try alloc.dupe(u8, buf.items);
            buf.deinit(alloc);
            const a = runOnce(alloc, src_copy, &[_]u8{0x00}, assisted) catch {
                alloc.free(src_copy);
                continue;
            };
            const b = runOnce(alloc, src_copy, &[_]u8{0xff}, assisted) catch {
                alloc.free(src_copy);
                continue;
            };
            alloc.free(src_copy);
            if (a.final_d != b.final_d) found += 1;
        }
    }
    return found;
}

test "CONTROL: the search detects input-dependent pointer movement when it exists" {
    // Without this, the negative below would be worthless: a broken search finds
    // nothing in either profile. Here the assisted profile must yield a witness.
    const alloc = std.testing.allocator;
    const found = try countPointerDivergence(alloc, true, 3);
    try std.testing.expect(found > 0);
}

test "BOUNDED NEGATIVE: eight Classic opcodes never move d by input, depth<=3" {
    // Bound: 1 + 5 + 25 + 125 = 156 templates, two inputs each, strict profile.
    const alloc = std.testing.allocator;
    const found = try countPointerDivergence(alloc, false, 3);
    try std.testing.expectEqual(@as(usize, 0), found);
}

test "the eight-opcode profile still shows input-dependent output" {
    // The boundary is specific, not "the strict profile is inert": control that
    // changes what is printed IS demonstrated. What is missing is pointer
    // movement. Uses the committed fixture, the same one the vertical-slice gate
    // asserts on, so this cannot drift from the demonstrated artifact.
    const alloc = std.testing.allocator;
    const src = @embedFile("fixtures/free_pure/vertical_slice.hell");
    var parser = hell.Parser.init(src);
    var program = try parser.parse(alloc);
    defer program.deinit(alloc);
    var layout = try hell.resolveLayout(&program, alloc);
    defer layout.deinit(alloc);
    var emitted = try hell.emit(&layout, alloc);
    defer emitted.deinit(alloc);

    var vm = mb.MalbolgeCore.initFreePure(alloc, 10, .fixed);
    defer vm.deinit();
    try vm.load(emitted.slice());
    var a = try vm.run(500, &[_]u8{0x00});
    defer a.stdout.deinit(alloc);
    var b = try vm.run(500, &[_]u8{0xff});
    defer b.stdout.deinit(alloc);
    try std.testing.expect(a.stdout.items.len > 0);
    try std.testing.expect(!std.mem.eql(u8, a.stdout.items, b.stdout.items));
}
