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
- F10: Lutter's quine under `classic` / `pure_fixed` / `epochal` — Classic row
  reproduces it byte-for-byte (69,547,437 steps), the two unbounded rows do not;
  frontier crossed at step 1230 by pointer assignment. Evidence only, not a gate.
- S1: `SHA256SUMS.txt` is now verified in the harness (`evidence/verify_seal_manifest.py`),
  so every CI run on both runners checks the published bytes against their seals.
  Gate count 49 → 50.
- F10 raw captures annexed (`evidence/F10_QUINE_EPOCHAL_20261018/`): sealed-run console
  output, its `time` report, and both bounded trials kept as bytes with a `PROVENANCE.md`
  separating budget artifacts from behavioural results. Adds no claim; sealed paths 35 → 40.
- The moved seal measured in CI: run `39118092762` on `2b57e9d` prints
  `manifest_sha256=d45319d1… entries=40 ok=40` with 50 PASS / 0 FAIL / 0 SKIP on both
  ubuntu and windows runners — documentation only, no sealed byte changed.
- F11/F12: `corpus/classic/quine_m281.mal` vendored from the published MB-Database copy
  (byte-identical to BolgeForge `candidate_m281_53562b.mal`, reproducible with the public
  `synthesize.py 281`), plus two gates that need no external input — F11 frontier crossing
  and width-relative EOF (`in` at EOF = `3^padwidth - 1`: `59048` vs `177146`), F12 the
  62 239 852-step byte-exact self-reproduction. Gate count 50 → 52, sealed paths 40 → 53,
  `manifest_sha256=298fe800…`.
- Those two gates measured green on both runners: run `39129462270` on `318aa9b`, ubuntu
  3 m 56 s and windows 7 m 05 s, each printing `entries=53 ok=53` and
  `52 PASS / 0 FAIL / 0 SKIP` — documentation only.
- `GUIA.md` gained the missing warning that `--growth epochal` changes the end-of-input
  value at a widening, with two measured CLI commands. `GUIA.md` is sealed, so this is an
  integrity event: identity `298fe800…` → `a39adde9…`, sealed paths 53 → 54, because the
  fixture the guide now cites (`tests/frontier_witness.txt`) was sealed in the same block.
  No gate added.
- That seal read back from CI: run `39144966132` on `69b69f5` prints `a39adde9… entries=54
  ok=54 drift=0 missing=0` on ubuntu (3 m 54 s) and windows (4 m 19 s) with 52 PASS / 0 FAIL /
  0 SKIP on each; the newly sealed `tests/frontier_witness.txt` is now integrity-checked on both
  platforms. Runner F12 timings halved on windows with identical runner images, recorded as noise.
- Control read: the very next push `69b69f5..8ead5e9` touched only unsealed docs and both
  runners of run `39145896988` still print `a39adde9… entries=54 ok=54` with 52 PASS / 0 FAIL /
  0 SKIP. Four job-runs on identical images show the fast job swapping platforms (ubuntu then
  `48.9 + 47.0` s, windows then `68.2 + 94.3` s): the variance is per run, not per platform.
- `evidence(F13): measure scoped fixed-3^19 parity against a deterministic external machine`
  (`f097db0`) — 20 pre-registered expectations, 20 MATCH, 0 FALSIFIED, exit 0, three machines
  per case (external `MalbolgeLispSlop/src/bolge19.zig`, our Python core, our Zig core),
  region 0 only, ≤4-cell programs. Two expectations assert disagreement on purpose: `rot`
  (`0x9e` ours vs `0x92` reference) and the halt counter (`ours = reference + 1`). The
  reference is **not vendored** (licensing), so the gate exits 3 without the sibling checkout
  and CI shows `SKIP (NOT_DEMONSTRATED, missing external input)` while local reads
  `53 PASS / 0 FAIL / 0 SKIP`. Gate count 52 → 53, sealed paths 54 → 60, identity
  `a39adde9…` → `ad581d0a…`; `src/` untouched. Ledger entry 39.
- `evidence(F14): measure regional dispatch divergence V1 against deterministic reference`
  — 17 pre-registered expectations (D1–D5, P1–P3, R0, R1_*, R2_*), 17 MATCH, 0 FALSIFIED,
  exit 0, comparing `MalbolgeFree` against `MalbolgeLispSlop/src/bolge19.zig` across
  Region 0, Region 1 ($c \ge 3^{18}$) and Region 2 ($c \ge 2 \cdot 3^{18}$). Demonstrates
  exact regional offset divergence ($+117 \equiv 23 \pmod{94}$ in Region 1, $+140 \equiv 46 \pmod{94}$
  in Region 2) in formula sampling (150 000 pairs, 0 mismatches) and in execution traces jumping
  into Region 1 (`b"(aO"` and `b"'&B"`). Gate count 53 → 54, sealed paths 60 → 65, identity
  `ad581d0a…` → `7e3c9a09…`; `src/` untouched. Ledger entry 40.

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
- Unshackled bit-parity as such (`NOT_DEMONSTRABLE`: the original uses
  `srand(time(NULL))`, so the reference cannot agree with itself). Gate F13 measures a
  different claim — agreement with a deterministic fixed-3^19 machine over region 0 —
  and is not offered as Lutter parity.
- Unbounded width growth (finite ladder by construction; dense bounded at
  `w=20`).
- Ouroboros self-hosting (blocked on measured input capacity + brackets).
