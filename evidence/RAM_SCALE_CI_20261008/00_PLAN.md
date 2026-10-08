# RAM scale sweep — approved bounded design, 2026-10-08

User explicitly approved a real14..20 sweep, preventative resource stop,
separate u32 ceiling, and16/32/64/128 GiB projections without runtime changes.

Reuse the E20 observation-only core/probe after verifying their original hashes
and the original/observed small differential. Never edit the core or introduce
u64/u128 dense representations. Every measured rung boots at10 and calls the
real VM loop once; separate rungs are fresh runs, not one growing persistent
VM shared between benchmarks. Each rung independently crosses all its frontiers.

Before every build/run: capture RAM, disk, pressure, process limits; require
10 GiB MemAvailable and8 GiB temporary free space. Predicted runtime RSS is
previous measured peak scaled by3 per rung, with25% margin; first rung uses
the prior verified E20 RSS scaled down, with a128 MiB floor. Require prediction
and exact source/storage minimum within60% of MemAvailable. Enforce that60%
address-space ceiling on child runtime, CPU600 s and wall660 s. Build uses2 GiB.

Measure14..20 sequentially. Validate all WIDEN positions, status, steps,
final c/d, cells, no assisted opcodes and hashes. Stop before allocating21:
u32 cannot support it, hash storage exceeds the16 GB budget, and even a
hypothetical u64 source+array minimum exceeds16 GiB.

Tests cover exact21 bytes, memory/disk threshold, ceiling even with abundant
RAM, projection labeling, verified seed and tampered-event rejection.
`verify_scale.py` verifies downloaded hashes and proves no next-rung source
configuration or execution log was created. GitHub artifacts preserve all
raw logs/JSON and small generated code; no giant sources, stdout or binaries.

Projection rows use ideal available=total,60% budget and25% margin on minimum
storage. They are upper ceilings allowed by that incomplete storage test,
not guarantees. Actual runtime/output overhead can reduce them. RAM-width
relationship applies to this specific linear witness, not arbitrary programs:
a fixed-width lazy VM may run a tiny program with little materialized memory.

Human guide: GUIA.md. Historical E20 and local resource blocks stay unchanged.
