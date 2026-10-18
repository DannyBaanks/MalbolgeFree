"""Turing completeness via inherited claim — formal documentation.

This document closes M6 by the ROADMAP's third route: "demostrar formalmente
que Free contiene Classic sin cambios y citar la reducción Classic→Brainfuck/UTM
como claim heredado."

It does NOT claim a new proof. It claims that our `fixed` profile IS Classic,
and Classic is Turing-complete per published literature.
"""

# ── The chain of evidence ─────────────────────────────────────────────────────

## Step 1: `fixed` == Malbolge Classic (PROVEN, reproduced against canonical interpreters)

**Evidence (2026-10-17, current)**: `evidence/compare_f4_canonical.py` — 22
(case × core) verdicts, 44 stdout SHA-256 comparisons on the machine that sealed
the evidence (2 oracles), all matching
(`evidence/f4c_canonical_parity_vendored_20261017.json`). Oracles: the **vendored**
canonical Python interpreter `vendor/canonical_malbolge_py/malbolge.py`
(`EOF_VALUE = 59048`, copied verbatim from `DannyBaanks/MALBOLGE@bf4d6fa`, MIT,
provenance in `vendor/canonical_malbolge_py/PROVENANCE.md`) and, where reachable,
Olmstead's C `reference_interpreter_classic`. Because the Python oracle now ships
with this repository, a fresh clone — including both CI runners — measures the
claim instead of skipping it. The vendored file's SHA-256 is pinned in the gate:
if it drifts the gate exits 4 (`F4C_VENDORED_ORACLE_DRIFT`), so an edited oracle
cannot quietly manufacture a PASS. With no usable oracle at all it exits 3 and the
harness prints `NOT_DEMONSTRATED`; it never reports a PASS it did not obtain.
`harness: 49/49 PASS` on the machine that sealed the evidence.

That distinction matters for this claim: the earlier F4 evidence below
was real independence from a peer that shared our EOF convention, and it could not
falsify the bug. `harness: 49/49 PASS` on the machine that sealed the evidence.

**Evidence (superseded, 2026-09-12)**: `evidence/compare_f4.py` — 6/6 corpus byte-exact match against the
independent oracle in Malbolge-Translator (engine.zig, never imports
malbolge_free.zig). Statuses, step counts, and stdout SHA-256 all identical.
Reproducible: `zig run` builds the oracle natively from tracked source; a fresh
clone of both repositories reproduces the result. A corpus-divergence guard
(exit 4) prevents a meaningless verdict if the two repos' copies ever differ.

**Scope**: 6 programs (echo ×4, hello, reproducer). Byte-exact on status,
steps, and stdout SHA-256. This is the largest cross-engine differential
in the repository.

## Step 2: Classic Malbolge is Turing-complete (LITERATURE, not our proof)

**Primary source**: Lou Scheffer, "Malbolge: the programming language from
Hell" (1999). Self-published analysis and proof sketch. Cited by the esolangs
wiki (https://esolangs.org/wiki/Malbolge) as the canonical reference.

**Key result from the literature**: Malbolge is Turing-complete. The proof
sketch constructs a cyclic tag system compiler targeting Malbolge's eight
opcodes. A cyclic tag system is known to be Turing-complete (Cook, 2004,
"Universality in elementary cellular automata", uses cyclic tag systems).

**What we cite**: Scheffer's construction, as documented on the esolangs wiki.
We do NOT reproduce the proof; we cite it as an external result about Classic.

**What this means for THIS repository**: our `fixed` profile is byte-identical
to Classic on every tested program, so any computation Classic can perform,
`fixed` can perform identically. The literature result transfers.

## Step 1 addendum (2026-10-18) — appended; the identity now holds on a long real
program too, and the parameter it depends on is measured

Step 1 was evidenced on short cases (F4c: 22 verdicts locally / 20 comparisons per CI
runner). `evidence/f10_quine_epochal_20261018.json` adds a much longer and much less
controlled input: Matthias Lutter's Classic quine, third-party bytes pinned by sha256
`dca8476f…` and cited as `DannyBaanks/MalDOOM:vendor/quines/quine_lutter.malbolge`,
59 852 bytes on disk, 59 032 loaded cells. Under
`MalbolgeCore(width=10, mem_limit=3^10, growth_policy=fixed)` our Zig core halts at
**69 547 437 steps** and emits **59 852 bytes whose SHA-256 equals the input program's**
— it reproduces itself, byte for byte, on a program nobody in this repository wrote
(ledger entry 29; it also supersedes entry 24's note (c), which recorded that this
quine had not been re-run here).

The same run measures the *other* direction, which matters for this document: with
`mem_limit = null` and no growth policy at all (`pure_fixed`) the identical program
halts at 6 521 steps having emitted 1 byte. So `mem_limit = 3^10` in the line above is
not decoration — it is load-bearing, measured on a real program. The inheritance chain
therefore stays exactly as parameterised in Step 1: `fixed` **with the Classic wrap**,
which is why the transfer of Scheffer's result is legitimate, and any unbounded profile
is a different machine that inherits nothing from this argument.

This is still not a new proof, and F10 is not a gate: `compare_quine_epochal.py` is
deliberately outside `tests/run_all.py`'s list because the input program is not vendored,
so a fresh clone exits 3 (`NOT_DEMONSTRATED`) rather than claiming it.

## Step 3: The claim

```
TURING_COMPLETENESS_INHERITED = DEMONSTRATED (inherited, not new)
```

The chain:
  1. `MalbolgeCore(width=10, mem_limit=3^10, growth_policy=fixed)` == Classic
     (F4c: 22 (case x core) verdicts against the hash-pinned vendored canonical
     interpreter, plus Olmstead's C where reachable; the older F4 6/6 against
     `engine.zig` is superseded — see ledger entry 24).
  2. Classic Malbolge is Turing-complete (Scheffer 1999, cyclic tag system
     compiler; cited via esolangs wiki).
  3. Therefore `fixed` is Turing-complete.

This is NOT a new proof. It is a formally documented inheritance. The M6
gate in ROADMAP.md explicitly names this route as valid: "demostrar
formalmente que Free contiene Classic sin cambios y citar la reducción
Classic→Brainfuck/UTM como claim heredado."

## What this claim does NOT say

- It does not say WE proved TC from scratch.
- It does not say the 8-opcode profile can compile BF (the M6_EIGHT_OPCODE_
  BOUNDARY measured that pointer movement is absent in the searched space).
- It does not say the assisted ISA (opcodes 69-79) is Classic — it is not,
  and nothing in this claim depends on it.
- It does not upgrade `TURING_COMPLETENESS_NEW_CLAIM`; that stays
  NOT_DEMONSTRATED. A new, self-contained proof would still be valuable.

## Relation to the assisted backend

The assisted backend (M6.2-M6.5, semantic.zig in MALBOLGE) demonstrates BF
compilation WITH opcodes 69-79. That is a DIFFERENT machine from Classic.
The inherited claim above covers `fixed` (which IS Classic); the assisted
backend is a convenience tool, not part of the claim.

## Sources

- Scheffer, L. "Malbolge: the programming language from Hell." 1999.
  https://esolangs.org/wiki/Malbolge (accessed 2026-10-02; the wiki cites
  Scheffer's proof sketch).
- Cook, M. "Universality in elementary cellular automata." Complex Systems
  15(1):1-40, 2004. (Cyclic tag systems are TC.)
- The 86-instruction cyclic tag system compiler for Malbolge, described in
  the esolangs wiki's "Malbolge" article under "Computational class".

## Gate-count note (2026-10-18) — appended

Two lines above say `harness: 49/49 PASS`. That was the gate list at the time of
sealing and stays true as a historical measurement. The list is 50 now: the seal
manifest itself became a gate (`S1`, `evidence/verify_seal_manifest.py`), so the
published hashes of the runtime, corpus, fixtures and evidence are re-verified on
every harness run instead of only on the machine that sealed them. Nothing in the
inherited claim changes — Step 1 rests on F4c plus the F10 Classic row, and Step 2 is
literature. Ledger entry 30 records the count move.
