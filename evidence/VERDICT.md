# VERDICT — MALBOLGE_FREE_V0

## Claims table

(Claim numbers kept from the original brief. C7/C8 renamed 2026-09-05: the
old names `GROW_ON_DEMAND_WIDTH` / `TRUE_OMEGA_SEMANTICS` are retired because
the width is an ordinary finite variable `w`, and the omega naming suggested
infinity claims this project does not make.)

| Claim | Status |
|---|---|
| C0 SINGLE_PARAMETRIC_CORE | **DEMONSTRATED** — one core, no `k==10/19` switch, verified by inspection + full corpus run |
| C1 CLASSIC_PARITY_K10 | **RECORDED 6/6, NOT REPRODUCIBLE TODAY** — `evidence/f4_classic_parity.json` records 6/6 equal sha256; live re-run 2026-09-05 gives 4/6 (hello.mal, reproducer.mal). Root cause located: Zig `crazy` masks the accumulator with bitwise `&` instead of `mod`. Fix identified, not applied in this pass. See `f4_classic_parity_rerun_20260905.json` and `docs/HONESTY_LEDGER.md` #8 |
| C2 UNSHACKLED_PARITY_K19 | **NOT_DEMONSTRABLE** — original `Unshackled.c` uses `srand(time(NULL))`, so reference parity is nondeterministic by construction. We can reproduce the deterministic subset only. |
| C3 ARBITRARY_FINITE_K | **DEMONSTRATED** — widths 10, 11, 12, 19, 20, 23, 26 all load + fill correctly, and `src/malbolge_free.zig` runs the corpus k=10 (wrap) and k=20 (no wrap) |
| C4 NO_FIXED_COMPILED_MAX_ADDRESS | **DEMONSTRATED** — there is no `MAX_ADDR`. The `mem_limit` becomes `null` precisely in unbounded mode, and nothing lazily resets memory to a 3^k window |
| C5 LEGAL_CROSSING_3_POW_19 | **DEMONSTRATED** — `evidence/f7_witness.zig`, program "('& %$") => movd-chain reaches d=1,743,392,169 > 3^19=1,162,261,467. Re-run 2026-09-05: `cfg=k20_fixed status=MAX_STEPS steps=50 max_addr=1743392210 >3^19=true`. See also `f7_python_check.py`. |
| C6 WIDTH_EXTENSION_CONSISTENCY | **DESTROYED** — `rotate(v, k) % 3^k != rotate(v, k+1) % 3^k` unless `v % 3 == 0`. Numerics: 33% consistency over 27 samples on w=3. `crazy` is consistent 100% of the time (the op is purely tritwise and padding with zeros is already neutral). Re-verified 2026-09-05 via `f8_check.py` |
| C7 FRONTIER_WIDTH_WIDENING | **DEMONSTRATED** — the tested `10 -> 11` transition: `tests/t_frontier_moment.zig` prints `WIDEN step=59050 c=59049 d=59049 old_w=10 new_w=11`, exactly one event, prior trace untouched. Re-verified 2026-09-05 |
| C8 REPEATED_WIDTH_WIDENING | **NOT_DEMONSTRATED** — no run has crossed a second frontier. The witness halts at step 70076 (< 3^11 = 177147). Do not extrapolate the C7 result into "widens forever". |
| C9 CLASSIC + UNSHACKLED -> FREE | **DEMONSTRATED** in both readings |
| C10 TURING_COMPLETENESS | **NO_NEW_CLAIM** |

## Verdict

`FREE_PARAMETRIC = DEMONSTRATED`

`FRONTIER_WIDTH_WIDENING (10 -> 11) = DEMONSTRATED` — single transition,
anchor intact, past not replayed

`REPEATED_WIDTH_WIDENING = NOT_DEMONSTRATED`

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
py    evidence/compare_f4.py            # classic-parity checker (pyref vs zig)
zig run evidence/run_f4.zig             # corpus-on-Zig emitter
```
