# Annex: raw F15 captures

Commentary written for this annex; it regenerates nothing and re-formats nothing.
The measurement itself lives in `evidence/f15_encryption_cascade_20261018.json`,
produced by `evidence/compare_f15_encryption_cascade.py` against the expectations
pre-registered in `docs/F15_ENCRYPTION_CASCADE_V3_PREGISTRATION.md`. These are the bytes
the machine printed.

| file | what it is |
|---|---|
| `console.txt` | the checker's own stdout: reference hashes, cores, 21 `MATCH` expectation lines (D1-D5, P1-P4, R1_C1_*, R2_C5_*, R3_C7_*, R4_SUB33_*), `F15 EXPECTATIONS=21 MATCH=21 FALSIFIED=0`, `F15 ENCRYPTION_CASCADE_DIVERGENCE_V3=PASS` |
| `resource_usage.txt` | GNU `/usr/bin/time -v` for that same process: wall 0.25 s, user 0.09 s, system 0.06 s, peak RSS 31 556 kB, `Exit status: 0` |

Command, run 2026-10-18 on this machine (Zig 0.16.0, Python 3.12.3, Linux
7.0.0-38-generic), from the repository root:

```
/usr/bin/time -v python3 evidence/compare_f15_encryption_cascade.py \
    --output evidence/f15_encryption_cascade_20261018.json
```

It needs the external reference, so a clone without `../MalbolgeLispSlop` beside
it exits **3** and the harness prints an explicit
`SKIP (NOT_DEMONSTRATED, missing external input)`; that is what CI shows for this
gate until a vendoring decision is made.

## What the numbers actually pin

* `D1`–`D5` — table properties: canonical `TRANSLATED` has 94 characters; reference `XLAT_CONCAT`
  has 141 characters ($27 + 100 + 14 = 141$); `XLAT_CONCAT[33:127] == TRANSLATED` (the 33-byte prefix
  shifts direct indexing to match $v - 33$); the disagreement set over $[0, 255]$ is exactly
  $[0, 32] \cup [127, 140]$ (47 values); all values in $[0, 140]$ converge to $[33, 126]$ in $\le 2$ steps.
* `P1`–`P4` — permutation and domain properties: cycle lengths on $[33, 126]$ are `[68, 9, 6, 5, 4, 2]`;
  iterated encryption matches across depths 1, 2, 5, 10, 50, 100 on all 94 characters (0 mismatches);
  sub-33 domain has 33/33 divergence (fixed point vs prefix mapping); high-byte domain has 14/14 divergence
  (fixed point vs suffix mapping); 100 000 random canonical samples match 100%.
* `R1` (`C1`, `b"ubO"`) — 3-cell baseline: halts at $c=2, d=2$, stdout `0xda`, 2 cells encrypted
  ($117 \to 111$ `'o'`, $98 \to 84$ `'T'`).
* `R2` (`C5`, `b"ubs`M"`) — 5-cell linear cascade: halts at $c=4, d=4$, stdout `b"AB"`, 4 cells encrypted
  ($117 \to 111$ `'o'`, $98 \to 84$ `'T'`, $115 \to 82$ `'R'`, $96 \to 60$ `'<'`).
* `R3` (`C7`, `b"ubs`q^K"`) — 7-cell linear cascade: halts at $c=6, d=6$, stdout `b"XYZ"`, 6 cells encrypted
  ($117 \to 111$, $98 \to 84$, $115 \to 82$, $96 \to 60$, $113 \to 108$, $94 \to 57$).
* `R4` (`C_SUB33`, `b"'bO"`) — Sub-33 cell mutation witness: step 1 executes `rot(39, 19) = 13` on cell 0.
  In `MalbolgeFree`, 13 is outside $[33, 126]$, so encryption is skipped (`encrypted_cells == 1`, only
  cell 1 is encrypted, cell 0 stays 13). In `bolge19`, $13 < 141$, so cell 0 is encrypted into `XLAT_CONCAT[13] = 32`.
  Demonstrates domain guard divergence on real program execution.

## What this annex is not

Not Turing completeness. Not parity with Lutter's original `Unshackled.c` (which calls `srand(time(NULL))`).
Read `docs/F15_ENCRYPTION_CASCADE_V3_PREGISTRATION.md` before quoting any number from here.
