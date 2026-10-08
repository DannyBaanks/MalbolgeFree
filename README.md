# Malbolge Free

> **Measured update — 2026-10-08:** the real epochal VM reached **width 20**
> from boot width 10, and a separate parametric sweep measured **targets 1–20**
> with every VM booting at 1. Peak RAM at 20 was about **5.77 GiB**.
> [Results, tables, resource limits and verification](#measured-e20-and-ram-scaling-2026-10-08).
> The dense `u32` representation still stops at 20. Tiny-width runs explicitly
> accept ASCII outside the initial word range; fixed20 also has a demonstrated
> EOF disagreement with the original Nagoya interpreter.

```
Malbolge Classic    :   >:(
Malbolge Unshackled :   >:D
Malbolge Free       :   ^w^   (Malbolgato)
```

> **Historical release v1.1.0** (2026-10-02) — all milestones green or explicitly bounded.
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
A: No. The real VM has reached `20` from boot width `10`. A separate
parametric sweep starts at `1` and measures every target through `20`, with
explicit tiny-width word-range exceptions. For this linear witness, steps
and large-rung storage grow approximately threefold per rung. Width `21`
was not executed; the dense `u32` representation ends at `20`.

## The machine

`MalbolgeCore(width, mem_limit, growth_policy)` — one core, three knobs.
In the code, the current value of `w` is stored in a field called `padwidth`
(starting from the `width` you boot with). We use `w` in the docs and
`padwidth` in the code; they are the same thing.

| policy | width evolves? | how | status |
|---|---|---|---|
| `fixed` | no | classic frozen width | Classic parity semantics |
| `pad_to_padwidth` | yes — by value overflow | pads operands when big values appear | **DESTROYED** by rotate (see below) |
| `epochal` | yes — by address frontier | widens `w` when `c`/`d` reach `3^w` | **DEMONSTRATED (scoped)** — `10 -> 20`; separate parametric `1 -> 20` sweep below |

## Measured E20 and RAM scaling (2026-10-08)

These are finite, workload-specific measurements on GitHub Ubuntu runners.
Each benchmark starts a fresh VM; its epochal execution crosses every
frontier up to the target. A target reached with `MAX_STEPS` means the
configured execution budget ended, rather than a program `HALT`.
The original runtime source was unchanged. An observation-only core copy
records actual widening events; small original/observed differential checks
and repeated runs validate that instrumentation.

### Continuous boot10 run: 10 → 20

One uninterrupted `vm.run`, boot width 10, `epochal`, `free_pure`, no address
wrap and dense `u32` storage reached width 20 after **1,162,261,468 steps**
and **10 widenings**. Final `c` and `d` were both 1,162,261,468. It materialized
1,162,262,480 cells and produced 383,299,003 output bytes, with zero assisted
opcodes. Peak RSS was **6,197,026,816 bytes (5.77 GiB)**; executable wall time
was **109.87 s**.

The final transition was recorded before reading the boundary instruction:

```text
WIDEN step=1162261468 c=1162261467 d=1162261467 old_w=19 new_w=20
```

[CI run](https://github.com/DannyBaanks/MalbolgeFree/actions/runs/37847283479) ·
[verdict and raw evidence](evidence/E20_GITHUB_RUN_20261008/04_VERDICT.md) ·
[Spanish operating guide](evidence/E20_CI_20261008/GUIA.md).

### RAM sweep: fresh boot10 VMs, targets 14–20

A second experiment measured each rung separately. Its target 20 fields,
frontier events and source/output hashes match the continuous run above.
This is reproducibility in the Zig implementation; full E20 Python parity
was not tested.

| Target | Steps | Peak RSS (GiB) | Executable time (s) |
|---:|---:|---:|---:|
| 14 | 1,594,324 | 0.0086 | 0.136 |
| 15 | 4,782,970 | 0.0244 | 0.405 |
| 16 | 14,348,908 | 0.0719 | 1.258 |
| 17 | 43,046,722 | 0.2143 | 3.926 |
| 18 | 129,140,164 | 0.6419 | 11.612 |
| 19 | 387,420,490 | 1.9255 | 35.604 |
| 20 | 1,162,261,468 | 5.7709 | 110.134 |

The collector checks resources **before building or allocating the next
rung**: at least 10 GiB available RAM and 8 GiB free disk, a budget of 60%
of available RAM, and a peak estimate with 25% margin. Address-space and
execution-time limits provide additional bounds.

It stopped before allocating target 21. Available RAM was about 14.66 GiB;
the budget was 8.80 GiB and extrapolated peak was 21.64 GiB. Separately,
dense `u32` cannot represent width 21 values, and the existing hash-storage
estimate exceeded the budget. No target 21 build or execution was performed.

[CI run](https://github.com/DannyBaanks/MalbolgeFree/actions/runs/37848647590) ·
[exact measurements CSV](evidence/RAM_SCALE_RUN_20261008/MEASUREMENTS.csv) ·
[resource gates and verdict](evidence/RAM_SCALE_RUN_20261008/04_VERDICT.md) ·
[Spanish operating guide](evidence/RAM_SCALE_CI_20261008/GUIA.md).

### Parametric boot1 sweep: targets 1–20

Twenty fresh VMs each started at width 1. The target 20 run crossed **19
frontiers**, executed **1,162,261,468 steps**, used **6,195,867,648 bytes
(5.77 GiB)** peak RSS and took **68.80 s**. Every resource gate allowed its
rung. This experiment ends at 20 by design; it did not search beyond 20 or
measure the RAM ceiling.

| Target | Widenings from 1 | Steps | Peak RSS (GiB) | Executable time (s) |
|---:|---:|---:|---:|---:|
| 1 | 0 | 2 | 0.000633 | 0.0020 |
| 2 | 1 | 4 | 0.000633 | 0.0020 |
| 3 | 2 | 10 | 0.000633 | 0.0019 |
| 4 | 3 | 28 | 0.000633 | 0.0019 |
| 5 | 4 | 82 | 0.000633 | 0.0020 |
| 6 | 5 | 244 | 0.000629 | 0.0024 |
| 7 | 6 | 730 | 0.000629 | 0.0025 |
| 8 | 7 | 2,188 | 0.000629 | 0.0024 |
| 9 | 8 | 6,562 | 0.000626 | 0.0026 |
| 10 | 9 | 19,684 | 0.000751 | 0.0031 |
| 11 | 10 | 59,050 | 0.000996 | 0.0050 |
| 12 | 11 | 177,148 | 0.001606 | 0.0106 |
| 13 | 12 | 531,442 | 0.003311 | 0.0290 |
| 14 | 13 | 1,594,324 | 0.008656 | 0.0839 |
| 15 | 14 | 4,782,970 | 0.024433 | 0.2563 |
| 16 | 15 | 14,348,908 | 0.071941 | 0.7873 |
| 17 | 16 | 43,046,722 | 0.214756 | 2.3798 |
| 18 | 17 | 129,140,164 | 0.643707 | 7.5303 |
| 19 | 18 | 387,420,490 | 1.924576 | 22.6560 |
| 20 | 19 | 1,162,261,468 | 5.770351 | 68.7993 |

**Classification: `PARAMETRIC_ASCII_OUTSIDE_BOOT_WORD`.** The loader accepts
printable ASCII values of at least 33, while a width 1 word has range 0–2.
All initial source cells therefore exceed the boot word range. These runs
measure the current parametric core, without claiming closed-word semantics
at tiny widths or shrinking an existing VM.

Targets 1–5 agree across original Zig, observed Zig, repeated observed Zig
and the Python core on the checked execution fields and output hashes.
The bounded target 5 trace records out-of-range fetched cells at active
widths 1, 2, 3 and 32 out-of-range encryption results at width 4. EOF is treated
as a deliberate sentinel, separately from ordinary memory-cell range checks.
A small harness assumption that encryption must be nonzero was corrected;
target 1 legitimately encrypts zero cells, and the initial failure is preserved.

The boot1 and boot10 target 20 sources have the same SHA-256, but their output
hashes differ. Their width histories produce different trajectories; keep
`boot_width` when comparing or combining measurements. The shorter elapsed
time here is **not** a controlled performance comparison between the two
experiments.

[CI run](https://github.com/DannyBaanks/MalbolgeFree/actions/runs/37850925619) ·
[exact measurements CSV](evidence/START1_SCALE_RUN_20261008/measurements.csv) ·
[verdict and raw evidence](evidence/START1_SCALE_RUN_20261008/04_VERDICT.md) ·
[Spanish operating guide](evidence/START1_SCALE_CI_20261008/GUIA.md).

### Larger RAM: projections, not measurements

The earlier boot10 witness's storage model gives these conservative gates,
assuming all physical RAM is available, a 60% budget and a 25% storage margin:

| Ideal RAM (GiB) | Budget (GiB) | Current storage gate ceiling | Hypothetical wider dense gate ceiling |
|---:|---:|---:|---:|
| 16 | 9.6 | 20 | 20 |
| 32 | 19.2 | 20 | 20 |
| 64 | 38.4 | 20 | 21 |
| 128 | 76.8 | 20 | 21 |

The wider dense representation has **not been implemented or tested**.
Source plus a hypothetical `u64` array alone would require at least 29.23 GiB
at 21, 87.68 GiB at 22 and 263.03 GiB at 23, before output/runtime overhead.
Target 22 therefore fails this conservative 128 GiB gate. This linear witness
would require about 561.77 TiB at 30; 128 GiB does not approach 60.

These estimates describe this witness's materialized memory. A tiny
fixed-width program can touch little memory, so there is no universal
RAM-to-Malbolge-width law. See the [projection assumptions](evidence/RAM_SCALE_RUN_20261008/04_VERDICT.md#larger-machines-storage-projections-only).

### Fixed20 versus original Nagoya

Growing from 10 to 20 does not establish equivalence with a machine booted at
fixed20. In the separate fixed20 comparison, the original Nagoya sample and
ASCII `A` echo agreed with both Free cores, but EOF echo `ubO` differed:
Nagoya emitted hex `a9`, Free Zig/Python emitted `ff`. General fixed20 Nagoya
compatibility therefore fails on the tested corpus. The runtime was not
rewritten to hide the difference.

[Counterexample, reference provenance and raw outputs](evidence/E20_CONTROLLED_20261008/03_NAGOYA_COMPARE.md).

### Verify the preserved evidence without rerunning billions of steps

```bash
python3 evidence/E20_CI_20261008/verify_ci.py evidence/E20_GITHUB_RUN_20261008
python3 evidence/RAM_SCALE_CI_20261008/verify_scale.py evidence/RAM_SCALE_RUN_20261008
python3 evidence/START1_SCALE_CI_20261008/verify_start1.py evidence/START1_SCALE_RUN_20261008
```

Each receipt preserves raw command logs, environment snapshots, result
fields, source/output hashes and instrumentation provenance. Timings include
source generation, load, VM execution and hashing, excluding compilation;
small rows also include process launch overhead. Large generated source and
stdout are represented by their generator, lengths and SHA-256, rather than
committed as gigabytes of data. Verifiers check the recorded evidence; they
do not independently execute the full computation again.

Still **NOT_DEMONSTRATED**: unbounded growth, width 21 execution, full E20
Python parity, closed-word tiny-width semantics, dynamic shrinking, general
historical-language equivalence, or a universal RAM-to-width relation.

## Historical measurements (2026-09-16 to 2026-10-01)

The measurements below retain their original dates and values. The new E20
results above supersede their earlier maximum measured width of 19.

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

This historical measurement was limited by available memory; the current
dense representation also has a width 20 element-type ceiling: to reach `w` the
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

**Historical milestone: the ladder reached 19** (2026-10-01), after the dense representation
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
| C8 `REPEATED_WIDTH_WIDENING` | **DEMONSTRATED** — committed witness `10 -> 11 -> 12` on the real VM; boot10 rungs through `20` measured, plus the explicitly parametric boot1 sweep; see the E20 receipts above |
| `UNBOUNDED_WIDTH_GROWTH` | **NOT_DEMONSTRATED** — the ladder is finite by construction and now measured to `20`; the dense path is additionally bounded at `w = 20` by the `u32` element type |
| `PARAMETRIC_BOOT1_TO_20` | **DEMONSTRATED (scoped)** — fresh boot1 targets 1–20, with ASCII outside the boot word range explicitly labelled; no closed-word tiny-width or shrinking claim |
| `FIXED20_NAGOYA_PARITY` | **FAIL (scoped counterexample)** — original Nagoya emits `a9` on EOF echo, Free Zig/Python emit `ff` |
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
