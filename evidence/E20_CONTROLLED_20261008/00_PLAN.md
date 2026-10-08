# E20 controlled research plan

Spec: the user's 2026-10-08 Compose MalbolgeFree E20 Nagoya20.
Base: 621fa40d29571f8f0bc44ff7af279b18e10479df, clean master; isolated branch
research/e20-controlled-20261008. No runtime changes or historical rewrites.

H1: one real epochal VM, initially width 10, no wrap, crosses 19 to 20.
H2: separately, fixed width 20 agrees with the original Nagoya interpreter
on an explicitly recorded corpus. Finite observations never imply universal equivalence.

- [x] Record hardware, limits, exact dense bytes and hash-only estimate.
- [x] Run epochal, full VM, dense differential and Python/Zig regressions.
- [x] Calibrate dense rung 15 twice; capture GNU time RSS and deterministic fields.
- [x] Apply resource gate before E20. If blocked, do not allocate its witness.
- [x] Fetch Nagoya reference into temporary storage, inspect MIT license,
  hash source and archive; compare original sample and minimal valid programs.
- [x] Record separate verdicts, commands, raw output and hashes; commit evidence.

Review focus: 0/1-based boundaries, aggregate-only growth evidence, stdout
buffer overhead, EOF sentinel differences, fixed address wrap versus no wrap.
Resource guardrails: >=10 GiB MemAvailable, >=8 GiB temporary free space,
estimated peak <=60% of MemAvailable. No remote execution, no process killing.

The specified execution workflow is followed directly in this session.
H1 currently fails the resource gate; instrumentation for a billion-step run
is deferred until resources permit it. Existing source vm.run is preserved.

Completed as bounded research: H1 gate blocked; H2 counterexample recorded.
