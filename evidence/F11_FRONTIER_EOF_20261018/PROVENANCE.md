# Annex: raw F11 captures

Commentary written for this annex; it regenerates nothing and re-formats nothing.
The measurement itself lives in `evidence/f11_frontier_eof_20261018.json`, produced
by `evidence/compare_f11_frontier_eof.py`. These are the bytes the machine printed.

| file | what it is |
|---|---|
| `console.txt` | the checker's own stdout plus its `F11_RC=` line: the three profile rows per core, 15 `MATCH` expectation lines, the `max_addr_touched` disclosure, `F11 EXPECTATIONS=15 MATCH=15 FALSIFIED=0`, `F11 FRONTIER_EOF_DIFFERENTIAL=PASS`, `F11_RC=0` |
| `resource_usage.txt` | GNU `/usr/bin/time -v` for that same process: wall 0:01.26, user 1.11 s, system 0.14 s, peak RSS 92 412 kB, `Exit status: 0` |

Command, run 2026-10-18 on this machine (Zig 0.16.0, Python 3.12.3), from the
repository root, with no external input:

```
/usr/bin/time -v python3 evidence/compare_f11_frontier_eof.py \
    --output evidence/f11_frontier_eof_20261018.json
```

The budget is `MALFREE_F11_BUDGET`, default 60 000 steps — which is why the
`classic` row reads `MAX_STEPS@60000` rather than a halt: this program needs
62 239 852 steps to self-reproduce, and F11 is not measuring that (F12 is).

## What the numbers say

- `pure_fixed` `in` returns **59 048 = 3^10 - 1** at step 7 541.
- `epochal` `in` returns **177 146 = 3^11 - 1** at steps 25 687 and 25 702, because
  the core widened 10 -> 11 at step 1 230 (`{from:10,to:11,step:1230,c:1344,d:59049}`).
  Same source line in both cores, different value from Classic's: EOF is
  **width-relative**, so a Classic program's hard-coded EOF detector stops meaning
  "end of input" once the machine has widened.
- Both cores agree on every compared observable (8 fields x 3 profiles), and the
  controls `reproducer.mal` (1 948 steps, 96 B) and `hello.mal` (40 steps, 12 B)
  are profile-independent — so the difference is not an instrumentation artifact.

## Disclosed, not smoothed over

`max_addr_touched` is deliberately **not** a compared field. The two cores define it
differently — Python updates it only on writes (`src/malbolge_core.py:156-161`), Zig
on reads and writes (`src/malbolge_free.zig:337-338`) — and the measured deltas
(`classic` 0, `pure_fixed` +2, `epochal` +1) are that definitional gap, not a
behavioural divergence. Cite it only together with the core that measured it.

Expectation **E13 was falsified by a defect in this checker before it passed**: the
Zig driver's `field=stdout_prefix_len` diff line reports a *byte index*, not a step,
and folding it into a step predicate produced a phantom P1 violation. It is now
filtered out and printed as `excluded_non_step_fields=['stdout_prefix_len']`. The
falsification was a bug in our own code, so it is recorded in the checker's
docstring rather than deleted.
