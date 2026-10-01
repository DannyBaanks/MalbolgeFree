//! M7: the compiler's silent-corruption path, and the decoder crash it hid.
//!
//! Finding this required feeding the m7 compiler's output for a *bracketed*
//! program into the image decoder. What happened is the point of this file:
//!
//!   1. `m7/compiler.bf` does not resolve brackets. It classifies `[` and `]` to
//!      opcodes 7 and 8, counts them, and emits records with `has_target = 0`.
//!      For `++++++[>++++++<-]>.` the resulting image has the right header, the
//!      right length and the right instruction count (19) -- and the WRONG
//!      bytes. Structurally plausible, semantically wrong.
//!   2. That image reached `bf_ir_image.decode`, which rejected it via
//!      `validate` -- and crashed with a double free on the way out, because
//!      `decode` had registered `errdefer code.deinit()` AND
//!      `errdefer program.deinit()` for the same buffer. A malformed image
//!      should report a malformed image, not take the process down.
//!
//! The compiler is NOT fixed here (resolving brackets needs scratch the tape
//! does not have; see docs/M7_TAPE_CAPACITY.md). What is fixed is the crash, and
//! what is added is a guard so the silent-corruption path can never look healthy
//! again by accident.
const std = @import("std");
const translator = @import("bf_to_ir.zig");
const image = @import("bf_ir_image.zig");

/// Output of `m7/compiler.bf` for the input `++++++[>++++++<-]>.`.
/// Regenerate with tests/t_m7_uroboros_seed.zig's tooling; kept as a fixture so
/// this regression guard does not depend on running the BF compiler in CI.
const bracketed_image = @embedFile("fixtures/m7/bracketed_probe.bin");

test "a malformed image is rejected, not crashed on" {
    // The regression this file exists for: before the fix this call SEGVFAULTED
    // inside Allocator.free via the errdefer double free.
    const alloc = std.testing.allocator;
    try std.testing.expectError(error.MissingJumpTarget, image.decode(bracketed_image, alloc));
}

test "the compiler's bracketed output is plausible but wrong, which is the trap" {
    // Pin WHY the decoder must reject it: the header, the length and the count
    // are all self-consistent. Only the missing jump targets give it away, so a
    // consumer that trusts the header would happily execute garbage.
    try std.testing.expectEqualStrings("BFIR1", bracketed_image[0..5]);
    const count = std.mem.readInt(u32, bracketed_image[5..9], .little);
    try std.testing.expectEqual(@as(usize, 19), count);
    try std.testing.expectEqual(9 + count * 12, bracketed_image.len);

    // Every bracket record carries has_target = 0, which is what validate rejects.
    var brackets: usize = 0;
    var offset: usize = 9;
    while (offset < bracketed_image.len) : (offset += 12) {
        const op = bracketed_image[offset];
        if (op == 7 or op == 8) {
            brackets += 1;
            try std.testing.expectEqual(@as(u8, 0), bracketed_image[offset + 1]);
        }
    }
    try std.testing.expectEqual(@as(usize, 2), brackets);
}

test "decode still accepts a well-formed image and frees exactly once" {
    // Non-regression: the happy path and the other error paths must be intact
    // after moving cleanup into `fill`.
    const alloc = std.testing.allocator;
    var program = try translator.compile("+[.-]", alloc);
    defer program.deinit();
    const encoded = try image.encode(&program, alloc);
    defer alloc.free(encoded);

    var decoded = try image.decode(encoded, alloc);
    defer decoded.deinit();
    try std.testing.expectEqual(program.code.items.len, decoded.code.items.len);

    // InvalidHeader and InvalidLength are decided before any allocation.
    var bad_header = try alloc.dupe(u8, encoded);
    defer alloc.free(bad_header);
    bad_header[0] = 'X';
    try std.testing.expectError(error.InvalidHeader, image.decode(bad_header, alloc));

    const truncated = try alloc.dupe(u8, encoded[0 .. encoded.len - 3]);
    defer alloc.free(truncated);
    try std.testing.expectError(error.InvalidLength, image.decode(truncated, alloc));

    // InvalidFlags is decided inside the fill phase.
    var bad_flags = try alloc.dupe(u8, encoded);
    defer alloc.free(bad_flags);
    bad_flags[10] = 7;
    try std.testing.expectError(error.InvalidFlags, image.decode(bad_flags, alloc));
}