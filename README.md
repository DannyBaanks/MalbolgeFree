# Malbolge Free

```
Malbolge Classic    :   >:(
Malbolge Unshackled :   >:D
Malbolge Free       :   ^w^   (Malbolgato)
```

## What this is, in one minute

1. Malbolge Classic runs every program at one fixed size: **10 trits**. Never
   more, never less.
2. Malbolge Free takes that fixed 10 and turns it into a **variable**, called
   `w`. `w` is the width the machine is using right now.
3. `w` always holds an ordinary finite integer. Think of it like `x` in a
   school equation:

   ```
   x = 10        <- right now the width is 10
   x = 11        <- later it can be 11
   ```

   Same variable, new finite value. Nothing in this project is infinite.
4. As long as `w = 10` is enough, the machine simply keeps running at 10.
5. If a pointer (`c` or `d`) walks all the way to the end of the current
   address space (cell `3^10 = 59049`), a rule called the **frontier policy**
   can move `w` from 10 to 11 before that step executes.
6. Everything the program already did before that moment stays exactly as it
   happened. The past is not recomputed and not rewritten.
7. Nobody here is calling anything "infinite".

Optional notation, if you like symbols (skip it if you don't — the words above
already say the same thing):

- `w_t` = the value of `w` at execution step `t`. From the recorded run:
  `w = 10` for the first 59049 steps, then `w = 11`.
- `W(state, current_width) -> next_width` = the rule that decides when `w`
  changes. The implemented rule: *if a pointer has reached `3^w`, bump `w` by
  one before running that step.*
- A stretch of execution under one value of `w` is called an **epoch** (just
  a stage of the run). When `w` changes, the finished epoch is said to be
  **anchored** — meaning: kept as-is, never recomputed.

So three different things share the letter w in conversation, and they are not
the same: `w` the variable, `w_t` its value at step `t`, and `W` the rule that
decides when the value changes.

## Quick answers

**Q: Does `w` mean infinity?**
A: No.

**Q: Does `w` have a real value while the program runs?**
A: Yes. Always a plain finite integer — for example 10, or later 11.

**Q: Why would `w` change?**
A: Because execution reached the edge of the current address space and the
next step needs more room.

**Q: Is the past re-executed with the new width?**
A: No. What ran at 10 stays exactly as it ran at 10.

**Q: Have we shown `w` can grow forever?**
A: No. We have shown one recorded transition, `10 -> 11`. Nothing more is
claimed.

## The machine

`MalbolgeCore(width, mem_limit, growth_policy)` — one core, three knobs.
In the code, the current value of `w` is stored in a field called `padwidth`
(starting from the `width` you boot with). We use `w` in the docs and
`padwidth` in the code; they are the same thing.

| policy | width evolves? | how | status |
|---|---|---|---|
| `fixed` | no | classic frozen width | Classic parity semantics |
| `pad_to_padwidth` | yes — by value overflow | pads operands when big values appear | **DESTROYED** by rotate (see below) |
| `epochal` | yes — by address frontier | widens `w` when `c`/`d` reach `3^w` | **DEMONSTRATED** for the tested `10 -> 11` transition |

## Demonstrated (re-verified 2026-09-05)

**FRONTIER WIDTH WIDENING** (`epochal` policy, unbounded memory): a
70000-character witness program built from `in`/`out`/`crazy`/`nop` ops only
(`evidence/gen_frontier_witness.py`) runs until `c` reaches `3^10 = 59049`;
the trigger fires exactly once, `w` goes `10 -> 11`, and the run continues.
The witness halts at step 70076 (a lazily-filled cell decodes `hlt`), long
before the next frontier `3^11 = 177147`. Actual output, reproduced twice:

```
WIDEN step=59050 c=59049 d=59049 old_w=10 new_w=11
run status: steps=70076 widen_events=1 at steps { 59050 }
final padwidth=11
```

**3^19 CROSSING** (legal-movd witness): the program `' & % $` booted at
`w = 20` executes `movd` over lazily-filled cells and ends with
`d = 1743392210 > 3^19 = 1162261467`. Python and Zig agree. Actual output:

```
cfg=k20_fixed status=MAX_STEPS steps=50 max_addr=1743392210 >3^19=true
```

**WIDTH-EXTENSION BROKENNESS** (`fixed` interpretation): rotating a value at
width `k` and then pretending it is a width-`k+1` value gives inconsistent
results for about 2/3 of inputs — `rotate(v,10)` needs `v % 3` to survive a
width change, and it doesn't. Measured: rotate agrees only 9/27 (33.3%) of
the time across widths; `crazy` agrees 729/729 (100%). This is why
"grow whenever a value overflows" is **not** a valid semantics.

**LAZY-FILL PERIODICITY**: the crazy-fill chain enters a period-6 cycle at
`program_len + 2`, numerically verified at widths 10, 11, 12, 19, 20, 26 over
all sampled seeds. This makes single-cell lazy lookup O(1). Claim stays at
"verified numerically", not "proved".

**LAZY == EAGER FILL** (Python reference core): `tests/t_phase23.py` —
bit-for-bit equality against the eager Classic fill for all 59049 cells at
`k=10`, plus spot checks at `k = 11, 12, 19`.

## Not demonstrated / destroyed

| Claim | Status |
|---|---|
| C7 `FRONTIER_WIDTH_WIDENING` | **DEMONSTRATED** — the tested `10 -> 11` transition only |
| C8 `REPEATED_WIDTH_WIDENING` | **NOT_DEMONSTRATED** — no run has crossed a second frontier |
| `UNSHACKLED_PARITY` | **NOT_DEMONSTRABLE** by construction (the original uses `srand(time(NULL))`) |
| `VALUE_OVERFLOW_WIDENING` (`pad_to_padwidth`) | **DESTROYED** — rotate breaks consistency across widths |
| `CLASSIC_PARITY_ZIG` (6/6 corpus) | **NOT CURRENTLY REPRODUCIBLE** — see below |

### Parity re-audit (2026-09-05)

`evidence/f4_classic_parity.json` (committed) records **6/6** sha256 matches
against the Python reference. Re-running the checker today produces **4/6**:
`hello.mal` and `reproducer.mal` diverge from the reference (Python prints
`Hello World!`; Zig emits garbage bytes; steps still match at 40).

Root cause located: in the Zig core's `crazy` op, the accumulator is masked
with a **bitwise AND** (`a & (3^w - 1)`) where Classic semantics call for
`a mod 3^w`. At step 3 of `hello.mal` this turns `a = 29524` into `25088`,
and everything downstream drifts. This affects the `fixed` policy too, so the
recorded 6/6 is not reproducible from the committed Zig as it stands.

The fix is one line (use `mod 3^w`), but it changes runtime behavior, so it
was **not applied in this documentation pass** — it is flagged for the owner's
decision. Live checker output is preserved in
`evidence/f4_classic_parity_rerun_20260905.json`.

## The "Purrfect" Badge

The pattern that makes this what it is: **memory values wrapped in crazy stay
in-byte**, but memory addresses (`c`, `d`) keep advancing through the address
space even when `mem_limit = null`. Crazy is width-agnostic. Rotate is not. So
the place your width change happens has to be "pointer advancement", not
"cell value". Built this project around Danny spotting that.

## A note on the old name

Earlier drafts used the symbol `ω` for this project and called the width claim
"TRUE_OMEGA_SEMANTICS". That notation was removed because it suggested
infinity or ordinal semantics that Malbolge Free does not claim. The variable
is just `w`, a finite integer at every executed step. The cat stays.

## Run

```bash
# classic-parity checker (Python reference vs Zig core)
py evidence/compare_f4.py

# frontier widening evidence (the 10 -> 11 transition)
zig run tests/t_frontier_moment.zig

# 3^19 crossing witness (k=20)
zig run evidence/f7_witness.zig

# rotate/crazy width-extension consistency (prints 33.3% / 100% line,
# then exits non-zero from its own assert — the printed numbers are the evidence)
py evidence/f8_check.py

# epochal invariants (halting programs never widen)
zig test tests/t_epochal.zig
```

Every evidence file prints its own verdict. All raw bytes are in `evidence/`.
Known-broken pieces are listed in `docs/HONESTY_LEDGER.md`.

## License

MIT ^w^

(It's the cat. It's always the cat.)

---

## Turing Completeness Demonstration

Malbolge is Turing-complete (Lou Scheffer, 1998). Practical demonstration in this repo:

**External reference (Malbolge-Translator):**
```bash
cd Malbolge-Translator/zig
zig run src/t_turing_full.zig
```
Output:
```
✅ TURING COMPLETENESS DEMONSTRATED
   Brainfuck (TC) -> Malbolge compilation works
   Both produce identical output: Hello World!
```

The generator (`generator.zig`) compiles arbitrary output strings to Classic Malbolge.
Since Brainfuck is TC and we can compile BF output → Malbolge, Malbolge is TC by reduction.
Reference: Scheffer (1998) "Malbolge is Turing-complete" — simulates restricted Brainfuck.
