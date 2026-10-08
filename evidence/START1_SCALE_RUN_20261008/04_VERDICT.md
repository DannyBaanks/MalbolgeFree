# Parametric boot1 sweep — measured 2026-10-08

[CURRENT] PARAMETRIC_1_TO_20_MEASURED_SCOPED. Twenty fresh VMs booted at
width1 and reached targets1 through20. Target20 executed1,162,261,468 steps,
recorded19 real frontier widenings, and stopped MAX_STEPS at width20.
No runtime modification; the observation-only copy logs frontier events.

Peak RSS at20:6,195,867,648 bytes (5.770 GiB); executable wall time68.7993s.
Time includes source generation, loading, execution and hashes, excluding build.
Small rows include process launch overhead and do not establish instruction speed.
Every allocation gate allowed its rung; target20 budget9,440,221,593 bytes.
This sweep ends at20 by design; it did not test21 or locate the RAM ceiling.

Each run has classification PARAMETRIC_ASCII_OUTSIDE_BOOT_WORD: all initial
source cells are printable ASCII>=33 while boot width1 has range0..2.
The loader accepts these cells. This measures the current parametric core,
not a closed-word1-trit language. At target5, bounded trace audit found fetched
cells outside the active range at widths1,2,3 (3,6,18 respectively), and32
out-of-range encryption results among53 encrypted cells at width4.
EOF sentinel is not classified as an ordinary cell. Full runs have no giant trace.

Controls: targets1..5 original Zig / observed Zig / repeated observed Zig agree
on execution fields and source/stdout hashes; Python independently agrees.
All three parser tests passed. A prior harness failure assumed encrypted>0;
small target1 legitimately encrypted zero cells. Failure and correction are
preserved in START1_SCALE_CI_20261008/local_validation; runtime was not changed.

Target20 source SHA matches the earlier boot10 experiment, but stdout SHA
is fecf7ad8a2732d3078905a1b915fb2505c314fdc03675e612bb1e13374c96bca,
which differs from boot10's84b36064019d339f445bfa627609f38d897bde7db5f0398393851bf2ba3df770.
Boot1 encrypted927,336,235 cells, boot10 encrypted927,336,249. This is a separate
execution family; do not pool rows without boot_width.

NOT_DEMONSTRATED: shrinking an existing VM; closed-word semantics at tiny
widths; equivalence with historical Malbolge variants; unbounded growth;
width21 execution; runtime/u64 widening; universal RAM-to-width law;
performance comparison between different runner runs. RAM projections from
the earlier boot10 experiment remain projections, not new measurements.

Evidence: raw logs, source, environment snapshots, limits, commands, hashes,
verdict and derived measurements.csv. Raw evidence was copied byte-for-byte.
