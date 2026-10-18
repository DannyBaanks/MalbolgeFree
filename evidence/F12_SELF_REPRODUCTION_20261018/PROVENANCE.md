# Annex: raw F12 captures

Commentary written for this annex; it regenerates nothing and re-formats nothing.
The measurement itself lives in `evidence/f12_selfreproduction_20261018.json`,
produced by `evidence/compare_f12_selfreproduction.py`. These are the bytes the
machine printed.

| file | what it is |
|---|---|
| `console.txt` | the checker's own stdout plus its `F12_RC=` line: program pin, both budgets, measured per-core wall seconds, three profile rows per core, 7 `MATCH` expectation lines (K1-K7), the four `F12 SCOPE` lines, `F12 EXPECTATIONS=7 MATCH=7 FALSIFIED=0`, `F12 SELF_REPRODUCTION_KNOWN_ANSWER=PASS`, `F12_RC=0` |
| `resource_usage.txt` | GNU `/usr/bin/time -v` for that same process: wall 1:52.97, user 112.82 s, system 0.06 s, peak RSS 84 044 kB, `Exit status: 0` |

Command, run 2026-10-18 on this machine (Zig 0.16.0, Python 3.12.3), from the
repository root, with no external input:

```
/usr/bin/time -v python3 evidence/compare_f12_selfreproduction.py \
    --output evidence/f12_selfreproduction_20261018.json
```

## Why the cost is what it is

The gate runs the program to its real halt under `classic`: **62 239 852 steps**, on
both cores. Measured inside that same process: Zig 63.1 s, Python 49.8 s — the rest
is the two bounded trace passes (`zig_trace=2000`) and process startup. This is why
`tests/run_all.py` gives F12 its own 900 s timeout instead of the 180 s default: on
Windows runners the same halt is plausibly 2-4x slower, and a default-timeout gate
would report a harness failure for a machine that was simply slower.

The two wrap-free profiles are cheap by comparison and are included to show they
*don't* reproduce: `pure_fixed` halts at 9 718 steps with 0 bytes, `epochal` at
25 729 with 3 bytes.

## What this gate is and is not

K5 compares our step count against the value three engines outside this repository
published on 2026-10-17 (`MALBOLGE-MB-DATABASE/quine/evidence/quine_53562_verification.json`:
the native C runner, `mb_ref`, and `mb_classic_indep.c`). That makes F12 a
**known-answer parity** gate: two cores here reach an answer already agreed on
outside here.

It is not an independent discovery of the quine, and it is not a claim about
`epochal`: `source_eq_stdout` is `True` only under `classic` (K7), and the
smallest-quine / ranking claims stay in the source repository, where the sweep over
an enumerated universe was actually done. `max_addr_touched` is not compared — the
two cores measure it by different rules, as F11 discloses.
