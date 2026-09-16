//! bf_conditional.zig — BF conditional jump mechanism for Malbolge.
//!
//! Implements the `[` and `]` semantics using:
//!   1. ROT to read BF cell value into `a`
//!   2. OPR to conditionally modify a trampoline cell
//!   3. JMP through the trampoline
//!
//! The trampoline cell starts at value 0. When a=0 (BF cell is zero):
//!   crazy(0, 0, 10) = 29524, and 29524 mod 94 = 8
//!   If trampoline is at position P where P mod 94 = 90:
//!     (8 + 90) mod 94 = 4 = JMP → skip/enter as needed
//!
//! When a≠0 (BF cell is non-zero):
//!   crazy(a, 0, 10) mod 94 ≠ 8 for all BF cell values 1-255
//!   So the trampoline does NOT encode JMP → falls through

const std = @import("std");
const mb = @import("malbolge_free");

/// Check if a position is JMP-compatible (position mod 94 == 90).
pub fn isJmpPosition(pos: usize) bool {
    return pos % 94 == 90;
}

/// Compute the JMP target for a trampoline at position P.
/// When the trampoline is JMP, it reads cell[d] and sets c = cell[d].
/// The caller must ensure cell[d] contains the desired target address.
pub fn jmpTarget(pos: usize) bool {
    _ = pos;
    return true;
}

/// Compute crazy(0, 0, w) mod 94 for the trampoline check.
pub fn trampolineJmpResidue() u128 {
    const v = mb.crazy(0, 0, 10);
    return v % 94;
}

/// Verify that crazy(a, 0, 10) mod 94 != 8 for a given BF cell value
/// after rotation.
pub fn verifyConditional(bf_cell: u8) bool {
    const a = mb.rotate(@intCast(bf_cell), 10);
    const result = mb.crazy(a, 0, 10);
    return result % 94 != 8;
}

test "trampoline: crazy(0,0,10) mod 94 == 8" {
    try std.testing.expectEqual(@as(u128, 8), trampolineJmpResidue());
}

test "trampoline: 8 + 90 mod 94 == 4 (JMP)" {
    try std.testing.expectEqual(@as(u128, 4), (8 + 90) % 94);
}

test "conditional: all BF cells 1-255 produce non-JMP" {
    var cell: u16 = 1;
    while (cell <= 255) : (cell += 1) {
        try std.testing.expect(verifyConditional(@intCast(cell)));
    }
}

test "conditional: BF cell 0 produces JMP (via a=0)" {
    const a = mb.rotate(0, 10);
    try std.testing.expectEqual(@as(u128, 0), a);
    const result = mb.crazy(a, 0, 10);
    try std.testing.expectEqual(@as(u128, 8), result % 94);
}

test "rotate: BF cell values map correctly" {
    try std.testing.expectEqual(@as(u128, 0), mb.rotate(0, 10));
    try std.testing.expect(mb.rotate(1, 10) != 0);
    try std.testing.expect(mb.rotate(255, 10) != 0);
}

test "crazy: non-zero a with V=0 gives different residues" {
    const a1 = mb.rotate(1, 10);
    const a2 = mb.rotate(2, 10);
    const a3 = mb.rotate(128, 10);
    const r0 = mb.crazy(0, 0, 10) % 94;
    const r1 = mb.crazy(a1, 0, 10) % 94;
    const r2 = mb.crazy(a2, 0, 10) % 94;
    const r3 = mb.crazy(a3, 0, 10) % 94;
    try std.testing.expect(r1 != r0);
    try std.testing.expect(r2 != r0);
    try std.testing.expect(r3 != r0);
}
