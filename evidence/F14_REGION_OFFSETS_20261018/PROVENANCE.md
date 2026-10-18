# Annex: raw F14 captures

Commentary written for this annex; it regenerates nothing and re-formats nothing.
The measurement itself lives in `evidence/f14_region_offsets_20261018.json`,
produced by `evidence/compare_f14_region_offsets.py` against the expectations
pre-registered in `docs/F14_REGION_OFFSETS_V1_PREGISTRATION.md`. These are the bytes
the machine printed.

| file | what it is |
|---|---|
| `console.txt` | the checker's own stdout plus its `F14_RC=` line: reference hashes, cores, regional geometry, 17 `MATCH` expectation lines (D1-D5, P1-P3, R0, R1_STATUS, R1_REGION, R1_HALT_DIVERGENCE, R1_CROSS_CORE, R2_STATUS, R2_REGION, R2_OPCODE_DELTA, R2_CROSS_CORE), `F14 EXPECTATIONS=17 MATCH=17 FALSIFIED=0`, `F14 REGION_1_2_DISPATCH_DIVERGENCE_V1=PASS`, `F14_RC=0` |
| `resource_usage.txt` | GNU `/usr/bin/time -v` for that same process: wall 0.19 s, user 0.13 s, system 0.03 s, peak RSS 32 764 kB, `Exit status: 0` |

Command, run 2026-10-18 on this machine (Zig 0.16.0, Python 3.12.3, Linux
7.0.0-38-generic), from the repository root:

```
/usr/bin/time -v python3 evidence/compare_f14_region_offsets.py \
    --output evidence/f14_region_offsets_20261018.json
```

It needs the external reference, so a clone without `../MalbolgeLispSlop` beside
it exits **3** and the harness prints an explicit
`SKIP (NOT_DEMONSTRATED, missing external input)`; that is what CI shows for this
gate until a vendoring decision is made.

## What the numbers actually pin

* `D1`–`D5` — the regional geometry: `END = 3^19 = 1 162 261 467`, `THIRD = 3^18 = 387 420 489`,
  and reference offsets `offs = [0, 117, 140]`. $117 \equiv 23 \pmod{94}$ and $140 \equiv 46 \pmod{94}$.
* `P1`–`P3` — 150 000 seeded pairs sampled across all three regions ($c < 3^{18}$, $3^{18} \le c < 2 \cdot 3^{18}$,
  and $2 \cdot 3^{18} \le c < 3^{19}$). In Region 0, **0** mismatches (equality). In Region 1, **100%** of samples
  differ by exactly $+23$. In Region 2, **100%** of samples differ by exactly $+46$.
* `R0` — Control Case C1 (`ubO`) in Region 0 halts on all three machines at $(c=2, d=2)$ with stdout `0xda`.
* `R1` — Case R1 (`(aO`, `[40, 97, 79]`) executes `movd` then `jmp` to land in Region 1 ($c = 581\,130\,700$).
  Because of the $+117$ offset, `bolge19` hits opcode 81 (`HALT`) at step 11 ($c = 581\,130\,727$). Our cores
  evaluate step 11 as NOP (opcode 58) and halt at step 60 ($c = 581\,130\,775$), both agreeing to the step and address.
* `R2` — Case R2 (`'&B`, `[39, 38, 66]`) jumps into Region 1 at step 4 ($c = 581\,130\,750$). At step 4, our core
  evaluates opcode 68 (`nop`) while the reference evaluates $(68 + 117) \bmod 94 = 91$ (`invalid`), exhibiting
  the predicted delta of $+23$.

## What this annex is not

Not Turing completeness. Not equivalence in encryption cascades (V3). Not Lutter's original `Unshackled.c`
(which calls `srand(time(NULL))`). Read `docs/F14_REGION_OFFSETS_V1_PREGISTRATION.md` before quoting any number from here.
