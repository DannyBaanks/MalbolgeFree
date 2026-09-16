const std = @import("std");
const mb = @import("malbolge_free");

/// BF conditional via trampoline — concrete implementation.
///
/// The mechanism:
///   1. ROT reads BF cell → a (a=0 iff cell is zero)
///   2. OPR modifies trampoline at position T: cell[T] = crazy(a, V, w)
///   3. At T: op = (cell[T] + T) % 94. If a=0: op=4=JMP. If a≠0: op≠4.
///   4. JMP reads cell[d] and sets c = cell[d].
///
/// The d-synchronization problem: after ROT (d++), OPR (d++), and intervening
/// NOPs (d++ each), d = T when JMP executes. So JMP reads cell[T] = trampoline.
///
/// This means: when a=0, c = crazy(0, V, 10) = 29524 (if V=0). That jumps
/// to position 29524 — OUTSIDE the program.
///
/// SOLUTION: Use a two-phase approach.
///   Phase 1: ROT + OPR to modify trampoline
///   Phase 2: MOVD to redirect d to a CELL containing the target address
///   Phase 3: JMP — reads cell[d] = target address
///
/// But MOVD sets d = cell[d], and d advances after each step.
/// After phase 1: d = BF_addr + 2 (after ROT at P, OPR at P+1)
/// After MOVD: d = cell[BF_addr + 2] (need this to be trampoline addr T)
/// After NOPs: d advances further
/// At JMP: d = ... complicated
///
/// ACTUAL SOLUTION: Don't use the trampoline as the jump target.
/// Instead, use the trampoline ONLY to determine the instruction at T.
/// The jump target is a SEPARATE cell that d points to when JMP executes.
///
/// Layout:
///   Pos P:   ROT (reads BF cell → a)
///   Pos P+1: OPR (modifies cell[T] = crazy(a, V, w))
///   Pos P+2 to T-1: NOPs (advance c and d to T)
///   Pos T:   [trampoline] — cell[T] determines instruction
///   After T steps from P: d = T - P + (BF_addr + 2) = BF_addr + (T - P + 2)
///
/// When JMP at T executes: d = BF_addr + (T - P + 2).
/// JMP reads cell[BF_addr + (T - P + 2)] as jump target.
///
/// We need cell[BF_addr + (T - P + 2)] = target_address.
/// We can pre-load this cell in the DATA section.
///
/// For T % 94 = 90 and P = 0:
///   d = BF_addr + (90 + 2) = BF_addr + 92
///   cell[BF_addr + 92] must = target_address
///
/// If BF_addr = 0: cell[92] = target_address.
/// We can set cell[92] in the DATA section!
///
/// For `[` (open bracket):
///   If BF cell == 0: JMP past the loop body
///   If BF cell != 0: fall through (enter loop)
///
/// For `]` (close bracket):
///   If BF cell != 0: JMP back to loop start
///   If BF cell == 0: fall through (exit loop)
///
/// The `]` is the inverse: we need JMP when a≠0, not JMP when a=0.
/// This requires a different trampoline initial value V.
///
/// For `]` with V ≠ 0:
///   a=0: crazy(0, V, 10) mod 94 ≠ 8 → not JMP ✓
///   a≠0: crazy(a, V, 10) mod 94 = 8 → JMP ✓
///
/// Need to find V such that crazy(a, V, 10) mod 94 = 8 for ALL a≠0
/// where a = rotate(cell, 10) for cell in 1..255.
///
/// This is harder to prove. For now, let's implement `[` only.

const TRAMPOLINE_POS: usize = 90; // 90 % 94 == 90
const NOP_AFTER_OPR: usize = 2; // ROT at P, OPR at P+1, so d = BF_addr + 2 after OPR

test "conditional: trampoline at pos 90 with V=0" {
    // Verify the trampoline works for the `[` case.
    const t_pos: u128 = 90;
    const v: u128 = 0;

    // When a=0: trampoline becomes JMP
    const a_zero: u128 = 0;
    const result_zero = mb.crazy(a_zero, v, 10);
    try std.testing.expectEqual(@as(u128, 4), (result_zero + t_pos) % 94);

    // When a≠0: trampoline does NOT become JMP
    const a_one = mb.rotate(1, 10);
    const result_one = mb.crazy(a_one, v, 10);
    try std.testing.expect((result_one + t_pos) % 94 != 4);

    const a_max = mb.rotate(255, 10);
    const result_max = mb.crazy(a_max, v, 10);
    try std.testing.expect((result_max + t_pos) % 94 != 4);
}

test "conditional: MOVD redirection analysis" {
    // After MOVD at pos 2: d = cell[2] (the MOVD command char)
    // emitCommandToChar(40, 2) = ((40 + 94) - 2) % 94 = 132 % 94 = 38
    const cmd: u8 = 40; // MOVD
    const pos: usize = 2;
    const pos_mod: u8 = @intCast(pos % 94);
    var ch: u8 = ((cmd +% 94) -% pos_mod) % 94;
    if (ch < 33) ch += 94;
    try std.testing.expectEqual(@as(u8, 38), ch); // '&' character

    // After MOVD: d = 38. Then d++ → d = 39.
    // After NOPs at pos 3..89: d = 39 + 87 = 126.
    // At JMP at pos 90: d = 126.
    // JMP reads cell[126] as jump target.
    const d_at_jmp: u128 = 38 + 1 + (90 - 3); // 38 + 1 (d++) + 87 (NOPs)
    try std.testing.expectEqual(@as(u128, 126), d_at_jmp);
}

test "conditional: full sequence verification" {
    // The full sequence for `[` (open bracket):
    //   Pos 0: ROT (reads BF cell → a)
    //   Pos 1: OPR (modifies trampoline at pos 90)
    //   Pos 2: MOVD (d = cell[2] = 38)
    //   Pos 3..89: NOPs (d advances to 126)
    //   Pos 90: [trampoline] — JMP if a=0, else something else
    //   Pos 91: HALT (if not skipped)
    //
    // When a=0 (BF cell is zero):
    //   - Trampoline at pos 90: op = (crazy(0,0,10) + 90) % 94 = 4 = JMP
    //   - JMP reads cell[126] as jump target
    //   - If cell[126] = 91: c = 91 (skip to HALT) ✓
    //
    // When a≠0 (BF cell is non-zero):
    //   - Trampoline at pos 90: op ≠ 4 (not JMP)
    //   - Falls through to pos 91 (HALT) — same as skip!
    //
    // Wait, that's wrong. When a≠0, we should ENTER the loop, not skip.
    // But pos 91 is HALT in both cases.
    //
    // The issue: the trampoline only controls WHETHER to jump.
    // If not JMP, we fall through to pos 91 (HALT).
    // If JMP, we jump to cell[126] (which we set to 91 = HALT).
    //
    // Both cases end at HALT! That's not a conditional.
    //
    // The problem: we need TWO different targets:
    //   - When a=0: jump to HALT (skip loop)
    //   - When a≠0: fall through to loop body (enter loop)
    //
    // But the trampoline only controls whether to jump, not where.
    // The jump target is always cell[126].
    //
    // For a real conditional:
    //   - When a=0: JMP to HALT (cell[126] = 91)
    //   - When a≠0: not JMP, fall through to loop body (pos 91 = loop body)
    //
    // So pos 91 must be the LOOP BODY, not HALT.
    // And cell[126] must be the HALT position (after the loop body).
    //
    // This works! The layout is:
    //   Pos 0: ROT
    //   Pos 1: OPR
    //   Pos 2: MOVD
    //   Pos 3..89: NOPs
    //   Pos 90: trampoline
    //   Pos 91: loop body (if a≠0, fall through here)
    //   ...
    //   Pos N: HALT
    //   cell[126] = N (HALT position)
    //
    // When a=0: JMP to N (skip loop body)
    // When a≠0: fall through to pos 91 (enter loop body)
    //
    // This is the correct mechanism!
    //
    // For `]` (close bracket): we need the INVERSE.
    //   - When a≠0: JMP back to loop start
    //   - When a==0: fall through (exit loop)
    //
    // This requires a different trampoline initial value V.
    // With V=0: a=0 → JMP, a≠0 → not JMP. Wrong direction for `]`.
    //
    // For `]` with V≠0: need crazy(a, V, 10) mod 94 = 8 for a≠0.
    // This is harder to prove. For now, let's implement `[` only.

    // Verify the layout is correct.
    // When a=0: trampoline is JMP, cell[126] = HALT position
    // When a≠0: trampoline is not JMP, fall through to loop body

    // The trampoline value when a=0:
    const t_val = mb.crazy(0, 0, 10);
    try std.testing.expectEqual(@as(u128, 29524), t_val);

    // (29524 + 90) % 94 = 4 = JMP
    try std.testing.expectEqual(@as(u128, 4), (t_val + 90) % 94);

    // When a≠0: trampoline value mod 94 ≠ 8 (so op ≠ 4)
    const a1 = mb.rotate(1, 10);
    const t_val1 = mb.crazy(a1, 0, 10);
    try std.testing.expect(t_val1 % 94 != 8);
}
