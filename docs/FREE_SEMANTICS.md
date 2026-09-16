# MALBOLGE FREE — Semantic Definition

`Free(k)` is a parametric family `M_k` with a single core, no width
special-cases.

## Parameters

| Param | Value |
|---|---|
| `width k` | number of trits in `crazy` and `rotate` at boot — the start width |
| `mem_limit` | `3^k` (finite, wrap) or `null` (unbounded, lazy crazy-fill) |
| `growth_policy` | `fixed`, `pad_to_padwidth` (legacy, see C6), or `epochal` |

Naming: the docs call the current width `w`. The code stores it in the field
`padwidth`, initialised from `width`. Same thing, two names; `w` is the
conceptual/documental name of "active width". At every executed step `w` is a
concrete finite integer (10, then 11 in the recorded run).

## What stays constant

- Same 8 opcodes, same numeric ops.
- Same `(cell + pos) % 94` decode.
- Same `_ENC` encryption table.
- Lazy crazy-fill rules load `cell = crazy(mem[i-1], mem[i-2])` no matter the
  width.

## What IS width-dependent

- `crazy` uses exactly the current width `w` trits (Classic: 10 fixed).
- `rotate(v)` = `v // 3 + (v % 3) * 3^(w-1)`.
- Memory size (if any) = `3^k`.
- `mod 3^k` wrap on addresses (present iff `mem_limit = 3^k`).

Implementation note (2026-09-05): the lazy crazy-fill in the Zig core fills
new cells using the **start** width even after an epochal widening
(`crazy(v1, v2, self.width)`). Cells are not recomputed when `w` changes;
that is exactly the anchor property applied to the fill.

## What FREE adds

- **No `if k==10` or `force_unshackled` gates.** Same core sees `10..26`.
- Growth policies:
  - `fixed`: `w` never changes. Classic semantics.
  - `pad_to_padwidth`: value-overflow growth. **Destroyed** for rotate (C6);
    kept in the code as a legacy probing mode, not defended as semantics.
  - `epochal`: address-frontier growth. When `c` or `d` reaches `3^w`,
    `w` increases by one before that step executes; everything already
    produced stays untouched. This is the only defended growth semantics.
- **Lazy crazy-fill with 6-periodicity shortcut**: the crazy-chain from any
  seed enters a period-6 tail (verified numerically for widths 10, 11, 12,
  19, 20, 26 over all sampled seeds). Enables writing beyond any finite
  boundary without materializing every cell.

## Growth policy table

| policy | trigger | change to `w` | defended? |
|---|---|---|---|
| `fixed` | none | none | yes (Classic) |
| `pad_to_padwidth` | a value needs more trits | jumps to fit the value | no — destroyed by rotate (C6) |
| `epochal` | `c` or `d` reaches `3^w` | `w -> w + 1`, once per frontier | yes — one transition measured (C7) |

## Honesty note

`Free(k=10, fixed, wrap)` == Classic. On the Python side that equality is
reproduced bit-for-bit across all 59049 cells (`tests/t_phase23.py`); on the
Zig side the recorded 6/6 corpus parity is **not currently reproducible**
(2026-09-05 re-audit: 4/6, bitwise-mask bug in the Zig `crazy` op located —
see README and `docs/HONESTY_LEDGER.md`).

`Free(k=19)` reproduces the *parameterized* Unshackled behavior: the real
Unshackled starts `rotwidth = 10 + rand() % 6`, so exact bit-parity is
impossible — **documented as parity-class, not bit-parity**.

## Claims

```
C0  SINGLE_PARAMETRIC_CORE         = DEMONSTRATED
C1  CLASSIC_PARITY_K10             = recorded 6/6 in evidence/f4_classic_parity.json;
                                     NOT reproducing live as of 2026-09-05 (4/6,
                                     bitwise-mask bug located in Zig crazy op,
                                     fix pending owner decision)
C2  UNSHACKLED_PARITY_K19          = NOT_DEMONSTRABLE (nondeterministic reference)
C3  ARBITRARY_FINITE_K             = DEMONSTRATED
C4  NO_FIXED_COMPILED_MAX_ADDR     = DEMONSTRATED
C5  LEGAL_CROSSING_3_POW_19        = DEMONSTRATED
C6  WIDTH_EXTENSION_CONSISTENCY    = DESTROYED for rotate (33.3% agreement),
                                     CONSISTENT for crazy (100%)
C7  FRONTIER_WIDTH_WIDENING        = DEMONSTRATED — the tested 10 -> 11
                                     transition only (tests/t_frontier_moment.zig:
                                     WIDEN at c = 3^10, history preserved,
                                     w = 11 from that step on)
 C8  REPEATED_WIDTH_WIDENING        = DEMONSTRATED — witness crosses
                                      10 -> 11 at step 59050 and 11 -> 12 at
                                      step 177148 (evidence/f9_repeated_frontier.json)
C9  CLASSIC+UNSHACKLED=>FREE       = DEMONSTRATED (parametric reading)
C10 TURING_COMPLETENESS            = NO_NEW_CLAIM
```

(C7/C8 keep their numbers from the original claims table; only the names and
definitions changed — 2026-09-05, when the old omega-based names were retired.)

## Explicitly not claimed

- That `w` is infinite, unbounded-in-principle, ordinal, or anything other
  than a variable holding one finite integer per step.
- That widening can repeat arbitrarily often: two transitions are recorded;
  behavior beyond `12` remains unclaimed.
- That epochs are equivalent views of each other: rotate breaks any
  simultaneous-equivalence reading (C6); the claim is sequential only.
