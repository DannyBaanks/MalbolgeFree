# M7 — Measured tape capacity, and why self-hosting is blocked

Date: 2026-10-01. Supersedes the explanation in `m7/STATUS.md`, which was
measured wrong.

## What was claimed

`m7/STATUS.md` said a self-contained `compiler.bf` (~1500+ operators) "cannot
auto-compile its own source inside the backend of 256 cells", because `TAPE_BASE`
zeroes only cells 1000..1255.

## What is actually true

`TAPE_BASE` does zero exactly 256 cells (`src/malbolge_free.zig`, op 75) and
leaves `d` at 999, so the usable BF tape is that window. That part is correct.

But the **reason** the compiler cannot self-compile is not its own size.
Simulating `m7/compiler.bf` as BF and recording the highest pointer it reaches:

| input length (bytes) | max pointer | steps |
|---:|---:|---:|
| 0 | 3 | 291 |
| 50 | 53 | 310,389 |
| 100 | 103 | 650,489 |
| 200 | 203 | 1,420,689 |
| 300 | 258 | 1,989,039 |
| 400 | **258** | 2,737,339 |
| 800 | **258** | 5,671,345 |

The pointer tracks input length about 1:1 and then **saturates at 258**. So the
compiler's real constraint is its **input capacity of roughly 255 bytes**, not
its own footprint: compiling `""` touches 4 cells, and a nested program touches
about 25.

Bracket nesting is cheap by comparison, about 2 cells per level:

| nesting depth | max pointer |
|---:|---:|
| 1 | 7 |
| 5 | 15 |
| 10 | 25 |

so nesting up to roughly 125 levels still fits.

`compiler.bf` is 1519 bytes. It cannot ingest its own source because 1519 > 255.
That is the blocker, stated correctly.

## The worse problem: silent corruption past the limit

Past roughly 255 input bytes the compiler does not fail. It stops advancing and
keeps emitting. For a 400-character input it emitted 1737 bytes with a
self-consistent header but an instruction count that does not match the records
actually written. Nothing signals the failure.

And brackets are broken at *any* length. `m7/gen.py`'s `_emit_records` is
documented as "Bracket-free": it classifies `[` and `]` to opcodes 7 and 8,
counts them, and emits every record with `has_target = 0`. For
`++++++[>++++++<-]>.` the output has the right header, the right length and the
right count (19) with the wrong bytes:

| case | match vs oracle |
|---|---|
| `""`, `++`, `+++.-.`, `>+++<+>.>.`, `,+.`, `>>+<++.` | byte-exact |
| `++++++[>++++++<-]>.` | same length, same count, **different bytes** |

So `compiler.bf` is a correct compiler for bracket-free input up to about 255
bytes, and a **silently wrong** compiler outside that.

## The crash this was hiding

Feeding that silently-wrong image to `bf_ir_image.decode` reached `ir.validate`,
which correctly rejected it — and then **segfaulted in `Allocator.free`**.
`decode` had registered two cleanups for the same buffer:

```zig
errdefer code.deinit();      // frees the list buffer
...
var program = ir.Program{ .code = code };
errdefer program.deinit();   // frees the SAME buffer again
try ir.validate(&program);   // rejects bracketed images -> double free
```

Any image that got as far as `validate` failing took the process down. That is
why the bracket problem could go unnoticed: the visible symptom was a crash, not
a wrong answer.

Fixed by moving the fill into its own function so exactly one cleanup is in
scope. `tests/t_m7_compiler_image_guard.zig` (3/3) now asserts the malformed
image is **rejected with `MissingJumpTarget`**, that the image is structurally
plausible (which is the trap), and that the happy path plus
`InvalidHeader` / `InvalidLength` / `InvalidFlags` all still behave.

## Consequence for the Uroboros gate

`VM(I1, compiler.bf) = I2` stays **NOT_DEMONSTRATED**, for two independent
reasons now measured rather than assumed:

1. **Input capacity.** 1519 bytes of source against a ~255 byte ceiling.
2. **Bracket resolution.** Not implemented; self-hosting needs it because
   `compiler.bf` itself contains 49 bracket pairs.

Closing (2) needs scratch while scanning, which the contiguous 256-cell tape
does not provide, so it lands on the same `TAPE_BASE` decision. Note that even a
wider tape does not fix (1) on its own: the compiler's internal capacity is
baked into its own layout and would have to grow with it.

## The tape was widened anyway, and what that did and did not buy

`TAPE_BASE` and the tape size were bare literals (1000, 256) duplicated across
the core, the backend contract and three M6 differential tests. They are now
`TAPE_BASE` / `DEFAULT_TAPE_SIZE` in the core, the size is per-instance via
`setTapeSize(n)`, and the default stays 256 so recorded M6 evidence remains
comparable. `tests/t_m7_tape_width.zig` (4/4) pins that a wider tape is zeroed
across its whole length, that the size is validated, and that widening changes
capacity but **not** semantics: identical behaviour inside the first 256 cells.

What widening did NOT buy, stated plainly:

- **It does not raise the compiler's 255-byte input ceiling.** That ceiling was
  measured by simulating `compiler.bf` on an *unbounded* tape and it still
  saturated at 258. The ceiling is baked into the compiler's own generated
  layout, so no runtime tape size can move it.
- **It does not implement bracket resolution.**

So the two measured blockers for Uroboros both survive widening. What changed is
that the runtime ceiling is no longer a hardcoded constant, so a future compiler
generated with a stride-N layout has room to run.

## Reproduce

```bash
zig test -Mroot=tests/t_m7_compiler_image_guard.zig
zig test --dep hell=hell --dep malbolge_free=malbolge_free \
  -Mroot=tests/t_m7_tape_width.zig \
  -Mhell=src/hell.zig -Mmalbolge_free=src/malbolge_free.zig
```