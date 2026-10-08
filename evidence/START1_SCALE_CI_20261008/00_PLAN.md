# Parametric start1 sweep — approved design, 2026-10-08

User approved a new1..20 sweep where every measured VM boots at1, real
execution, explicit labels when ASCII/memory values exceed the small active
word. This is not shrinking an existing VM or historical Malbolge at1 trit.

No runtime change. Preserve/hash the existing observation-only core copy.
Adapt only the stock probe's boot width10→1, target guard1..20 and expected
growth target−1. Target1 executes2 steps without widening; target20 executes
1,162,261,468 real steps with19 sparse WIDEN events. One vm.run per rung.
Each rung is a fresh machine, not a persistent benchmark session.

ASCII loader accepts33..126 whereas boot word1 represents0..2. Thus **every
rung in this new sweep** is PARAMETRIC_ASCII_OUTSIDE_BOOT_WORD at initial load,
even if it later reaches20. This family measures the shipped parameterized
operator/frontier behavior, not a closed one-trit-cell machine. Never merge
these rows into prior start10 rows without boot/profile labels.

Validate targets1..5 on original vs observed core, observed repeat, Python
reference. Compare result fields, source/stdout hashes, final pointers,
encryption counts and sparse events. Small runs use runWithTrace on the real
loop and aggregate fetched-cell and encryption-result range violations by
active width. No full trace for large targets. EOF sentinel is intentional
and is not confused with an ordinary memory-cell range violation.

The full sweep uses fresh RAM/disk/pressure snapshots and the same60% budget,
10 GiB MemAvailable and8 GiB disk guardrails. RSS prediction uses prior rung
times3 with25% margin and128 MiB floor. OS address-space cap, CPU600 s and
wall660 s per command. Only small validation is allowed locally with bounded
512 MiB execution and2 GiB build; large execution stays on GitHub Ubuntu.

Tests: legitimate zero encryption, Python small frontier growth, reject
tampered semantic labels. The zero-encryption check failed first under the
old positive-encryption expectation, then passed after correcting the harness
predicate to0<=encrypted<=steps. Original target1 raw log confirms two crazy
steps, zero encryptions, two fetched ASCII cells outside the1-trit word.
Raw initial failure is preserved in local_validation/initial_failure/.

Artifacts: commands/logs, snapshots, sparse events, small audits, hashes,
source/VM binary hashes, all20 measurement rows, CSV after verified download.
No source >1GB, no huge stdout, no binaries in Git. Spanish guide: GUIA.md.
