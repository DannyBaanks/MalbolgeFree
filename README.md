# Malbolge Free

```
Malbolge Classic    :   >:(
Malbolge Unshackled :   >:D
Malbolge Free       :   ^w^   (Malbolgato)
```

> **Release v1.1.0** (2026-10-02) — all milestones green or explicitly bounded.
> **Patch 2026-10-17** — Classic EOF corrected in both cores (`in` at end of
> input now assigns `3^w - 1`, so `out` after EOF emits `0xa8`, not `0xff`) and
> parity re-measured against canonical interpreters. The canonical Python
> interpreter is now **vendored** (`vendor/canonical_malbolge_py/`, hash-pinned),
> so a fresh clone measures that parity instead of skipping it. See
> [Canonical parity](#canonical-parity-2026-10-17) and ledger entries 24, 25, 26, 27, 28.
> Harness 49/49 PASS on the machine that produced the sealed evidence, and 49 PASS /
> 0 SKIP on both CI runners, where F4c measures 10 cases × 2 cores × 1 vendored oracle
> = 20 comparisons (run `39108877995`, entry 28). Where no
> canonical interpreter is usable at all the gate exits 3 and the harness prints
> `SKIP (NOT_DEMONSTRATED, missing external input)` — measured, not assumed; it
> never reports a PASS it did not obtain. Turing completeness holds
> via the documented inherited claim (`fixed` == Classic; Classic is TC per
> Scheffer 1999) — see [Turing Completeness Status](#turing-completeness-status).
> What is *not* claimed (unbounded growth, Unshackled parity, Ouroboros
> self-hosting, a new TC proof) is listed explicitly in that section.
>
> **Appended 2026-10-18 — the gate count moved 49 → 50.** The seal itself is now a
> gate: `evidence/verify_seal_manifest.py` (S1) re-hashes every path listed in
> `SHA256SUMS.txt` with `hashlib` (pure Python, because Windows runners have no
> `sha256sum`) and exits 4 on drift, a missing path, a malformed line, a duplicate or
> a path escaping the repository. Before this, the seal was verified only by hand on
> the sealing machine, so CI could publish bytes that no longer matched their recorded
> hashes. Measured on this machine at 50 PASS / 0 FAIL / 0 SKIP (manifest sha256
> `9140d359…`, 35 sealed paths, all matching); the CI figure is stated only after it
> is read from each runner's own log. Every "49" in this repository is the gate list
> as it stood through commit `be39798` — a historical measurement, not a stale claim.
> Its first run caught a real stale seal, which happened to be `tests/run_all.py`
> having just been edited to add the gate. Ledger entry 30.
>
> **Appended 2026-10-18 (later) — the sealed set grew to 40 paths.** The raw captures
> around F10 (console stdout, GNU `time` report, and both bounded trial reports with
> their falsified expectations) are annexed under
> `evidence/F10_QUINE_EPOCHAL_20261018/`, so the manifest identity printed by S1 moved
> `9140d359…` → `d45319d1…` (`entries=40 ok=40`, harness still `50 PASS / 0 FAIL / 0
> SKIP`). Every `9140d359…` quoted above and in the ledger is the manifest as of commit
> `8b97437`, not a stale claim. Ledger entry 31.
>
> **Appended 2026-10-18 (CI) — `d45319d1…` is measured green on both runners** (run
> `39118092762`, commit `2b57e9d`): ubuntu job `117647889202` and windows job
> `117647889354` each print `entries=40 checked=40 ok=40 … malformed=0`,
> `SEAL VERDICT: PASS` and `50 PASS / 0 FAIL / 0 SKIP`, over the same 50 gate names, so a
> clean clone integrity-checks the annexed captures too. Ledger entry 32. What CI still
> does *not* do is re-run F10: its checker is not in `GATES` and exits 3 without the
> third-party quine.
>
> **Appended 2026-10-18 (vendored) — that last sentence is now closed by new gates, not
> by editing it: the gate count moves 50 → 52.** `corpus/classic/quine_m281.mal` is the
> published 53 562-byte self-reproducing Classic program (`96b670b8…`), vendored
> byte-for-byte from `DannyBaanks/Malbolge-MB-Database:quine/quine_53562_m281.mb` —
> identical to `DannyBaanks/BolgeForge@5a55b9b:artifacts/candidate_m281_53562b.mal`,
> with `corpus/classic/PROVENANCE.md` recording that `python3 synthesize.py 281`
> reproduces these exact bytes from the *public* synthesizer. On it, two gates that need
> no external input: **F11** (frontier crossing + width-relative EOF, both cores, 15
> expectations, 1.26 s) and **F12** (the real 62 239 852-step halt, byte-exact
> self-reproduction on both cores, agreeing with the three engines that published that
> answer, 1:52.97). Measured locally: `52 PASS / 0 FAIL / 0 SKIP`, rc 0, and S1 prints
> `manifest_sha256=298fe800…`, `entries=53 … ok=53`. The CI figure is stated only after it
> is read from each runner's own log. F10's own checker is still deliberately outside
> `GATES` and still exits 3 without the Lutter quine; entries 29 and 32 stand as measured,
> and what changed is the *forward-looking* half: a clean clone can now re-execute this
> class of experiment for itself. Ledger entries 33 and 34.
>
> **What F11 says about the language (appended 2026-10-18).** `in` at end of input returns
> `3^padwidth - 1`: **59 048** under `pure_fixed` and **177 146** under `epochal` once the
> core has widened `10 → 11` at step 1 230 — same value on both cores. A Classic program's
> hard-coded EOF detector therefore stops meaning "end of input" under the unbounded
> profiles: `epochal` is not input-compatible with Classic, on top of the removed address
> wrap. Two programs measured, no claim about Turing completeness.

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

## Demonstrated (re-verified 2026-09-16; Classic parity re-verified 2026-10-17)

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

## Appended 2026-10-18 — the same frontier on a real program (F10)

Everything in the section above widens on witnesses that walk `c` one cell at a
time, so their crossing lands exactly on `3^w`. That is a property of those
witnesses, not of the policy. `evidence/f10_quine_epochal_20261018.json` runs a
program nobody here wrote — Matthias Lutter's Classic quine, cited as
`DannyBaanks/MalDOOM:vendor/quines/quine_lutter.malbolge` and pinned by sha256
`dca8476f…`, 59 852 bytes on disk, 59 032 cells loaded — through three profiles
of the same core:

| profile | `mem_limit` | growth | status | steps | stdout |
|---|---|---|---|---:|---|
| `classic` | `3^10` (wrap) | `fixed` | `HALTED` | 69 547 437 | 59 852 bytes whose sha256 equals the program's: it reproduces itself |
| `pure_fixed` | `null` | `fixed` | `HALTED` | 6 521 | 1 byte |
| `epochal` | `null` | `epochal` | `HALTED` | 8 761 | nothing; widened `10 -> 11` once |

What that measures, and what it does not:

- **The frontier is reached at step 1230, not at 59050.** `d` is *assigned*
  `3^10 = 59049` (the earliest Zig trace divergence `classic` vs `pure_fixed` is
  step 1229). The sentence above the ladder table — "to reach `w` the pointer must
  walk to `3^(w-1)`" — therefore describes the cost of the synthetic witnesses, not
  a requirement of the rule. That text stays as published; this bullet is the
  correction, appended.
- **Removing the address wrap is alone enough to stop being Classic.** `pure_fixed`
  has no growth policy whatsoever and the quine no longer reproduces, so the epochal
  widening is not what silenced it. Stored and addressed memory images are identical
  for all three profiles before execution (`c455d288…`, no first difference), so the
  divergence is addressing during execution, not `load`.
- **Invariant P1 holds on real code**: the earliest `pure_fixed` vs `epochal` trace
  divergence is step 1246, after the widening at step 1230 — history preserved until
  the first `WIDEN`.
- **The raw captures are preserved, including the false starts** (appended
  2026-10-18, ledger entry 31): `evidence/F10_QUINE_EPOCHAL_20261018/` holds the
  sealed run's console output, its GNU `time` report, and both bounded trial reports
  that were run before it — the 15 000-step one with 5 falsified expectations of 9,
  the 1 000 000-step one with 2 of 10. They are byte-for-byte copies, sealed in
  `SHA256SUMS.txt`, and `PROVENANCE.md` there says which falsifications are budget
  artifacts rather than behavioural results. Nothing in the annex adds a claim, and
  F10 remains evidence rather than a gate, so it also does not move the count: the
  `49/49` above stays a historical measurement and the gate list is 50.

- **Not claimed**: that one program generalises to the corpus; that `epochal` is or
  is not Turing-complete (the claim is compatibility with Classic); CI reproducibility
  of F10 — the input is third-party and deliberately not vendored, so a fresh clone of
  this repository exits 3 (`NOT_DEMONSTRATED, missing external input`). F10 is
  evidence, not a gate: it is absent from the `GATES` list in `tests/run_all.py`, so
  the `49/49` figure at the top of this file is unchanged by it. Full facts:
  `docs/HONESTY_LEDGER.md` entry 29 and
  `evidence/F10_QUINE_EPOCHAL_20261018.hashes.json`.

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
| `CLASSIC_PARITY_CANONICAL` (11 cases × 2 cores, 2 oracles here) | **DEMONSTRATED** (2026-10-17) — `evidence/compare_f4_canonical.py` diffs both cores byte-a-byte against canonical implementations: 22 (case × core) verdicts, **44** stdout SHA-256 comparisons on this machine (2 oracles), 20 on CI (1 vendored oracle, no external `hello_world.malbolge`). Includes the four EOF witnesses. Report: `evidence/f4c_canonical_parity_vendored_20261017.json` |
| `CLASSIC_PARITY_ZIG` (6/6 corpus vs `engine.zig`) | **SUPERSEDED — measured divergence** (2026-10-17). The old oracle `Malbolge-Translator/zig/src/engine.zig` assigns `0xFFFF` at EOF, the same non-canonical family our core used to assign; 4/6 programs now differ. See `evidence/f4_engine_zig_divergence_20261017.json` and `docs/HONESTY_LEDGER.md` entry 24 |

### Canonical parity (2026-10-17)

EOF was wrong in both cores: `in` at end of input stored a sentinel
(`-1` in Python, `u128::max` in Zig) that only `crazy` normalized, so `out` after
EOF emitted `0xff` where the 1998 interpreter emits `3^10 - 1 = 59048` → `0xa8`.
An external audit measured it; the fix and the re-sealing are ledger entry 24, and
the vendoring of the canonical oracle below is ledger entry 25.

Parity is therefore measured against **canonical** implementations, never against
a peer that shares our convention:

- `vendor/canonical_malbolge_py/malbolge.py` — a clean-room Classic interpreter
  with `EOF_VALUE = 59048`, **vendored verbatim** from
  [`DannyBaanks/MALBOLGE`](https://github.com/DannyBaanks/MALBOLGE) at commit
  `bf4d6fa` (MIT). Provenance and the reason for vendoring:
  `vendor/canonical_malbolge_py/PROVENANCE.md`; the source repo's MIT `LICENSE`
  text is copied verbatim next to it.
- `reference_interpreter_classic` — Olmstead's C (`if ( x == EOF ) a = 59048;`),
  compiled natively from `reference_interpreter.c`. Kept **outside** the repo; used
  when reachable or when `MALFREE_REFERENCE_CLASSIC` points at it.

The vendored oracle is hash-pinned inside the gate. If its SHA-256 stops matching,
the gate exits **4** with `F4C_VENDORED_ORACLE_DRIFT`: a silently edited oracle
producing a green parity verdict is the exact failure mode that hid this bug for a
month, so drift is a hard failure — never a skip, never a PASS.
That pin is also why `.gitattributes` says `* -text`: the Windows runners default to
`core.autocrlf=true`, and at `7e6eb5d` they handed the gate a CRLF copy of the oracle.
The pin disagreed and CI failed loudly instead of certifying a program nobody reviewed
(ledger entry 26). The same default then corrupted the gate's own case manifest — a
stray `\r` reached the Zig core as an input byte, producing a `MISMATCH` that was our
harness rather than Classic, and was fixed by writing the manifest as bytes and trimming
a trailing CR in the driver. Neither time was the core touched (ledger entry 27).
Both defects fixed, run `39108877995` is green on ubuntu **and** windows with F4c
measuring `10 cases x 2 cores x 1 oracle = 20 stdout-hash comparisons` and
`49 PASS / 0 SKIP` on each runner — so this claim no longer depends on one workstation
(ledger entry 28).

Comparisons are on stdout bytes only: the C oracle exposes no step count.

Before trusting any interpreter as an oracle, test it on the EOF witness itself —
the property this bug turned on: `in,out,halt` on empty stdin must emit `0xa8`
(`59048 % 256`). An interpreter that emits `0xff` shares the sentinel family and
cannot falsify it; that is how the old F4 oracle let the bug sit under a green
seal. Note that this repository still ships `evidence/malbolge.py`, an older
interpreter that assigns `a = -1` at EOF — the gate never imports it, and pointing
`MALFREE_MALBOLGE_REFERENCE` at it would defeat the purpose.

To add an oracle of your own:

```bash
export MALFREE_REFERENCE_CLASSIC=/path/to/reference_interpreter_classic  # ELF/binary
export MALFREE_MALBOLGE_REFERENCE=/path/to/canonical/malbolge.py         # extra, unpinned
py evidence/compare_f4_canonical.py
```

### The old F4 oracle (2026-09-12, oracle rebuilt 2026-10-01)

`evidence/compare_f4.py` is kept, but it is **no longer a gate**. Two findings on
2026-10-17:

1. Its oracle was a Windows `.exe` produced by hand and never committed, so
   outside Danny's machine F4 could not run at all. It was replaced by
   `zig/src/parity_check.zig` in the sibling `Malbolge-Translator` repo, tracked
   with its corpus (commit `0c8a56b`) and built natively:

   ```bash
   zig run --dep engine=engine -Mroot=src/parity_check.zig -Mengine=src/engine.zig
   ```

   run from that repo's `zig/` directory. It imports `engine.zig`, never
   `malbolge_free.zig`, so it stayed an independent implementation of Classic
   rather than a copy of the runtime under test. Independence was real; canonicity
   was not — independence from a bug is not agreement with the language.
2. `compare_f4.py` always exited 0, even after printing `=> MISMATCH`, so
   `tests/run_all.py` printed `PASS: F4 Classic parity` over a failing comparison.
   The exit code now follows the verdict.

`compare_f4.py` also verifies that both repos embed a byte-identical corpus and
refuses to report parity if they ever diverge (`F4_CORPUS_DIVERGENCE`, exit 4).

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

# canonical Classic parity (uses the vendored hash-pinned oracle; adds
# MALFREE_REFERENCE_CLASSIC when Olmstead's C is reachable; exit 3 = no usable
# oracle at all, exit 4 = the vendored oracle drifted from its pin)
py evidence/compare_f4_canonical.py

# seal integrity (gate S1, also run in CI): every path listed in SHA256SUMS.txt
# against the bytes actually on disk. Pure Python, so it behaves identically on
# Windows runners, which have no `sha256sum`. exit 4 = drift, missing path,
# malformed line or path escaping the repository — integrity failures, never a
# skip; there is no exit 3 branch because this gate has no external input.
py evidence/verify_seal_manifest.py

# old F4 measurement (engine.zig oracle — kept as a record, no longer a gate)
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
to Classic Malbolge — F4c canonical parity, 22 (case × core) verdicts against the
hash-pinned vendored oracle plus Olmstead's C where available, reproducible from a
fresh clone (see [Canonical parity](#canonical-parity-2026-10-17)) — and Classic is
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
