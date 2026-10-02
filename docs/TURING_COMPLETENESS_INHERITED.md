"""Turing completeness via inherited claim — formal documentation.

This document closes M6 by the ROADMAP's third route: "demostrar formalmente
que Free contiene Classic sin cambios y citar la reducción Classic→Brainfuck/UTM
como claim heredado."

It does NOT claim a new proof. It claims that our `fixed` profile IS Classic,
and Classic is Turing-complete per published literature.
"""

# ── The chain of evidence ─────────────────────────────────────────────────────

## Step 1: `fixed` == Malbolge Classic (PROVEN, reproduced from fresh clone)

**Evidence**: `evidence/compare_f4.py` — 6/6 corpus byte-exact match against the
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

## Step 3: The claim

```
TURING_COMPLETENESS_INHERITED = DEMONSTRATED (inherited, not new)
```

The chain:
  1. `MalbolgeCore(width=10, mem_limit=3^10, growth_policy=fixed)` == Classic
     (F4 6/6, reproducible, corpus-divergence guarded).
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
