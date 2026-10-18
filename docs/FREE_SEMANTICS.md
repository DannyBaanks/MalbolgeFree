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
reproduced bit-for-bit across all 59049 cells (`tests/t_phase23.py`). On the Zig
side it is now measured against **canonical** interpreters: 22 verdicts
(11 cases x 2 cores), 44 stdout SHA-256 comparisons with this machine's two
oracles (`evidence/compare_f4_canonical.py`, 2026-10-17; the canonical Python
oracle is vendored and hash-pinned in `vendor/canonical_malbolge_py/`, so a fresh
clone measures 10 x 2 x 1 = 20 comparisons instead of skipping). Earlier states of
this note were
themselves corrections: 2026-09-05 found 4/6 with a bitwise-mask bug in the Zig
`crazy` op, 2026-09-12 reported 6/6 against `engine.zig`, and the 2026-10-17 audit
showed that oracle shared our non-canonical EOF convention, so it could not falsify
the EOF bug (see `docs/HONESTY_LEDGER.md` entries 19, 20, 22 and the appended 24
and 25).

`Free(k=19)` reproduces the *parameterized* Unshackled behavior: the real
Unshackled starts `rotwidth = 10 + rand() % 6`, so exact bit-parity is
impossible — **documented as parity-class, not bit-parity**.

## Claims

```
C0  SINGLE_PARAMETRIC_CORE         = DEMONSTRATED
C1  CLASSIC_PARITY_K10             = DEMONSTRATED 2026-10-17 against canonical
                                     interpreters: 22 verdicts (11 cases x 2 cores),
                                     44 stdout SHA-256 comparisons with 2 oracles
                                     (evidence/f4c_canonical_parity_20261017.json;
                                     re-measured with the vendored pinned oracle in
                                     evidence/f4c_canonical_parity_vendored_20261017.json).
                                     History of this row: 4/6 on 2026-09-05 (Zig
                                     crazy bitwise-mask bug, later fixed), recorded
                                     6/6 vs engine.zig, then superseded because that
                                     oracle shared our non-canonical EOF value.
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
C10 TURING_COMPLETENESS            = INHERITED (fixed==Classic, Classic is TC
                                      per Scheffer 1999; see docs/TURING_COMPLETENESS_INHERITED.md.
                                      NEW_CLAIM stays NOT_DEMONSTRATED)
EPOCHAL_PYTHON_PARITY              = DEMONSTRATED (2026-10-01; Zig vs Python core
                                      on epochal witnesses up to 60k steps)
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

## Addendum (2026-10-18) — appended; supersedes the count in the `epochal` table row,
and adds a measured compatibility statement per policy

The growth-policy table above says `epochal` is defended with "one transition
measured (C7)". That row is left as written and superseded by C8, which the claims
block below already carries: `evidence/f9_repeated_frontier.json` measures **two**
transitions on one witness — `10 -> 11` at step 59050 and `11 -> 12` at step 177148,
`final_width: 12`. Nothing beyond `w = 12` is claimed.

`evidence/f10_quine_epochal_20261018.json` (ledger entry 29) then asks the question
the policy table cannot answer: does each policy *behave* like Classic on a real
program? One program, Lutter's quine (`DannyBaanks/MalDOOM:vendor/quines/quine_lutter.malbolge`,
sha256 `dca8476f…`, 59 852 bytes on disk / 59 032 loaded cells), empty stdin, our own
Zig core with the Python core as cross-check:

| profile | `mem_limit` | growth | outcome on the quine |
|---|---|---|---|
| `classic` | `3^10` (wrap) | `fixed` | `HALTED` at 69 547 437 steps, 59 852 bytes of stdout, sha256 equal to the program: it reproduces itself |
| `pure_fixed` | `null` | `fixed` | `HALTED` at 6 521 steps, **1 byte** of stdout |
| `epochal` | `null` | `epochal` | `HALTED` at 8 761 steps, **0 bytes**; widened `10 -> 11` once, at step 1230 |

Three readings follow, and the artifact is written so each is separable:

1. **The wrap is the load-bearing parameter.** `pure_fixed` changes nothing except
   `mem_limit`, and the quine stops self-reproducing. So the two lower rows are not
   evidence against frontier growth; they are evidence that removing address wrapping
   already leaves Classic.
2. **The frontier is reachable on real code, and earlier than the synthetic witnesses
   suggest.** `d` is *assigned* to `3^10` at step 1229 rather than walked to it at
   step 59050. The witnesses' step does not generalise; invariant P1 (history
   preserved until the first `WIDEN`) does — the earliest `pure_fixed` vs `epochal`
   trace divergence is step 1246, after the widening at 1230.
3. **Pre-execution state is not the cause.** Stored and addressed memory images are
   byte-identical across all three profiles (`c455d288…`, no first difference), so the
   divergence is produced during execution by addressing, not by `load`.

Not claimed here: that one program generalises to the corpus; that `epochal` is or is
not Turing-complete (see `docs/TURING_COMPLETENESS_INHERITED.md`, and `TURING_COMPLETENESS_NEW_CLAIM`
stays `NOT_DEMONSTRATED`); that F10 is reproducible on a fresh clone — the quine is
third-party and deliberately not vendored, so `compare_quine_epochal.py` exits 3
(`NOT_DEMONSTRATED, missing external input`) when MalDOOM is not beside this repository.
F10 is **not** in `tests/run_all.py`'s gate list, so the published gate count is
unchanged by it.

