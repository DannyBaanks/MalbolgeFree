# Changelog — Malbolge Free

Built from the git history (`git log --format="%ad %s"`). No entry is invented;
each line is a commit message. Claims about what each change demonstrated live
in `docs/HONESTY_LEDGER.md`, not here.

## Unreleased (toward 1.0.0)

- Product CLI: `run` / `inspect` / `trace` with contractual exit codes,
  `trace_run` proven identical to `run` (60k steps incl. epochal).
- Removed stale `tests/malbolge_free.zig` + `evidence/malbolge_free.zig`
  (unreferenced pre-M1 copies; canonical runtime is `src/`).
- M7 tape width: `TAPE_BASE` / `DEFAULT_TAPE_SIZE` are named constants,
  size configurable per instance; default stays 256.
- M7: double free on malformed images fixed; tape-capacity claim corrected
  (input capacity ~255 bytes, not compiler size).
- M6 boundary: what eight Classic opcodes can/can't do, bounded and measured.
- M0 closed: EOF trace cases + numeric precision (10/10), 2 hazards pinned.
- M4b: free-pure vertical slice (8 opcodes only, input-dependent output).
- F4 parity oracle built natively from tracked source; reproducible clone.
- Epochal policy implemented in the Python core; differential vs Zig.
- Dense representation: ladder measured to `w=19` (was 16).
- CI on ubuntu + windows; manual epochal-ladder workflow.
- Fixed Zig 0.16.0 Debug miscompile of u128 switch (if-chain).

## 2026-09-24 and earlier

- 2026-09-24: relative paths instead of fixed `C:\Development`; `run_f4.pdb`
  removed from the index.
- 2026-09-16: epochal ladder on the real VM up to `w=16`, plus E10→E19 toy
  ladder; clean-room Malbolge Classic emitter.
- 2026-09-10: Brainfuck→Malbolge Turing completeness demonstration
  (output-reproduction smoke test, not a new TC proof).
- 2026-09-09: Spanish README merged; v1.0.0 parity fixes.
- 2026-09-05: omega notation retired for the finite variable-width model;
  parametric Malbolge core; Classic parity 6/6.

## Explicitly NOT in any release

- Turing completeness as a new claim (`NO_NEW_CLAIM`, see M6 docs).
- Unshackled bit-parity (`NOT_DEMONSTRABLE`: the original uses
  `srand(time(NULL))`).
- Unbounded width growth (finite ladder by construction; dense bounded at
  `w=20`).
- Ouroboros self-hosting (blocked on measured input capacity + brackets).
