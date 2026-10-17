# Vendored canonical Classic oracle: `malbolge.py`

Copied **verbatim** from another repository so that canonical parity can be
*measured* by CI instead of skipped by it.

| field | value |
|---|---|
| source repository | `https://github.com/DannyBaanks/MALBOLGE` (directory `ISyCo Git/MALBOLGE`) |
| source file | `malbolge.py` |
| source commit | `bf4d6fab2052804b2877d29d75c670e1d63f3fa2` |
| SHA-256 of this copy | `e64af4f0d51712e99fdf205e1a102587e4e52c863302384b5d2599f6edf3222b` |
| license | MIT, `Copyright (c) 2026 DannyBaanks`. The source repo's `LICENSE` is copied verbatim next to this file (`vendor/canonical_malbolge_py/LICENSE`, sha256 `709121601d459258fdc9a0d7f40473571250e9f13335e42bbfc2290b343c9fa5`); it is byte-identical to this repository's own root `LICENSE`, so nothing changes for downstream users |
| copied | 2026-10-17, `diff` against the source file reports no differences |
| edits | none. If you edit this file, update the pinned `VENDORED_PY_SHA256` in `evidence/compare_f4_canonical.py` and record it here — otherwise the gate refuses to run |

## What it is

A self-contained Classic Malbolge interpreter written clean-room from the public
language description (documented behavior of the 1998 interpreter, as summarized
in Iizawa 2005, Appendix C). It is **not** a copy of anything in `src/`: it
imports nothing from this repository, so it can falsify our two cores.

Its EOF convention is the canonical one:

```python
EOF_VALUE = 59048   # 3**10 - 1
```

Measured on this very copy, 2026-10-17: `in,out,halt` with empty stdin reports
`HALTED` in 3 steps and emits `b'\xa8'` — `(3**10 - 1) % 256`, the same byte as
Olmstead's `malbolge.c` (`if ( x == EOF ) a = 59048;`). An interpreter that emits
`0xff` here is not canonical and must not be used as this oracle.

## Why it is vendored

`evidence/compare_f4_canonical.py` needs a canonical interpreter, and before this
copy existed the only ones available lived in sibling checkouts outside this
repository. Consequence: on a fresh clone (including both CI runners) the gate
printed `F4c_ORACLES_MISSING` and the harness reported
`SKIP (NOT_DEMONSTRATED, missing external input)` — honest, but it meant the
canonical-parity claim was established on one machine only.

Vendoring moves the claim to "reproducible from a fresh clone", at the cost of
the oracle now living inside the repo under test. That cost is paid for with a
pin: the gate compares this file's SHA-256 against `VENDORED_PY_SHA256` and
exits **4** (`F4C_VENDORED_ORACLE_DRIFT`) rather than reporting parity if they
differ. A silently edited oracle producing a green parity verdict is the exact
failure mode that hid the EOF bug for a month, so drift is a hard failure, never
a skip and never a PASS.

## Warning: this repository contains a *different* `malbolge.py`

`evidence/malbolge.py` (older, still present) assigns `a = -1` at end of input —
the non-canonical convention, the same family as the bug fixed on 2026-10-17.
`MALDOOM/vendor/malbolge/malbolge.py` is likewise non-canonical. Neither is used
by the F4c gate, which imports only this vendored file (or an explicit
`MALFREE_MALBOLGE_REFERENCE` override). Do not point the gate at
`evidence/malbolge.py`: it cannot falsify the bug it shares.
