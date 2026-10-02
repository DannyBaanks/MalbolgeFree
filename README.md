# Malbolge Free

```
Malbolge Classic    :   >:(
Malbolge Unshackled :   >:D
Malbolge Free       :   ^w^   (Malbolgato)
```

> **Release v1.1.0** (2026-10-02) — all milestones green or explicitly bounded.
> Harness 49/49 PASS, CI green on ubuntu + windows. Turing completeness holds
> via the documented inherited claim (`fixed` == Classic; Classic is TC per
> Scheffer 1999) — see [Turing Completeness Status](#turing-completeness-status).
> What is *not* claimed (unbounded growth, Unshackled parity, Ouroboros
> self-hosting, a new TC proof) is listed explicitly in that section.

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
   x = 12        <- and later 12, one rung at a time
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
  `w = 10` for the first 59049 steps, `w = 11` until step 177147, then
  `w = 12`.
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
A: Yes. Always a plain finite integer — for example 10, later 11, later 12.

**Q: Why would `w` change?**
A: Because execution reached the edge of the current address space and the
next step needs more room.

**Q: Is the past re-executed with the new width?**
A: No. What ran at 10 stays exactly as it ran at 10.

**Q: Have we shown `w` can grow forever?**
A: No. We have shown a finite ladder: `10 -> 11 -> 12` in the committed
witness, and every rung up to `19` measured on the real VM loop. Each rung
costs three times the steps and memory of the previous one, so this is a
measured ladder, not a proof of unbounded growth.

## The machine

`MalbolgeCore(width, mem_limit, growth_policy)` — one core, three knobs.
In the code, the current value of `w` is stored in a field called `padwidth`
(starting from the `width` you boot with). We use `w` in the docs and
`padwidth` in the code; they are the same thing.

| policy | width evolves? | how | status |
|---|---|---|---|
| `fixed` | no | classic frozen width | Classic parity semantics |
| `pad_to_padwidth` | yes — by value overflow | pads operands when big values appear | **DESTROYED** by rotate (see below) |
| `epochal` | yes — by address frontier | widens `w` when `c`/`d` reach `3^w` | **DEMONSTRATED** — ladder `10 -> 19` measured on the real VM |

## Demonstrated (re-verified 2026-09-16)

**FRONTIER WIDTH WIDENING** (`epochal` policy, unbounded memory): a witness
program built from `in`/`out`/`crazy`/`nop` ops only
(`evidence/gen_frontier_witness.py`) walks `c` linearly. When `c` reaches
`3^10 = 59049` the trigger fires, `w` goes `10 -> 11`, and the run continues;
the first 70000-character witness (kept as `evidence/frontier_witness.txt`)
halted at step 70076, before a second frontier. The current 190000-character
witness (`tests/frontier_witness.txt`) goes on to the next one. Actual output
of `tests/t_frontier_moment.zig` on 2026-09-16:

```
WIDEN step=59050 c=59049 d=59049 old_w=10 new_w=11
WIDEN step=177148 c=177147 d=177147 old_w=11 new_w=12
run status: steps=190000 widen_events=2 at steps { 59050, 177148 }
final padwidth=12
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

**REPEATED WIDTH WIDENING** (the epochal ladder): a 190000-character witness
of the same kind crosses two frontiers, `10 -> 11` at step 59050 and
`11 -> 12` at step 177148. `tests/t_m5_full_vm.zig` runs it through the real
`vm.run` loop (not a hand-stepped loop) and checks both rungs; the record is
`evidence/f9_repeated_frontier.json`.

How far it climbs is limited by memory, not by the rule: to reach `w` the
pointer must walk to `3^(w-1)`, and every executed cell is stored.
`evidence/M5_LADDER_SCALE/` generates longer witnesses and runs them on the
real VM. Measured on a 15 GiB laptop (2026-09-16), each rung from a fresh
`w = 10`, using the hash-map representation:

| climbs to | steps | widenings | cells stored |
|---:|---:|---:|---:|
| 13 | 531,442 | 3 | 532,454 |
| 14 | 1,594,324 | 4 | 1,595,336 |
| 15 | 4,782,970 | 5 | 4,783,982 |
| 16 | 14,348,908 | 6 | 14,349,920 |

**The ladder now reaches 19** (2026-10-01), after the dense representation
described below removed the memory wall that stopped it at 16:

| climbs to | steps | widenings | cells stored | seconds | array |
|---:|---:|---:|---:|---:|---:|
| 17 | 43,046,722 | 7 | 43,047,734 | 16.0 | 172 MB |
| 18 | 129,140,164 | 8 | 129,141,176 | 22.4 | 516 MB |
| 19 | 387,420,490 | 9 | 387,421,502 | 38.5 | 1.55 GB |

Measured on Linux x86_64, 14.8 GiB RAM, peak RSS 1.92 GiB for all three rungs
together (`run_ladder_scale.py --dense`, rows tagged `linux-14gib-dense` in
`evidence/M5_LADDER_SCALE/results.json`). Step counts match the hash-map
measurements exactly where both exist (rung 17: `43046722`, `padwidth=17`,
`growth=7`), so the representation changed the cost, not the measurement.

The old estimates for `17`/`18`/`19` (~2.1 / 8.4 / 16.9 GiB) were hash-map
figures and no longer apply. `19` no longer needs a 32 GiB machine.

The ladder above is measured with the Zig engine, but the `epochal` policy is no
longer single-engine: `src/malbolge_core.py` implements it and
`evidence/compare_epochal.py` cross-checks both implementations on widening
position, final width and output. That parity is exercised on witnesses that
cross several frontiers (including `w=10 -> 11`), not on the full 129M-step
ladder, which stays a Zig measurement.

### Dense representation (why 19 became reachable)

The hash map spends ~33 bytes per cell (16-byte key + 16-byte value + 1
metadata byte) on what is, before self-modification, **one ASCII byte** — and a
ladder witness is almost entirely source. That map, not the computation, was the
memory wall.

With `--dense`, the materialised range `[0, program_len+12)` is a flat `u32`
array (4 bytes per cell) and the hash map keeps only writes that land outside
it. Consequences:

- ~8x less RAM per rung; the `19` rung costs 1.55 GB instead of ~16.9 GiB.
- **Off by default.** Every existing constructor keeps the historical
  representation, so Classic parity and the epochal evidence are untouched.
- `enableDenseSource()` **refuses** widths whose values do not fit `u32`, i.e.
  `w >= 21` (`3^21` overflows). So the dense path has a structural ceiling at
  `w = 20`. The hash path has no such ceiling but costs ~33 bytes per cell.
- Equivalence is asserted, not assumed: `tests/t_dense_differential.zig` runs
  both representations and requires identical stdout, status, steps, final
  `a`/`c`/`d`, cells touched, encrypted cells and a field-by-field trace match.

`UNBOUNDED_WIDTH_GROWTH` therefore remains **NOT_DEMONSTRATED**, and now for a
sharper reason than "we stopped measuring": the ladder is finite by
construction, and in the dense representation it is bounded at `w = 20` by the
element type.

## E10 -> E19 epoch ladder (toy)

`epoch_ladder/` carries a separate, smaller experiment that *does* reach 19.
It is a **toy** and is labelled as one everywhere it appears.

- `dimension_epoch_ladder.py`: a parametric family with memory `3^k` and
  `c`/`d` wrapping at `3^k`, for `k = 10 .. 19`. The same three-op program
  `ubO` (`in`, `out`, `end`) runs in each dimension and the state byte `Z`
  crosses every boundary sealed by a hash. Replay passes, tamper is rejected.
- `offset_epoch_ladder.py`: a preregistered test of whether the three-region
  offset formula of the real 19-trit runtime generalises to `k = 11 .. 18`.
  The table is frozen by hash before running. Result: round-trip and boundary
  gates pass at every `k`, `first_failure: null`, and the same formula
  reproduces the existing E19 offsets.

```
E10 -> E11 -> E12 -> E13 -> E14 -> E15 -> E16 -> E17 -> E18 -> E19
state 5a at every boundary, 3 steps per epoch     LADDER PASS
FORMULA_GENERALIZES_E11_TO_E18=DEMONSTRATED
```

What it does **not** show: there is no historical Malbolge at 11..18 trits,
so E11–E18 are toy profiles, not recovered languages. What crosses the ladder
is state and the positional codec; `crazy`, rotation, encryption and jumps
are not demonstrated at the intermediate widths, and no arbitrary program is
claimed to be equivalent across them. Only E10 (Classic) and E19
(Unshackled-style) are real anchors. This is also a different thing from the
epochal ladder above: there `w` changes *inside one run*; here each epoch is
its own fixed dimension.

## Not demonstrated / destroyed

| Claim | Status |
|---|---|
| C7 `FRONTIER_WIDTH_WIDENING` | **DEMONSTRATED** — `10 -> 11` |
| C8 `REPEATED_WIDTH_WIDENING` | **DEMONSTRATED** — committed witness `10 -> 11 -> 12` on the real VM; rungs up to `19` measured in `evidence/M5_LADDER_SCALE/` (17-19 via the dense representation) |
| `UNBOUNDED_WIDTH_GROWTH` | **NOT_DEMONSTRATED** — the ladder is finite by construction and now measured to `19`; the dense path is additionally bounded at `w = 20` by the `u32` element type |
| `EPOCHAL_PYTHON_PARITY` | **DEMONSTRATED** (2026-10-01) — `src/malbolge_core.py` implements `epochal`; `evidence/compare_epochal.py` diffs it against the Zig core on status, steps, `padwidth`, widening count, final `c`/`d`, encrypted cells and stdout SHA-256 |
| `E10_TO_E19_TOY_LADDER` | **DEMONSTRATED (toy)** — state transport + codec only; see `epoch_ladder/` |
| `UNSHACKLED_PARITY` | **NOT_DEMONSTRABLE** by construction (the original uses `srand(time(NULL))`) |
| `VALUE_OVERFLOW_WIDENING` (`pad_to_padwidth`) | **DESTROYED** — rotate breaks consistency across widths |
| `CLASSIC_PARITY_ZIG` (6/6 corpus) | **DEMONSTRATED** — reverified 2026-09-12, and now reproducible from a fresh checkout: the oracle is built natively with `zig run`, no `.exe` and no wine |

### Parity re-audit (2026-09-12, oracle rebuilt 2026-10-01)

`evidence/compare_f4.py` re-runs against the canonical reference and reports
`all_match: true` for all six programs, including `hello.mal` and
`reproducer.mal`. This claim is limited to the six-program corpus.

The oracle used to be a Windows `.exe` produced by hand and never committed, so
outside Danny's machine F4 could not run at all. The oracle is now
`zig/src/parity_check.zig` in the sibling `Malbolge-Translator` repo, tracked
along with its corpus (commit `0c8a56b`), and it is built natively:

```bash
zig run --dep engine=engine -Mroot=src/parity_check.zig -Mengine=src/engine.zig
```

run from that repo's `zig/` directory. It imports `engine.zig`, never
`malbolge_free.zig`, so it stays an independent implementation of Classic
rather than a copy of the runtime under test. `compare_f4.py` also verifies
that both repos embed a byte-identical corpus and refuses to report parity if
they ever diverge (`F4_CORPUS_DIVERGENCE`, exit 4).

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
# all reproducible gates
py tests/run_all.py

# product CLI and positional Classic codec
py malbolge_cli.py verify
py malbolge_cli.py assemble "in,out,rot,movd,opr,nop,end"

# classic-parity checker (independent Zig oracle vs canonical Zig core)
py evidence/compare_f4.py

# frontier widening evidence (10 -> 11 -> 12 on the committed witness)
zig run tests/t_frontier_moment.zig

# ladder on the real VM loop, then climb further (see the scale guide)
py evidence/M5_LADDER_SCALE/run_ladder_scale.py --estimate 17 18 19
py evidence/M5_LADDER_SCALE/run_ladder_scale.py 13 14 15 16

# E10 -> E19 toy ladder
py epoch_ladder/dimension_epoch_ladder.py
py epoch_ladder/offset_epoch_ladder.py run

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

## Clean-room Classic emitter (`tools/`)

Separate from the Malbolge Free work above, this repository now carries our own
**Malbolge Classic** emitter, written clean-room: no external assembler at
runtime, no HeLL, no generated initialisation code.

### What it does

```python
import microprogram as mp
mp.emit_program([
    ("out", 0x3e),        # '>'
    ("in",),              # read one byte
    ("out_acc",),         # echo it
    ("jmp", "done"),
    ("out", 0x58),        # 'X' — unreachable trap
    ("label", "done"),
    ("out", 0x0a),        # newline
    ("halt",),
])
```

That description compiles to **one** 120-cell Classic Malbolge program
(`sha256 6a9f04ff…`). Feed it `A`, it prints `>A
` in 14 steps. The trap byte
`X` never appears, because the jump really happens.

| capability | example | cells |
|---|---|---:|
| byte synthesis | any of the 256 output bytes | 42–118 |
| sequential output | `HI
` | 51 |
| real input | `IN;OUT;HALT` = `(taN` | 4 |
| state + transform | `IN` → `crazy(A,39)` → `OUT` | 43 |
| unconditional jump | `A`, jump, unreachable `X`, `B` → `AB` | 122 |
| composed microprogram | the one above | 120 |

Every program is verified on **two independent engines** — a Python oracle and
a Zig runner — matching on status, output *and* step count. Emitted sources are
deterministic (stable SHA-256).

### The layout trick

Cell 0 holds `(` (value 40): at position 0 it decodes to `MovD`, *and* its value
is 40 — so the first instruction sets `d = 40`. During a linear stretch
`d = c + 40`, which means an op at code position `p` operates on data cell
`40 + p` and the accumulator carries across ops. Chaining `Rot`/`Opr` *is* the
synthesis.

**That invariant is local.** A `Jmp` breaks it: the VM does `c = mem[d]`,
encrypts the landing cell without executing it, and resumes at `mem[d] + 1`, so
the offset becomes `(d_jmp + 1) - target` (measured: `+40` → `-16`). The emitter
tracks `c` and `d` explicitly and never assumes `+40`.

Growth is linear: **+3 cells and +3 steps per output byte**.

### What it cannot do

No conditional branching, no loops, no backward jumps, no functions, no general
mutable memory, no arbitrary HeLL compilation, no Turing-complete frontend.
Those are not demonstrated and are not claimed.

### Run it

```bash
cd tools
py -m unittest discover -p "test_*.py" -v     # 33 tests

cd ../evidence/M4_MICROPROGRAM_V0
py run_m4.py                                   # 19 cases on both engines
```

Evidence, per milestone, with preregistrations, results and hashes:
`evidence/M2_BOOTSTRAP_REACH_V0/`, `evidence/M3_RAW_LAYOUT_V0/`,
`evidence/M4_MICROPROGRAM_V0/`, `evidence/A5_LMAO_PARITY_V0/`.
Guides (Spanish, with real executed output): `docs/GUIA_ESCALERA.md`, `docs/GUIA_RAW_MALBOLGE.md`,
`docs/GUIA_BOOTSTRAP.md`, `docs/GUIA_HELL_HIBRIDO.md`.

### On LMAO (external, GPLv3)

Matthias Lutter's [LMAO](https://github.com/esoteric-programmer/LMAO) is used
**only as an external behavioural oracle**, invoked as a separate process and
never vendored, linked or copied into this repository. `evidence/A5_LMAO_PARITY_V0/`
records the comparison: its six HeLL examples pass 34/34 of its own test
expectations on our two engines.

## License

MIT ^w^

(It's the cat. It's always the cat.)

---

## Turing Completeness Status

**M6 is PASS via the documented inherited claim**
(`docs/TURING_COMPLETENESS_INHERITED.md`): our `fixed` profile is byte-identical
to Classic Malbolge (F4 6/6, reproducible from a fresh clone), and Classic is
Turing-complete per Scheffer 1999 (cyclic tag system compiler, cited via the
esolangs wiki). This is the ROADMAP's explicitly named third route — an
inheritance, **not** a new proof.

What a new proof would still require (and remains NOT_DEMONSTRATED): a
BF→Malbolge compiler that preserves states, loops and input, or a BF/UTM
interpreter written in Malbolge Free. The output-reproduction smoke test below
is explicitly **not** that — it computes a finite Brainfuck output first and
then generates Malbolge for that output. It does not translate arbitrary BF
semantics. Ver `docs/TURING_COMPLETENESS.md`.

**Smoke test externo (Malbolge-Translator):**
```bash
cd Malbolge-Translator/zig
zig run src/t_turing_full.zig
```
Output:
```
OUTPUT REPRODUCTION SMOKE TEST: PASS
   Brainfuck output -> Malbolge generation works
   Both produce identical output: Hello World!
```

**Explicitly NOT claimed in any release:** unbounded width growth (finite by
construction; dense bounded at `w = 20`), Unshackled bit-parity (the reference
uses `srand(time(NULL))`), Ouroboros self-hosting (measured ~255-byte input
ceiling, unresolved brackets), and a new self-contained TC proof.
