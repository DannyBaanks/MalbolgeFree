# Vendored Classic program: `quine_m281.mal`

A published **self-reproducing** Classic Malbolge program, copied verbatim so the
frontier experiments can be *re-executed by CI* instead of depending on a sibling
checkout. See "Why it is vendored" below — this file exists because F10 could not
run on a clean clone.

| field | value |
|---|---|
| source repository | `https://github.com/DannyBaanks/Malbolge-MB-Database` (directory `ISyCo Git/MALBOLGE-MB-DATABASE`) |
| source file | `quine/quine_53562_m281.mb` (git blob `e5b6a1a9ca3b3cc753d889365b2c714b87e4dd84`, commit `c9a188a`) |
| identical copy in | `https://github.com/DannyBaanks/BolgeForge` — `artifacts/candidate_m281_53562b.mal`, same blob `e5b6a1a9…`, commit `5a55b9b` |
| size | 53,562 bytes (52,828 printable program characters + 734 `0x0A` that the quine prints as part of its own source; the Classic loader skips whitespace) |
| SHA-256 of this copy | `96b670b825372a0f41fa3b574d47457f92654b76411e5d5be4c438003087610e` |
| license | MIT, `Copyright (c) 2026 ISyCo Contributors`; both source repositories carry the same MIT `LICENSE` as this one |
| copied | 2026-10-18, `cmp` against both source files reports no differences |
| edits | none. If you edit this file, update `PROGRAM_SHA256` in `evidence/compare_f11_frontier_eof.py` and `evidence/compare_f12_selfreproduction.py` and record it here — both gates pin this hash and exit **4** on drift |

## Independent verification already published elsewhere

`MALBOLGE-MB-DATABASE/quine/evidence/quine_53562_verification.json` (sha256 of the
JSON recorded in that repo's own evidence) shows three engines, all dated 2026-10-17:

| engine | steps | output | parity |
|---|---|---|---|
| `runners/malbolge-original/malbolge` (native C runner) | 62,239,852, `HALTED` | 53,563 B, sha `2d96749e…` | first 53,562 B identical to source; the runner appends one conventional `0x0A` |
| `mb_ref` (independent C oracle) | last emission at 62,239,847 | 53,562 B, sha `96b670b8…` | byte-identical, no convention byte |
| `quine/evidence/mb_classic_indep.c` (written from the published spec, shipped with the evidence, 2,764 B) | 62,239,852, `HALTED` | 53,562 B, sha `96b670b8…` | byte-identical; calibrated on the unrelated `hello_world_40.mb` vector (40 steps, `HALTED`) |

Measured with the same instrumenter: 25,554 distinct code cells executed, against
27,293 for Lutter's quine (m=314).

## Authorship is externally reproducible from a public tool

The program was synthesized, not hand-written. The synthesizer that produces it is
**public and version-controlled**:

| field | value |
|---|---|
| tool | `BolgeForge/synthesize.py` |
| commit | `5a55b9b924c17bd35b0be24d32787ed6c4e4a4a8` ("BolgeForge v3.1 — portable classic Malbolge quine synthesizer") |
| SHA-256 | `e401dec1163c649747c4dd0263f125e25658b6ea44f064bb7c96d896d6b63e3c` |
| invocation | `python3 synthesize.py 281` |
| local reproduction | 2026-10-18, on this machine, from a scratch working directory: wrote 53,562 bytes and reported `VERIFICATION PASS: EXACT 0-BYTE DIFFERENCE BIT-FOR-BIT`. The written file's SHA-256 equals the pinned hash above. |

So the claim "anyone can regenerate this program" is demonstrated against the tool
that is actually published in `BolgeForge`, not against a private successor script.
No claim is made here about any synthesizer version that is not in that commit.

## Why it is vendored

`evidence/compare_quine_epochal.py` (F10) read the program from
`MALDOOM/…` through an absolute sibling path. On a fresh clone — i.e. on both CI
runners — the file is not there, the gate printed its missing-input branch and
returned **3** (`NOT_DEMONSTRATED`). Honest, but it meant the frontier/EOF findings
were established on one machine only, and it is exactly the reason the "new
Malbolge" claim could not be *affirmed* from a clean checkout.

With this file in `corpus/classic/`, `F11` (frontier + width-relative EOF, both
cores) and `F12` (full 62M-step byte-exact self-reproduction, both cores) run from
a fresh clone with no external input, and their exit code **3** branch is
unreachable by design.

## What this file does *not* certify

- It is a **Classic** program (`classic` profile). Vendoring it does not make the
  `epochal` profile input-compatible with Classic: measured in F11, once padwidth
  grows 10→11 the same empty stdin makes `in` return `3**11 - 1 = 177146` instead
  of `59048`, so this program's hard-coded EOF detector stops meaning "end of
  input" under `epochal`. F11 asserts that difference; it does not repair it.
- F12 is a **known-answer parity** gate: it shows our two cores reproduce a result
  three outside engines already agree on. It does not show that `epochal` can
  quine, and it supports no "smallest quine" claim beyond the scoped comparison
  already recorded in the source repository.
- Byte-exact self-reproduction is only ever demonstrated under the `classic`
  profile, at the documented 62,239,852-step halt.
