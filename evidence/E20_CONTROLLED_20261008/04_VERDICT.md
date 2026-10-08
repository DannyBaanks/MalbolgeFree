# Separate verdicts — 2026-10-08

EPOCHAL_19_TO_20: BLOCKED_RESOURCE_GATE / NOT_DEMONSTRATED

No target20 execution launched. The real witness starts at width 10 and calls
vm.run, but available memory was 5071921152 bytes (~4.72 GiB) with only
56102912 swap bytes free. Source+array alone needs 5811312388 bytes (~5.41 GiB),
exceeding the 3043152691-byte 60% budget. Disk free ~32.50 GiB meets its gate.
Hardware gate is not a statement of mathematical impossibility.

Fixed20_NAGOYA_PARITY: FAIL — EOF echo mismatch, independently reproduced
in both Free cores against unmodified Nagoya C. See 03_NAGOYA_COMPARE.md.

MALBOLGE20_IDENTICAL_TO_FREE_EPOCHAL: NOT_CLAIMED
UNBOUNDED_WIDTH_GROWTH: NOT_DEMONSTRATED
GENERAL_SEMANTIC_EQUIVALENCE: NOT_DEMONSTRATED (EOF equivalence refuted)

Small-run regressions: 2 epochal tests, 2 real-full-loop tests, 4 dense
differential tests and 3 conservative tests passed; Python/Zig differential
also passed its three small cases and wrap-rejection control. Dense width21
rejection is covered. These are not proof of a billion-step run.

Dense rung15 ran twice: steps=4782970, width=15, growth=5, final_c=4782970,
cells=4783982, stdout_len=1577368, capacity=0. Aggregate RESULT lines identical.
Warm run: 0.27 s wall, peak RSS 36692 KiB. Cold compile+run: 13.81 s,
425900 KiB peak. GNU time measures the command tree peak, not a sum of
simultaneous RSS. The stock probe does not hash VM stdout or record individual
WIDEN events; no such observations are invented for calibration or E20.

NOT_DEMONSTRATED: E20 transition timing/trace, its final state/stdout hash,
unbounded growth, universal conformance, bit-exact reference state parity.
Historical rungs17-19 remain historical records, not fresh full executions.

Next H1 step requires a fresh gate with sufficient real MemAvailable and
minimal event instrumentation validated on small cases. No remote run,
process termination, existing evidence overwrite or runtime modification occurred.
