# VERDICT — MALBOLGE_FREE_V0

## Claims table

(Claim numbers kept from the original brief. C7/C8 renamed 2026-09-05: the
old names `GROW_ON_DEMAND_WIDTH` / `TRUE_OMEGA_SEMANTICS` are retired because
the width is an ordinary finite variable `w`, and the omega naming suggested
infinity claims this project does not make.)

| Claim | Status |
|---|---|
| C0 SINGLE_PARAMETRIC_CORE | **DEMONSTRATED** — one core, no `k==10/19` switch, verified by inspection + full corpus run |
| C1 CLASSIC_PARITY_K10 | **DEMONSTRATED** — 2026-10-17: `evidence/compare_f4_canonical.py` matches BOTH cores byte-a-byte against canonical interpreters: 22 (case × core) verdicts, 44 stdout-hash comparisons on the sealing machine (Olmstead's C `reference_interpreter_classic` + the vendored `vendor/canonical_malbolge_py/malbolge.py`, `EOF_VALUE = 59048`), 20 on CI (vendored oracle only). Report: `evidence/f4c_canonical_parity_vendored_20261017.json`. The earlier reading of this claim — "matches the independent Zig oracle" — is superseded: that oracle (`Malbolge-Translator/zig/src/engine.zig`) assigns `0xFFFF` at EOF, so it agreed with our own EOF bug. Independence is not canonicity; the divergence is recorded in `evidence/f4_engine_zig_divergence_20261017.json`. |
| C2 UNSHACKLED_PARITY_K19 | **SPLIT — see both readings.** (a) Parity with the original `Unshackled.c`: **NOT_DEMONSTRABLE** by construction, because that program calls `srand(time(NULL))` (`MALDOOM/vendor/Unshackled.c:585`) and a nondeterministic peer falsifies nothing. (b) Parity with a *deterministic fixed-3^19 machine*: **DEMONSTRATED in a stated scope** (2026-10-18) — gate F13 (`evidence/compare_unshackled_k19.py`) agrees three ways with `MalbolgeLispSlop/src/bolge19.zig` on `end=3^19`, EOF `3^19-1`, the wrap modulus, the eight dispatch opcodes and 19-trit `crazy` (200 000 seeded pairs, 0 mismatches), and *disagrees as predicted* on `rot` (the reference rotates 18 trits, we rotate 19; divergence set is exactly `{v : v%3 != 0}`, the same shape as C6). Scope: region 0 only (`c < 3^18`; regional dispatch divergence V1 across regions 1 and 2 is measured by gate F14 in `evidence/f14_region_offsets_20261018.json`: 17/17 MATCH, confirming the $+117$/$+140$ offsets), images of 3-4 instructions, and the encryption alphabet / domain guard divergence V3 is measured by gate F15 in `evidence/f15_encryption_cascade_20261018.json`: 21/21 MATCH, confirming canonical cycle isomorphism over $[33, 126]$ and domain guard divergence over $[0, 32] \cup [127, 140]$. Expectations pre-registered in `docs/F13_UNSHACKLED_K19_PREGISTRATION.md`, `docs/F14_REGION_OFFSETS_V1_PREGISTRATION.md`, and `docs/F15_ENCRYPTION_CASCADE_V3_PREGISTRATION.md`; measurements in `evidence/f13_unshackled_k19_20261018.json`, `evidence/f14_region_offsets_20261018.json`, and `evidence/f15_encryption_cascade_20261018.json`. The earlier single-line reading of this claim ("NOT_DEMONSTRABLE, full stop") is superseded: it conflated (a) with (b). |
| C3 ARBITRARY_FINITE_K | **DEMONSTRATED** — widths 10, 11, 12, 19, 20, 23, 26 all load + fill correctly, and `src/malbolge_free.zig` runs the corpus k=10 (wrap) and k=20 (no wrap) |
| C4 NO_FIXED_COMPILED_MAX_ADDRESS | **DEMONSTRATED** — there is no `MAX_ADDR`. The `mem_limit` becomes `null` precisely in unbounded mode, and nothing lazily resets memory to a 3^k window |
| C5 LEGAL_CROSSING_3_POW_19 | **DEMONSTRATED** — `evidence/f7_witness.zig`, program "('& %$") => movd-chain reaches d=1,743,392,169 > 3^19=1,162,261,467. Re-run 2026-09-05: `cfg=k20_fixed status=MAX_STEPS steps=50 max_addr=1743392210 >3^19=true`. See also `f7_python_check.py`. |
| C6 WIDTH_EXTENSION_CONSISTENCY | **DESTROYED** — `rotate(v, k) % 3^k != rotate(v, k+1) % 3^k` unless `v % 3 == 0`. Numerics: 33% consistency over 27 samples on w=3. `crazy` is consistent 100% of the time (the op is purely tritwise and padding with zeros is already neutral). Re-verified 2026-09-05 via `f8_check.py` |
| C7 FRONTIER_WIDTH_WIDENING | **DEMONSTRATED** — `tests/t_frontier_moment.zig` prints `WIDEN step=59050 c=59049 d=59049 old_w=10 new_w=11`; the same witness continues through the C8 event. |
| C8 REPEATED_WIDTH_WIDENING | **DEMONSTRATED** for two frontiers: `10→11` at step 59050 and `11→12` at step 177148. Evidence: `f9_repeated_frontier.json`, `tests/t_m5_full_vm.zig`. Rungs up to 16 measured on the real VM (2026-09-16, `M5_LADDER_SCALE/results.json`); rungs 17/18/19 measured 2026-10-01 with the dense representation (`--dense`, label `linux-14gib-dense`, peak RSS 1.92 GiB). Step counts identical to the hash predictions. Do not extrapolate beyond 19. |
| C9 CLASSIC + UNSHACKLED -> FREE | **DEMONSTRATED** in both readings |
| C10 TURING_COMPLETENESS | **INHERITED** — `fixed` == Classic (F4c canonical parity: 22 case×core verdicts, all matching) and Classic is TC (Scheffer 1999). See `docs/TURING_COMPLETENESS_INHERITED.md`. A NEW proof stays NOT_DEMONSTRATED |

`EPOCHAL_PYTHON_PARITY` = **DEMONSTRATED** (2026-10-01). `src/malbolge_core.py` now
implements the `epochal` policy (frontier trigger before the step touches memory,
`padwidth` in crazy/rotate, frozen 12-cell tail) and `evidence/compare_epochal.py`
diffs it against the Zig core: status, steps, `padwidth`, widening count, final
`c`/`d`, encrypted cells and stdout SHA-256 all agree on witnesses with 3, 3 and 1
widenings. Negative control: disabling the Python trigger fails all 3 cases. Scope:
cross-checked up to 60k steps, not on the 129M-step `w=19` ladder.

M6 progress: the executable BF reference now has configurable tape bounds,
explicit EOF and pointer errors, and per-instruction traces. This is
infrastructure only; no BF interpreter has yet been executed inside Malbolge
Free. See `tests/t_m6_bf_reference.zig` and `docs/TURING_COMPLETENESS.md`.

## Verdict

`FREE_PARAMETRIC = DEMONSTRATED`

`FRONTIER_WIDTH_WIDENING (10 -> 11) = DEMONSTRATED` — single transition,
anchor intact, past not replayed

`REPEATED_WIDTH_WIDENING = DEMONSTRATED (10→11→12)`

## The witness

`('&%$" movd chain (from `evidence/f7_witness.zig` and checked by `f7_python_check.py`)

```
step=0 c=0 d=0 op=40 movd => d=40  (mem[0]='(')
step=1 c=1 d=41 movd => d=mem[41]=crazy(mem[40], mem[39], w=20) — lazy chain — = 3^19-sized
step=2 c=2 d=1743392165 movd => d=mem[1743392165]
  --- address beyond 3^19 touched ---
```

## What we don't claim

- That `pad_to_padwidth` mode is the original Unshackled build
- That the 6-periodicity of crazy-chain has been proved in algebra — verified numerically for the mentioned widths+seeds; the lazy-cell shortcut is only activated once the chain is measured to be periodic, with evidence in `evidence/crazy_periodicity.py`

## Reproduce

```
cd malbolge-free
zig run evidence/f7_witness.zig         # witness crossing (k=20 fixed + pad)
zig run evidence/f7_cross.zig           # boundary sweep (k=10 vs k=20)
py    evidence/f7_python_check.py       # simulated trace of the witness (movd chain)
py    evidence/compare_f4_canonical.py  # CANONICAL Classic parity (vendored pinned oracle; exit 3 = none usable, exit 4 = oracle drift)
py    evidence/compare_f4.py            # old engine.zig measurement (record, not a gate)
zig run evidence/run_f4.zig             # corpus-on-Zig emitter
```
