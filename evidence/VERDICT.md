# VERDICT — MALBOLGE_FREE_V0

## Claims table

(Claim numbers kept from the original brief. C7/C8 renamed 2026-09-05: the
old names `GROW_ON_DEMAND_WIDTH` / `TRUE_OMEGA_SEMANTICS` are retired because
the width is an ordinary finite variable `w`, and the omega naming suggested
infinity claims this project does not make.)

| Claim | Status |
|---|---|
| C0 SINGLE_PARAMETRIC_CORE | **DEMONSTRATED** — one core, no `k==10/19` switch, verified by inspection + full corpus run |
| C1 CLASSIC_PARITY_K10 | **DEMONSTRATED 6/6** — live F4 rerun matches the independent Zig oracle after correcting `crazy` to use modulo. |
| C2 UNSHACKLED_PARITY_K19 | **NOT_DEMONSTRABLE** — original `Unshackled.c` uses `srand(time(NULL))`, so reference parity is nondeterministic by construction. We can reproduce the deterministic subset only. |
| C3 ARBITRARY_FINITE_K | **DEMONSTRATED** — widths 10, 11, 12, 19, 20, 23, 26 all load + fill correctly, and `src/malbolge_free.zig` runs the corpus k=10 (wrap) and k=20 (no wrap) |
| C4 NO_FIXED_COMPILED_MAX_ADDRESS | **DEMONSTRATED** — there is no `MAX_ADDR`. The `mem_limit` becomes `null` precisely in unbounded mode, and nothing lazily resets memory to a 3^k window |
| C5 LEGAL_CROSSING_3_POW_19 | **DEMONSTRATED** — `evidence/f7_witness.zig`, program "('& %$") => movd-chain reaches d=1,743,392,169 > 3^19=1,162,261,467. Re-run 2026-09-05: `cfg=k20_fixed status=MAX_STEPS steps=50 max_addr=1743392210 >3^19=true`. See also `f7_python_check.py`. |
| C6 WIDTH_EXTENSION_CONSISTENCY | **DESTROYED** — `rotate(v, k) % 3^k != rotate(v, k+1) % 3^k` unless `v % 3 == 0`. Numerics: 33% consistency over 27 samples on w=3. `crazy` is consistent 100% of the time (the op is purely tritwise and padding with zeros is already neutral). Re-verified 2026-09-05 via `f8_check.py` |
| C7 FRONTIER_WIDTH_WIDENING | **DEMONSTRATED** — `tests/t_frontier_moment.zig` prints `WIDEN step=59050 c=59049 d=59049 old_w=10 new_w=11`; the same witness continues through the C8 event. |
| C8 REPEATED_WIDTH_WIDENING | **DEMONSTRATED** for two frontiers: `10→11` at step 59050 and `11→12` at step 177148. Evidence: `f9_repeated_frontier.json`. Do not extrapolate beyond 12. |
| C9 CLASSIC + UNSHACKLED -> FREE | **DEMONSTRATED** in both readings |
| C10 TURING_COMPLETENESS | **NO_NEW_CLAIM** |

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
py    evidence/compare_f4.py            # classic-parity checker (pyref vs zig)
zig run evidence/run_f4.zig             # corpus-on-Zig emitter
```
