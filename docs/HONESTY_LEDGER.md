# HONESTY LEDGER

What we got, how we got it, and where we know we cheated.

## VARIABLE WIDTH IS NOT INFINITY

The symbol `w` denotes the active width. At every executed step it has a
concrete finite integer value (10, then 11, in the recorded run). Current
evidence demonstrates exactly the tested frontier transition (`10 -> 11`,
`tests/t_frontier_moment.zig`), **not** an infinite sequence of widenings and
not even a second one: the witness run halts at step 70076, long before the
`3^11` frontier. Nothing in this repo claims otherwise. Earlier drafts used
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
