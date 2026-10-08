# E20 GitHub-hosted controlled experiment

User authorized GitHub CI execution on 2026-10-08, after the local resource
gate blocked E20. Repository is public; GitHub documents 16 GB for standard
Ubuntu runners. Actual MemAvailable and free temporary disk decide the gate.

H1 only: epochal free_pure booting at 10, no address wrap, one uninterrupted
vm.run through 19 to 20. H2 EOF disagreement remains unchanged.

1. Generate an exact copy of the core with only sparse WIDEN logging around
   frontierTrigger; original runtime file stays unchanged. Preserve/hash copy.
2. Run full-loop and dense differential tests on original and observed copies.
3. Compare target12 original/observed and repeat observed: aggregate fields,
   source/stdout hashes, final_d, encryption count and events must agree.
4. Compile separate executables; GNU time measures execution without compiler
   cost. Calibrate target18. Extrapolate peak to target20 with 25% margin.
5. Require >=10 GiB MemAvailable, >=8 GiB disk, estimated peak <=60% available.
   Apply RLIMIT_AS at that 60% budget, CPU 600 s and wall timeout 660 s.
6. Run target20 only on GO. Require all ten WIDEN events, exact one-based
   step/positions, final width/growth/c/d, no assisted opcodes, source and stdout
   hashes. Preserve negative output and classify blocked separately.
7. Upload only evidence files; retrieve and verify SHA-256 locally.

Known limitation: target18 RSS extrapolation is empirical, not an upper bound.
OS address-space cap can fail the run safely. Core u32 dense ceiling at 20
remains; this cannot demonstrate unbounded width growth or Nagoya equivalence.
VM instrumentation adds observation only, no replay/reinitialization or skipped
instructions. Source witness generation and SHA-256 do not simulate VM steps.

Local negative: initial harness incorrectly expected encrypted_cells==steps.
Actual code encrypts only ASCII cells; original target12 reported encrypted
141328 versus steps177148. Corrected predicate to 0<encrypted<=steps; equality
across original/observed still required. Raw negative and corrected validation
are preserved in local_validation/. No runtime fix was made.

Human commands and status interpretation: [GUIA.md](GUIA.md).
