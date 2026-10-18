# F13 — `UNSHACKLED_K19_PARITY`: pre-registered expectations

Status: **PRE-REGISTERED BEFORE EXECUTION** (2026-10-18). Written, then run, then
sealed. Nothing in the "predicted" column was observed before it was written
except `C1`, which was executed once during scoping (disclosed below).

## Why this gate exists

`UNSHACKLED_PARITY` has been carried as **NOT_DEMONSTRABLE** because the only
reference we had was the original `Unshackled.c`, which calls
`srand(time(NULL))` (`MALDOOM/vendor/Unshackled.c:585`) — a nondeterministic
peer cannot falsify anything. That label conflates two different claims:

* parity with the *original nondeterministic* `Unshackled` — unreachable by
  construction, and stays unreachable;
* parity with a *deterministic fixed-3^19 machine* — reachable, because such a
  machine now exists on this machine as a third-party artifact we did not write.

`GUIA.md` (Trampas) states the promotion condition for the second reading:
"a localized reference implementation and a reproducible run". This file
pre-registers what that run has to satisfy before the label may move.

## The two machines

| | ours | reference |
|---|---|---|
| artifact | `src/malbolge_core.py` `sha256 7c53f53d…`, `src/malbolge_free.zig` `sha256 8eba78b4…` | `../MalbolgeLispSlop/src/bolge19.zig` `sha256 47758a3f667f4089f6029d86130b94f14f082d4c113a212b8ff571d84113e8a3` (428 lines, verbatim copy of `malbolge-lisp-forensics/src/bolge19/main.zig`), built binary `build/bolge19` `sha256 04b294d37f8f200ea30ba1b301424d4c0358551817cdd94db12a7235ddd10c4e` |
| constructor | `initUnshackledK19(alloc)` = `init(alloc, 19, pow3(19), .fixed)`; Python `MalbolgeCore(width=19, mem_limit=3**19, growth_policy='fixed')` | `END = 1162261467` (`bolge19.zig:27`), fixed by construction |
| profile file | `profiles/` (ours) | `../MalbolgeLispSlop/profiles/fixed19.json` `sha256 6cc0afa10b050a36673e131b2efc69fa29e9589136f52b5f27a7dabe23b6ac1f` |
| lineage | this repository | composed from `fast20.c` (iczelia/malbolge-lisp) semantics + Autobolge-style overlay |
| build | `zig 0.16.0`, CPython 3.12 | `MalbolgeLispSlop/tools/build.sh`, `zig 0.16.0` |

**No reference byte is copied into this repository.** The gate reads the
sibling path, records the hashes it observed, and exits 3 if the reference is
absent. Vendoring is a licensing decision (the sibling ships `bolge19.zig`
under "MIT forense" and states "copy-and-revalidate, never import"), not a
technical step.

## Scope, stated before measuring

bolge19 decodes `idx = (c + mem[c] + off[region]) % 94` with
`offs = [0, 117, 140]` (`bolge19.zig:371-376, 388-389`), where `region =
c / 3^18`. Our cores decode `(c + mem[c]) % 94` with no region term
(`malbolge_core.py:196`, `malbolge_free.zig:487`). Therefore the two machines
can only be differential-tested while `c < 3^18 = 387 420 489` — region 0,
where `off[0] = 0`. Every case below executes 4 or fewer instructions from
address 0, so all addresses stay in region 0.

The same restriction excludes self-modification effects: in a forward walk each
cell is decoded exactly once, so the encryption divergence below cannot reach
the compared output. Each case is checked against that requirement, not assumed.

## Divergences identified by code reading (these are findings, not failures)

| ID | our cores | bolge19 | consequence |
|---|---|---|---|
| V1 | `(c + mem[c]) % 94` | `+ 117` in region 1, `+ 140` in region 2 | dispatch differs for `c >= 3^18`. Out of scope here; bolge19's own region-0 micro-anchor asserts region 0 is the canonical formula |
| V2 | `rotate(v, 19) = v//3 + (v%3)*3^18` | `mrot` (`bolge19.zig:65-71`) rotates the low **18** trits and leaves the 19th in place | differs for every value with `v % 3 != 0`; exercised by `C3` |
| V3 | encrypt via the 94-entry xlat indexed `mem[c] - 33`, guard `33 <= m <= 126` (`malbolge_core.py:258`, `malbolge_free.zig:641`) | encrypt via the 135-entry concatenation `"SOMEBODY MAKE ME FEEL ALIVE" + xlat + "AND SHATTER ME"` indexed by `mem[c]` directly, guard `m < 135` (`bolge19.zig:31-34, 419`) | different alphabet offset (27 vs 33) and different guard domain; **not exercised** by F13 (see Scope) |
| V4 | `steps` counts the halt instruction | `steps` is incremented at the end of the loop body and `break`s before it (`bolge19.zig:381-413, 422`) | our `steps` is exactly one greater. Recorded as a convention, not a mismatch |
| V5 | tail fill: frozen 12-cell crazy period (`malbolge_core.py:103-126`) | continuous crazy chain to the page boundary, then a period-6 pattern keyed by `pbase % 3^18 + i` (`bolge19.zig:84-117`) | representations agree inside the chain window (address < 65 536 for these images), may differ past it. Not exercised |

Our encryption reading is not an opinion: `vendor/canonical_malbolge_py/malbolge.py:26-31,127-128`
uses the same 94-entry `_ENCRYPT` dict with the `33 <= m <= 126` guard, and F4c
already demonstrates our cores agree with that oracle. So V3 is a
Classic-vs-fast20 divergence, not a defect in this repository.

## Case set

Images are whitespace-free byte images, so the reference's `--loader raw` and
our loader produce the same memory cells. Opcode alignment: cell at position
`p` holds `b` with `(b + p) % 94 = op`.

| case | image (decimal bytes) | stdin | instruction walk |
|---|---|---|---|
| `C1` | `117 98 79` = `ubO` | empty | in → out → halt |
| `C2` | `117 61 97 78` = `u=aN` | empty | in → crz → out → halt |
| `C3` | `68 38 97 78` = `D&aN` | empty | nop → rot → out → halt |
| `C4` | `117 98 79` = `ubO` | `A` (65) | in → out → halt |

## Pre-registered expectations (20)

`D1` `pow3(19) == json.end == 1 162 261 467`.
`D2` both cores assign `3^padwidth - 1 == json.eof_value == 1 162 261 466` at end of input.
`D3` our `mem_limit == json.end`, and both machines advance `c`/`d` modulo that same value.
`D4` the eight dispatch opcodes of `json.dispatch` are exactly the eight our Classic cores decode: `{4, 5, 23, 39, 40, 62, 68, 81}`.
`D5` `json.trits == 19 == our width == our padwidth` under the fixed policy.

`P1` `mcrz` transcribed from `bolge19.zig` (`CRZ2` + `CRAZY_TBL`, lines 36-63) equals `crazy(a, d, 19)` on **every** pair of a 200 000-sample seeded grid (`random.Random(20261018)`), i.e. **0 mismatches**.
`P2` the transcribed `mrot` differs from `rotate(v, 19)` on **exactly** the sample values with `v % 3 != 0` (mismatch set == predicate set), confirming V2 as a rule rather than a count.

`P1`/`P2` are a check of *our reading* of the reference, not an independent peer:
the falsifier is the binary itself — if the transcription were wrong, `C2`
would not reproduce the predicted byte.

`R1` `C1` status `HALTED` on both, at the same halt address (`c`, `d` equal).
`R2` `C1` stdout equal on both cores and on the reference, exactly one byte `0xda` (`(3^19-1) % 256 = 218`).
`R3` `C1` steps: ours `3`, reference `2` (V4).
`R4` `C2` status `HALTED` on both, same halt address.
`R5` `C2` stdout equal on both, exactly one byte `0x20`: `crazy(1 162 261 466, 61, 19) = 32`.
`R6` `C2` steps: ours `4`, reference `3`.
`R7` `C3` status `HALTED` on both, same halt address.
`R8` `C3` stdout **differs**, ours `0x9e` (`rotate(38,19) = 774 840 990`) and the reference `0x92` (`mrot(38) = 258 280 338`). A predicted divergence that does *not* appear is a falsification, not a pass.
`R9` `C3` steps: ours `4`, reference `3`.
`R10` `C4` status `HALTED` on both, same halt address.
`R11` `C4` stdout equal on both, exactly one byte `0x41` (a raw stdin byte, not a trit).
`R12` `C4` steps: ours `3`, reference `2`.

`L1` the reference reports `imagen=3 celdas` for `C1`, equal to our `program_len` — the raw loader stores file bytes verbatim on both sides.

Every case is run on both of our cores (Python and Zig) against the same
reference run, so a MATCH means three-way agreement.

## Exit contract

`0` all 20 expectations hold · `3` the reference source, profile or binary is
absent (`NOT_DEMONSTRATED`, an explicit skip, never a green) · `4` the reference
bytes drifted from the hashes recorded in the run report (integrity failure).
A falsified expectation exits `1` with the expectation ID printed.

## What F13 does not claim

Not Turing-completeness. Not parity with Lutter's `Unshackled` (V1/V2/V3/V5 are
differences from it). Not the growth policy, not Unicode I/O, not the `lutter`
loader rules, not any address in regions 1 and 2, not memory past the page
window, not the encryption cascade, and not a program of realistic size. Four
executed instructions each. The claim is exactly: **a localized deterministic
fixed-3^19 reference exists, runs on this machine, and agrees with both of our
cores on the parameter set and on these primitives.** That is enough to move
`UNSHACKLED_PARITY` out of "unreachable by construction" and into "measured, in
this scope" — and it is not enough to call our k19 profile `Unshackled`.
