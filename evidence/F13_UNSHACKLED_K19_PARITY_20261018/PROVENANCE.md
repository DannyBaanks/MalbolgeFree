# Annex: raw F13 captures

Commentary written for this annex; it regenerates nothing and re-formats nothing.
The measurement itself lives in `evidence/f13_unshackled_k19_20261018.json`,
produced by `evidence/compare_unshackled_k19.py` against the expectations
pre-registered in `docs/F13_UNSHACKLED_K19_PREGISTRATION.md`. These are the bytes
the machine printed.

| file | what it is |
|---|---|
| `console.txt` | the checker's own stdout plus its `F13_RC=` line: the three reference hashes, both cores, the region-0 scope line, four case rows (reference / Python / Zig), 20 `MATCH` expectation lines (D1-D5, P1-P2, R1-R12, L1), `F13 EXPECTATIONS=20 MATCH=20 FALSIFIED=0`, `F13 UNSHACKLED_K19_PARITY=PASS`, the `F13 DISCLOSURE` line, `F13_RC=0` |
| `resource_usage.txt` | GNU `/usr/bin/time -v` for that same process: wall 1.30 s, user 0.94 s, system 0.11 s, peak RSS 67 044 kB, `Exit status: 0` |

Command, run 2026-10-18 on this machine (Zig 0.16.0, Python 3.12.3, Linux
7.0.0-38-generic), from the repository root:

```
/usr/bin/time -v python3 evidence/compare_unshackled_k19.py \
    --output evidence/f13_unshackled_k19_20261018.json
```

It needs the external reference, so a clone without `../MalbolgeLispSlop` beside
it exits **3** and the harness prints an explicit
`SKIP (NOT_DEMONSTRATED, missing external input)`; that is what CI shows for this
gate until a vendoring decision is made. The four `zig run` calls are what the
1.30 s mostly is (build cache warm); the primitive sample is 400 000 draws.

## What the numbers actually pin

Three machines were asked the same four questions, so every `MATCH` below is a
three-way agreement, not a self-comparison:

* `C1`/`C4` — end of input assigns `1 162 261 466 = 3^19 − 1`, and a real stdin
  byte is assigned verbatim. Reference `a=1162261466` printed at the halt.
* `C2` — `crazy(1 162 261 466, 61, 19) = 32` on all three, and
  `P1` extends that to 200 000 seeded pairs with **0** mismatches: the
  reference's base-9 two-trit fast path (`CRZ2`, `bolge19.zig:37-63`) and our
  base-3 19-trit loop are the same function.
* `C3` — the two machines **disagree** as predicted: `0x9e` versus `0x92`,
  because `rotate(v,19)` moves the low trit to position 18 while
  `bolge19.mrot` rotates only 18 trits and leaves the 19th in place. `P2` states
  the rule, not the coincidence: the divergence set is exactly
  `{v : v % 3 != 0}` (133 230 of 200 000 values under 3^18).
* `L1` — the reference reports `imagen=3 celdas` / `4 celdas` for the same files
  our loader counts as `program_len` 3 / 4: byte-identical raw images.

Steps are reported as ours `3` against the reference `2` (and `4` against `3`).
That is V4, a counter convention: `bolge19.zig:422` increments after the step
body, and the halt branch at `:411-413` breaks before it. The gate asserts
`ours == reference + 1` rather than silently aligning the two, so a future change
to either counter shows up here.

## What this annex is not

Not parity with Lutter's `Unshackled`. Three differences from it are documented
and out of scope by construction — region offsets `+117`/`+140` at `c >= 3^18`
(V1), the 135-entry encryption table indexed by cell value against our
94-entry table indexed by `value − 33` with a different guard (V3), and the tail
representation past the page window (V5). Only V2 and V4 were exercised. The
programs are three and four instructions long. No claim about Turing
completeness, Unicode I/O, the `canonical` loader, or any program of realistic
size. Read `docs/F13_UNSHACKLED_K19_PREGISTRATION.md` before quoting any number
from here.
