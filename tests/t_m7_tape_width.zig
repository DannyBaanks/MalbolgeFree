//! The BF data tape is a contract decision, not a law of the machine.
//!
//! 256 used to be a bare literal in the core, duplicated across the backend
//! contract and three M6 differential tests. It is now `DEFAULT_TAPE_SIZE`, and
//! the size is configurable per machine. These tests pin:
//!   - the default is unchanged, so recorded M6 evidence stays comparable;
//!   - a wider tape actually works end to end (zeroed, addressable, and it does
//!     not collide with the program cells or the frontier);
//!   - the size is validated;
//!   - widening changes capacity, NOT semantics: the same program on the same
//!     first 256 cells behaves identically.
const std = @import("std");
const mb = @import("malbolge_free");
const hell = @import("hell");

test "default tape size is unchanged at 256" {
    const alloc = std.testing.allocator;
    var vm = mb.MalbolgeCore.initFreeAssisted(alloc, 10, null, .fixed);
    defer vm.deinit();
    try std.testing.expectEqual(mb.DEFAULT_TAPE_SIZE, vm.tape_size);
    try std.testing.expectEqual(@as(u128, 256), mb.DEFAULT_TAPE_SIZE);
    try std.testing.expectEqual(@as(u128, 1000), mb.TAPE_BASE);
}

test "tape size is validated" {
    const alloc = std.testing.allocator;
    var vm = mb.MalbolgeCore.initFreeAssisted(alloc, 10, null, .fixed);
    defer vm.deinit();
    try std.testing.expectError(error.InvalidTapeSize, vm.setTapeSize(0));
    try std.testing.expectError(error.InvalidTapeSize, vm.setTapeSize(std.math.maxInt(u128)));
    try vm.setTapeSize(2048);
    try std.testing.expectEqual(@as(u128, 2048), vm.tape_size);
}

test "a wider tape is zeroed across its whole length" {
    const alloc = std.testing.allocator;
    var vm = mb.MalbolgeCore.initFreeAssisted(alloc, 10, null, .fixed);
    defer vm.deinit();
    try vm.setTapeSize(2048);
    // Minimal program whose only job is to arm the tape.
    try vm.load("D*"); // NOP, TAPE_BASE, HALT
    var res = try vm.run(200, "");
    defer res.stdout.deinit(alloc);
    try std.testing.expectEqualStrings("HALTED", res.status);

    // Every cell of the widened tape is readable and zero.
    var i: u128 = 0;
    while (i < vm.tape_size) : (i += 1) {
        try std.testing.expectEqual(@as(u128, 0), try vm.cell(mb.TAPE_BASE + i));
    }
    // Just past the widened end there is no longer tape: reading it returns the
    // lazy crazy fill, not a zero, which is exactly why the size is a contract.
    const beyond = try vm.cell(mb.TAPE_BASE + vm.tape_size);
    try std.testing.expect(beyond != 0);
}

test "widening does not change behaviour inside the first 256 cells" {
    // The differential that matters: identical program, identical input, and the
    // observable prefix of the tape must agree between the default and a wide
    // machine. Widening is capacity, not a semantic change.
    const alloc = std.testing.allocator;
    const src =
        \\.CODE
        \\  TAPE_BASE
        \\  INC
        \\  STORE
        \\  INC
        \\  STORE
        \\  OUT 65
        \\  HALT
    ;

    const Snapshot = struct {
        out: []u8,
        first256: [256]u128,
        steps: u64,
    };
    const runWith = struct {
        fn f(allocator: std.mem.Allocator, wide: bool) !Snapshot {
            var parser = hell.Parser.init(src);
            var program = try parser.parse(allocator);
            defer program.deinit(allocator);
            var layout = try hell.resolveLayout(&program, allocator);
            defer layout.deinit(allocator);
            var emitted = try hell.emit(&layout, allocator);
            defer emitted.deinit(allocator);

            var vm = mb.MalbolgeCore.initFreeAssisted(allocator, 10, null, .fixed);
            defer vm.deinit();
            if (wide) try vm.setTapeSize(2048);
            try vm.load(emitted.slice());
            var res = try vm.run(400, "");
            defer res.stdout.deinit(allocator);

            var snap = Snapshot{
                .out = try allocator.dupe(u8, res.stdout.items),
                .first256 = undefined,
                .steps = res.steps,
            };
            var i: usize = 0;
            while (i < 256) : (i += 1) {
                snap.first256[i] = try vm.cell(mb.TAPE_BASE + i);
            }
            return snap;
        }
    }.f;

    var narrow = try runWith(alloc, false);
    defer alloc.free(narrow.out);
    var wide = try runWith(alloc, true);
    defer alloc.free(wide.out);

    try std.testing.expectEqualSlices(u8, narrow.out, wide.out);
    try std.testing.expectEqual(narrow.steps, wide.steps);
    try std.testing.expectEqualSlices(u128, &narrow.first256, &wide.first256);
}