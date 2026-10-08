# E20 GitHub result — 2026-10-08

EPOCHAL_19_TO_20: DEMONSTRATED_SCOPED
FIXED20_NAGOYA_PARITY: FAIL (separate local EOF counterexample)
MALBOLGE20_IDENTICAL_TO_FREE_EPOCHAL: NOT_CLAIMED
UNBOUNDED_WIDTH_GROWTH: NOT_DEMONSTRATED
GENERAL_SEMANTIC_EQUIVALENCE: NOT_DEMONSTRATED

[GitHub run 37847283479](https://github.com/DannyBaanks/MalbolgeFree/actions/runs/37847283479)
completed successfully using commit ac94be2b92345e2d872f05e265f853b4d3afac3e.
Raw downloaded artifact files are preserved byte-for-byte beside this report;
their original hashes.json was verified locally, not regenerated.

One boot at width 10, .epochal, mem_limit=null, free_pure, dense u32;
one uninterrupted vm.run, no pointer patching, fast-forward, replay or state
reinitialization. Observation-only core copy records the ten real WIDEN events.
Small original/observed differential and deterministic repetition passed.
Original and observed core copies passed full-loop and dense differential tests.

Critical event: `WIDEN step=1162261468 c=1162261467 d=1162261467 old_w=19 new_w=20`.
Step numbering is one-based, pointer positions zero-based; the trigger runs
before the instruction reads that boundary cell. Final status MAX_STEPS is
the deliberate run budget, not program HALT.

| Metric | Recorded value |
|---|---:|
| Real VM steps | 1,162,261,468 |
| Final width / growth events | 20 / 10 |
| Final c / d | 1,162,261,468 / 1,162,261,468 |
| Materialized cells | 1,162,262,480 |
| Output bytes | 383,299,003 |
| Encrypted cells / assisted opcodes | 927,336,249 / 0 |
| Executable elapsed | 109.87 s |
| Peak RSS | 6,197,026,816 bytes (5.77 GiB) |
| Available RAM at gate | 15,725,748,224 bytes |
| Estimated RSS with 25% margin | 7,772,682,186 bytes |
| OS address-space ceiling / gate budget | 9,435,448,934 bytes |

Time includes witness generation, VM load/run and source/stdout hashing,
excludes compilation. No swap events were reported by GNU time. Source was
generated in memory; neither the 1.16 GB source nor 383 MB stdout is committed.
The generator algorithm, hashes and length are preserved instead.

Source SHA-256: b9788933f5892f3a855e93d746e74cb1561fd00882182ac2b4e704f41af91aac
Stdout SHA-256: 84b36064019d339f445bfa627609f38d897bde7db5f0398393851bf2ba3df770

Reproduce/verify: see [CI plan](../E20_CI_20261008/00_PLAN.md) and
[Spanish guide](../E20_CI_20261008/GUIA.md). Actual commands/exit codes are
in commands.json; runtime/generator/harness hashes and measured commit are in
provenance.json. The preserved core copy and generated probe allow inspection
of instrumentation. No runtime source file was modified.

Scope: finite linear witness. Full E20 Python parity, unbounded growth,
universal state or language equivalence and general Nagoya conformance remain
NOT_DEMONSTRATED. Dense cannot safely represent widths>=21. The prior
[EOF disagreement](../E20_CONTROLLED_20261008/03_NAGOYA_COMPARE.md) is unchanged.
Only one full E20 run was performed; small instrumented runs were repeated.
