# HONESTY LEDGER

## Evidence update — 2026-10-08: epochal reaches 20, fixed20 EOF differs

`EPOCHAL_19_TO_20 = DEMONSTRATED_SCOPED`: GitHub-hosted Ubuntu run
37847283479, measured runtime/harness commit ac94be2. One VM initialized
free_pure/epochal at 10 with no wrap called the real vm.run loop once for
1,162,261,468 steps. Ten sparse events include 19→20 at step 1,162,261,468,
c=d=1,162,261,467. Final width20, growth10, c=d=1,162,261,468,
1,162,262,480 cells, 383,299,003 output bytes (SHA-256 preserved).
Elapsed executable time 109.87 s, peak RSS 6,197,026,816 bytes (5.77 GiB).
The gate calibrated rung 18, reserved a 25% margin, and limited address space
to 60% of measured MemAvailable. Core source is unchanged; an exact generated
copy adds only WIDEN observation around frontierTrigger. Original/observed
small-run fields and source/stdout hashes match; instrumented repeat agrees.
Tests run on both copies. Full E20 remains a Zig single-engine measurement.

Evidence: [E20 verdict](../evidence/E20_GITHUB_RUN_20261008/04_VERDICT.md),
downloaded raw artifact, original manifests and local hash verification.
The earlier local resource block remains a valid separate negative record.
`FIXED20_NAGOYA_PARITY = FAIL`: accepted INPUT/OUTPUT/HALT source `ubO`
at EOF emits a9 in original Nagoya and ff in Free Zig/Python. Official hello20
and ASCII-A echo have stdout parity. No global equivalence, no reference
state/step parity, no unbounded width claim. Earlier entries are historical.

What we got, how we got it, and where we know we cheated.

## VARIABLE WIDTH IS NOT INFINITY

The symbol `w` denotes the active width. At every executed step it has a
concrete finite integer value (10, then 11, then 12, ... in the recorded
runs). Current evidence demonstrates a **finite ladder**: `10 -> 11 -> 12` on
the committed witness, and every rung up to `19` measured on the real VM loop
(entries 14-16 below). It does **not** demonstrate an infinite sequence of
widenings. (Entry 7 records the earlier state, when the witness halted at
step 70076 and only one widening was exercised.) Nothing in this repo claims
otherwise. Earlier drafts used
the symbol `ω` for the composition idea; that notation was retired on
2026-09-05 because it suggested infinity/ordinal semantics that Malbolge Free
does not make.

| # | Claim | Evidence | Cheat check |
|---|---|---|---|
| 1 | Core is parametric without k-special-cases | `src/malbolge_free.zig` has no `if (k == 10) ...` | Search: `if.*k ?= 10` or `19` — clean |
| 2 | Classic parity on corpus | `evidence/f4_classic_parity.json` (6 programs, sha256 match) | stdout sampled, all 6 PASS |
| 3 | Lazy fill == eager fill | `t_phase23.py` 4 widths, 197 cells each | Python-side check pre-Jason update; fresh 59049-cell verifications under k=10..20 can't be brute-forced. I claim parity up to where I measured |
| 4 | Period-6 lazy fill is correct | `evidence/crazy_periodicity.py`, verified w=10,19,20,26 | NOT universally proven; the shortcut is a *consequence of observed* fixed-point stability |
| 5 | LEGAL_3^19_CROSSING | `f7_witness.zig` — `('&%` runs, max_addr=1743392210 | movd-set d takes *any* value; reading mem[d=1743392210] is lazy-legal (not an explicit write). --γ**
| 6 | Rotation inconsistency at k vs k+1 | `f8_check.py` — rotate ~33% consistent, crazy 100% | rotate isn't extension-consistent; growth under `pad_to_padwidth` is *safe only if width never fires during seeds-lazy-fill path* |

## Re-audit entries (2026-09-05)

| # | Claim | Evidence | Cheat check |
|---|---|---|---|
| 7 | Single frontier widening `10 -> 11` reproduces | `zig run tests/t_frontier_moment.zig` → `WIDEN step=59050 c=59049 d=59049 old_w=10 new_w=11`, `widen_events=1`, `final padwidth=11` (run twice, identical) | one transition only; the run halts at step 70076 < 3^11, so a second widening is *not* exercised |
| 8 | Classic parity 6/6 **was recorded**, but is **not reproducible today** | committed `evidence/f4_classic_parity.json` says all_match=true; live `py evidence/compare_f4.py` on 2026-09-05 gives 4/6 (hello.mal, reproducer.mal mismatch) — preserved at `evidence/f4_classic_parity_rerun_20260905.json` | root cause located by step trace: the Zig `crazy` op masks the accumulator with a bitwise `a & (3^w - 1)` instead of `a mod 3^w`; hello.mal step 3 turns `a=29524` into `25088`. Fix = one line (`mod`), **not applied in this pass** because it changes runtime behavior and that call belongs to the owner |
| 9 | `tests/t_frontier_trigger.zig` did not compile | zig 0.16.0 error: `no field named 'steps' in MalbolgeCore.stats` | fixed identifier (`res.steps`) + reworded print so it says what is actually known; a compile-only fix, zero semantic change |
| 10 | `tests/f4_corpus.zig` did not compile | zig 0.16.0 error: `std.fmt.fmtHexLower` no longer exists | swapped to `std.fmt.bytesToHex` (same usage as `run_f4.zig`); compile-only fix |
| 11 | `tests/f4_classic.zig` compiles but **fails** | expects `"Hello, world."`, gets garbage bytes | same root cause as #8 (bitwise mask in `crazy`); left failing on purpose — it is the failing-test evidence for the bug |
| 12 | `tests/t_phase23.py` tail "should not crash" crashes | `MemoryError` in `MalbolgeCore._cell` chain walk, growth_policy=`pad_to_padwidth` with an injected 7-trit cell at addr 200 | the *Python* core has no period-6 lazy shortcut, and the `pad_to_padwidth` route throws `d` to a giant address that `_cell` then walks cell-by-cell. All earlier asserts in the file PASS (lazy==eager k∈{10,11,12,19}, k=10 == Classic 59049 eager fill); only the destroyed-policy tail dies |
| 13 | `evidence/f8_check.py` exits non-zero | its final `assert` demands *crazy* be inconsistent too | the printed numbers (rotate 9/27 = 33.3%, crazy 729/729 = 100%) are the evidence and they reproduce; the assert's wording contradicts the docs. Left untouched — noisy exit, truthful numbers |

## Re-audit entries (2026-09-16) — the ladder

| # | Claim | Evidence | Cheat check |
|---|---|---|---|
| 14 | Repeated widening `10 -> 11 -> 12` on the real VM loop | `tests/t_m5_full_vm.zig` runs the 190000-char witness through `vm.run`: 2 widenings, `padwidth=12`, `final_c=190000`; stopping at step 177147 leaves `padwidth=11` | `t_m5_repeated.zig` and `t_frontier_moment.zig` step the VM by hand (they skip `crazy`/`out` and encryption), so the full-loop test was added. `f9_repeated_frontier.json` had a 63-char `witness_sha256` (one `2` missing); corrected to the real hash `3370003c...3013a57` |
| 15 | Ladder up to `16` | `evidence/M5_LADDER_SCALE/run_ladder_scale.py 13 14 15 16`: each rung PASS from a fresh `w=10`, widenings 3/4/5/6, results in `results.json` | superseded for rungs 17+ by entry 17; the hash-map ceiling it describes is real but no longer the binding one. Zig only: the Python oracle has no `epochal` policy |
| 17 | Ladder up to `19` + dense representation | `run_ladder_scale.py --dense --label linux-14gib-dense 17 18 19`: PASS, widenings 7/8/9, steps 43,046,722 / 129,140,164 / 387,420,490, `padwidth` 17/18/19, peak RSS 1.92 GiB for all three (Linux x86_64, 14.8 GiB). Rows tagged `repr=dense` in `results.json` | the `~33 bytes/cell` hash map was the wall, not the maths: the materialised range `[0, program_len+12)` is now a flat `u32` array (~4 B/cell) with the map keeping only out-of-range writes. **Off by default**; equivalence asserted field-by-field in `tests/t_dense_differential.zig` (4/4). Rung 17 steps/padwidth/growth identical across both representations, so this changed cost, not measurement. Dense **refuses** `w >= 21` (3^21 overflows u32), so that path is structurally bounded at `w=20` — a ceiling, not a claim. Single engine: Python oracle has no `epochal` |

| 23 | M2 bootstrap: full byte coverage | `tools/hell_materialize.py` with `rotcombine` (A := rot(crazy(A,v))): 256/256 bytes reachable, verified `synthesize(180) -> 180` (was in the 154..208 gap that the 201/256 model couldn't reach) | the earlier 201/256 was because the BFS only had rotload+crazy; adding ONE operation closes the gap. HeLL emission: `CRAZY v` + `Rot ?-` (two Classic instructions) |
| 22 | `TURING_COMPLETENESS_INHERITED` | `docs/TURING_COMPLETENESS_INHERITED.md`: `fixed` == Classic (F4 6/6 reproducible) and Classic is TC (Scheffer 1999). This is the ROADMAP M6's explicitly named third route, NOT a new proof | `TURING_COMPLETENESS_NEW_CLAIM` stays NOT_DEMONSTRATED. The assisted backend is a separate machine (69-79) and is NOT part of this claim |

| 21 | M6 boundary: what 8 Classic opcodes can/cannot do | `tests/t_m6_eight_opcode_boundary.zig` (4/4). `malformed_assisted_source_is_rejected`: strict profiles refuse auxiliary opcodes in source, so 'no assisted ISA' is falsifiable. **Bounded negative:** exhaustive search (depth<=3, 156 templates, x2 inputs) finds **0** programs that move `d` by input using only the 8 opcodes, while the **same** search on `free_assisted` finds witnesses (`d=29580` vs `d=130`); depth<=5 also 0. **Control asserted as a test** so the negative cannot be vacuous. Not a proof of impossibility, and it does NOT move `TURING_COMPLETENESS_NEW_CLAIM`, which stays NOT_DEMONSTRATED | what it adds is a reason: `d` is written only by op 40, so pointer-by-data needs a data-dependent jump; the eight-opcode profile lacks that in the searched space, which is exactly why the BF backend emits `TAPE_BASE`/`INC`/`D_REWIND`. Also note the existing M6 differential is between two profiles of ONE runtime, not two independent implementations, so it never met the acceptance criterion. Details in `docs/M6_EIGHT_OPCODE_BOUNDARY.md` |

| 20 | M0 EOF + precision, and the free-pure vertical slice | `tests/t_m0_eof_precision.zig` (10/10): EOF->out = `0xff`, sticky EOF, EOF vs real byte, EOF normalises to `3^w-1` inside crazy, sentinel visible in the trace, rot unaffected; `pow3` exact at 0,1,2,10,19,20,26,40,79,80. `tests/t_free_pure_vertical_slice.zig` (3/3): fixture found by exhaustive enumeration, output depends on input, `assisted_opcodes=0`, `lock_noencrypt=false`, `encrypted>0`, prefix identical to Classic, and a frontier crossed with no auxiliary ISA | **two precision hazards pinned, not fixed:** `pow3(n>=81)` returns `u128::max` instead of failing, and the `width<=80` guard is a `std.debug.assert` that `ReleaseFast` strips. Fixing either would change the public contract, so both are recorded as accepted limitations in SPEC_V1 §3. The vertical slice closes the M4 gate of the "verdadero" plan: the previously demonstrated backend was `free-assisted` (opcodes 69-79), which is a different machine |

| 19 | `CLASSIC_PARITY_ZIG` reproducible | `evidence/compare_f4.py` builds the sibling oracle natively (`zig run`, no `.exe`/wine) after `Malbolge-Translator` 0c8a56b tracked `zig/src/parity_check.zig` + `zig/corpus/*.mal`; 6/6 match, `all_match: true` | the oracle had been a hand-built untracked `.exe`, so F4 was `NOT_DEMONSTRATED` outside one machine; a fresh clone of both repos now reproduces it. New guard: `F4_CORPUS_DIVERGENCE` (exit 4) refuses parity if the two repos' corpus copies ever differ, because a verdict across different programs would be a silent false OK. Still limited to the 6-program corpus, and the two engines share a compiler but not an implementation |

| 18 | `EPOCHAL_PYTHON_PARITY` | `evidence/compare_epochal.py`: Zig core vs `src/malbolge_core.py` on 3 witnesses (3 widenings, 3 widenings, and a real `w=10 -> 11` crossing). Agree on status, steps, `padwidth`, widening count, final `c`/`d`, encrypted cells and stdout SHA-256; determinism and below-frontier degeneration also checked. Gate in `tests/run_all.py` | the Python core had **no** `epochal` at all before this, so the whole ladder rested on one engine. Negative control: disabling the Python frontier trigger makes all 3 cases fail, so the gate is not a rubber stamp. Python refuses `epochal` with a wrapping address space (the frontier would be unreachable). **Scope:** cross-checked on witnesses up to 60k steps / 1 widening at `w=10`, **not** on the 129M-step `w=19` run, which remains a single-engine measurement |

| 16 | E10 -> E19 toy epoch ladder | `epoch_ladder/` (copied from the sibling MALBOLGE lab, byte-identical fixture): `LADDER PASS`, offset formula `first_failure: null` for `k=11..18`, 7 unit tests | **toy**: E11-E18 are not historical languages; only state transport and the positional codec cross the ladder. `crazy`, rotation, encryption and jumps at intermediate widths are not demonstrated. It is not the same claim as entries 14-15 (fixed dimension per epoch vs `w` changing inside one run) |

## Legitimate ambiguity on C3/C7

The lazy fill is seeded by the last two "program" values, not by rounds. "lazy
cells = crazy(mem[i-1], mem[i-2])" — standard. No weasel. But the periodicity
proof stage: the chain after program_len+2 exhibits period 6 for the *specific
patterns in our corpus*. Could be a contraction — but the practical outcome is
verified on the corpus. We accept "period 6 evidenced, not proven for all
seeds" as an outstanding bound, not a bug.

## Where we did NOT cheat

- No `--patch memory` tail. The core never writes `memory[d] = value_ge_3^19`,
  only `movd` reads.
- Rot/growth are invocations of the operand widths, not direct assignments from
  host constants.
- The `('&%` witness runs fully and reports the crossing without instrumentation
  white RNA.
