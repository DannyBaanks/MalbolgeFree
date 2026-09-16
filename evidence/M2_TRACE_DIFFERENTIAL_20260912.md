# M2 Classic trace differential — 2026-09-12

## Claim

`CLASSIC_TRACE_CONFORMANCE`: the Classic runtime agrees with an independent
in-repository oracle on instruction state, input/EOF, jumps, writes caused by
self-encryption, termination, and the max-step boundary.

## Command

```text
py evidence/compare_m2.py
```

## Raw output

```text
M2_VALID_CASES=8
M2_ERROR_CASES=3
M2_TRACE_STEPS=44
M2_TRACE_DIFFERENTIAL=PASS
```

Exit code: `0`.

Environment:

```text
Python 3.12.4
Zig 0.16.0
Windows host
```

## Scope and controls

- Eight small Classic programs exercise OUT, IN, EOF, ROT, MOVD, CRAZY, JMP,
  runtime NOP, HALTED, and MAX_STEPS.
- Three load failures cover non-printable source, invalid positional opcode,
  and a valid but undersized source.
- The oracle is implemented independently in `evidence/compare_m2.py` from
  `docs/CLASSIC_SEMANTICS.md`; it does not import the Zig runtime.
- The checker is read-only and writes no report file.
- This is not a complete proof of all Classic programs or all 59049 memory
  states. Long-corpus stdout parity remains covered separately by F4.

## Known limitation

The M2 fixture set is deliberately compact. Exhaustive/randomized Classic
trace coverage and invalid-source error parity remain future work.
