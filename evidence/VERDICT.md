# VERDICT — MALBOLGE_FREE_V0

## Claims table (verbatim from the brief)

| Claim | Status |
|---|---|
| C0 SINGLE_PARAMETRIC_CORE | **DEMONSTRATED** — one core, no `k==10/19` switch, verified by inspection + full corpus run |
| C1 CLASSIC_PARITY_K10 | **DEMONSTRATED** — `evidence/f4_classic_parity.json`, 6/6 equal sha256 |
| C2 UNSHACKLED_PARITY_K19 | **NOT_DEMONSTRATED** — original `Unshackled.c` uses `srand(time(NULL))`, so reference parity is nondeterministic by construction. We can reproduce the deterministic subset only. |
| C3 ARBITRARY_FINITE_K | **DEMONSTRATED** — widths 10, 11, 12, 19, 20, 23, 26 all load + fill correctly, and `src/malbolge_free.zig` runs the corpus k=10 (wrap) and k=20 (no wrap) |
| C4 NO_FIXED_COMPILED_MAX_ADDRESS | **DEMONSTRATED** — there is no `MAX_ADDR`. The `mem_limit` becomes `null` precisely in unbounded mode, and nothing lazily resets memory to a 3^k window |
| C5 LEGAL_CROSSING_3_POW_19 | **DEMONSTRATED** — `evidence/f7_witness.zig`, program "('& %$") => movd-chain reaches d=1,743,392,169 > 3^19=1,162,261,467. Logged as max_addr by the VM. See also `f7_python_check.py`. |
| C6 WIDTH_EXTENSION_CONSISTENCY | **DESTROYED** — `rotate(v, k) % 3^k != rotate(v, k+1) % 3^k` unless `v % 3 == 0`. Numerics: 33% consistency over 27 samples on w=3. `crazy` is consistent 100% of the time (the op is purely tritwise and padding with zeros is already neutral) |
| C7 GROW_ON_DEMAND_WIDTH | **NOT_DEMONSTRATED** — the growth pad can affect rotate; extension-consistency fails so the unshackled "grow widthe upon touch" is not semantically safe. `pad_to_padwidth` mode exists and logs events (`stats.growth_events`) but relying on it for rotation changes semantics |
| C8 TRUE_OMEGA_SEMANTICS | **NOT_DEMONSTRATED** — C6 is a genuine blocker: rotate is the width pump, and its growth changes results. No dynamic-ω runtime claim survives |
| C9 CLASSIC + UNSHACKLED -> FREE | **DEMONSTRATED (parametric reading)**. The union works; the dynamic-ω reading does NOT |
| C10 TURING_COMPLETENESS | **NO_NEW_CLAIM** |

## Verdict

`FREE_PARAMETRIC = DEMONSTRATED`

`FREE_OMEGA = NOT_DEMONSTRATED`

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
