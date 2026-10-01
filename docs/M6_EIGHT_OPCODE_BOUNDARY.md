# M6 — What the eight Classic opcodes can and cannot do

Date: 2026-10-01. Status: **bounded negative result**, reproducible.

## The question

The M6 gate wants a BF->Malbolge compiler that preserves tape, loops, input and
output. The first sub-goal is BF `>`: move the data pointer by one.

In this machine `d` is written by exactly one opcode, 40 (`movd`: `d = mem[d]`),
and otherwise increments once per executed step. So making `d`
input-dependent requires a cell holding an input-derived address, which in turn
needs a data-dependent jump. That is a measurable question, not an assumption.

## Method

Exhaustive enumeration over templates of the form

```
.CODE
  IN
  <up to N instructions from {MOVD, OPR 39, NOP, JMP, INC}>
  OUT 65
  HALT
```

run twice, once with input `0x00` and once with `0xff`. A template counts as a
witness when `final_d` differs between the two runs. Note `INC` is an auxiliary
opcode, so in the strict profile it decodes to a NOP; it is kept in the set so the
*same* search can be pointed at the assisted profile as a control.

The search runs against `free_pure` (strict, eight opcodes, encryption on) and
against `free_assisted` (auxiliary ISA available).

## Result

| profile | witnesses with input-dependent `d` |
|---|---|
| `free_pure`, eight Classic opcodes | **0** |
| `free_assisted` | **> 0** (e.g. `IN; JMP; OUT 65; HALT` gives `d=29580` vs `d=130`) |

Widening the search to depth 5 over the focused instruction set still found
**zero** in the strict profile.

## Why this is not a proof of impossibility

The search is bounded, so this is a bounded negative. Two things keep it from
being a vacuous claim:

1. **Control.** The identical search pointed at `free_assisted` *does* find
   witnesses, so the methodology detects this effect when it exists. This is
   asserted as a test, so if a future change breaks the search the guard fails.
2. **The bound is stated**, in the test name and here.

## The boundary is specific

This is not "the strict profile is inert". Two things *are* demonstrated with
only the eight Classic opcodes:

- input-dependent **output** (`tests/t_free_pure_vertical_slice.zig`, and
  re-asserted here),
- self-modification with encryption active.

What is missing in the searched space is **pointer movement driven by data**.
That is precisely the capability the auxiliary ISA provides, and precisely why
the BF backend (`src/bfir1_backend.zig`) emits `TAPE_BASE` / `INC` / `D_REWIND`
rather than only Classic opcodes.

## Consequence for the M6 gate

`TURING_COMPLETENESS_NEW_CLAIM` stays **NOT_DEMONSTRATED**. This document does
not move it. What it adds is a reason: the missing piece is not "someone has not
written the compiler yet", it is that the eight-opcode profile lacks the
pointer-movement primitive the compiler needs, and closing that gap is either a
synthesis problem of unknown depth or a VM contract change.

Note also that M6's acceptance criteria ask for an independent implementation or
a formal proof of the translator. The differential work behind
`free_pure` vs `free_assisted` is a differential between two profiles of one
runtime, not that independence.

## Reproduce

```bash
zig test --dep hell=hell --dep malbolge_free=malbolge_free \
  -Mroot=tests/t_m6_eight_opcode_boundary.zig \
  -Mhell=src/hell.zig -Mmalbolge_free=src/malbolge_free.zig
```