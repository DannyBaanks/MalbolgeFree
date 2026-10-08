# Real RAM scale — 2026-10-08

MEASURED_WIDTHS: 14,15,16,17,18,19,20
MAX_MEASURED_WIDTH: 20
NEXT_WIDTH: 21
NEXT_EXECUTED: false
STOP: preventative RAM budget + dense u32 representation ceiling
UNBOUNDED_WIDTH_GROWTH: NOT_DEMONSTRATED

[GitHub run 37848647590](https://github.com/DannyBaanks/MalbolgeFree/actions/runs/37848647590)
executed harness commit f472b42953a6cece12d4615a41219586eaffe2b7 on Ubuntu 24.04.
The artifact's original hashes were verified locally after download. Every
rung is a fresh VM booting at 10; it calls vm.run once and crosses every
frontier up to its target. Rungs are separate runs, not a single persistent
machine shared between benchmarks. Runtime source stayed unchanged.

| Target width | Real steps | Peak RSS (GiB) | Executable time (s) |
|---:|---:|---:|---:|
| 14 | 1,594,324 | 0.0086 | 0.136 |
| 15 | 4,782,970 | 0.0244 | 0.405 |
| 16 | 14,348,908 | 0.0719 | 1.258 |
| 17 | 43,046,722 | 0.2143 | 3.926 |
| 18 | 129,140,164 | 0.6419 | 11.612 |
| 19 | 387,420,490 | 1.9255 | 35.604 |
| 20 | 1,162,261,468 | 5.7709 | 110.134 |

Time includes generation/load, real VM execution, source/stdout hashing,
excludes compilation. It is measured by the collector around GNU time, with
small launch/wait overhead. RSS is GNU time's child-process peak. No large
source or stdout was stored in Git. Small binary hashes, generator source,
source/output lengths and hashes preserve reproducibility.

The second full target 20 execution has identical result fields, WIDEN events,
source hash and stdout hash to the earlier standalone E20 run. This is
determinism in one Zig implementation, not a second-engine parity result.

## Why 21 was not attempted

Measured MemAvailable before 21: 15,744,765,952 bytes (~14.66 GiB).
The 60% budget was 9,446,859,571 bytes (~8.80 GiB). Scaled previous RSS with 25%
margin predicts 23,236,684,800 bytes (~21.64 GiB), above budget. That extrapolation
assumes unchanged representation and is not a prediction for a u64 engine.

Separately, dense u32 cannot represent width 21 values. Current hash-storage
estimate with reserved capacity is 286,954,626,938 bytes (~267.25 GiB), also
above budget. No width 21 source configuration, binary build or execution log
exists; the verifier checks that the gate stops before those actions.

Even a hypothetical dense u64 representation would require at least
31,381,068,714 bytes (29.23 GiB) for source+array at 21, before output/runtime
overhead. It was neither implemented nor tested. This raw lower subtotal
alone exceeds the GitHub runner's physical RAM; relaxing the 60% gate would
not make this representation fit here.

## Larger machines: storage projections only

| Ideal RAM (GiB) | Budget 60% (GiB) | Current storage gate ceiling | Hypothetical wider dense storage gate ceiling |
|---:|---:|---:|---:|
| 16 | 9.6 | 20 | 20 |
| 32 | 19.2 | 20 | 20 |
| 64 | 38.4 | 20 | 21 |
| 128 | 76.8 | 20 | 21 |

These are **not measured capabilities**. Model assumes all physical RAM is
available, then requires storage minimum plus 25% margin within 60% of that.
Runtime/output overhead, implementation limits and time can reduce ceilings.
The current column chooses dense u32 up to 20 and the hash budget beyond it;
it does not assert hash implementation conformance at untested larger widths.
The hypothetical column assumes u64 through 40, u128 thereafter, neither of
which exists as a dense runtime here.

For context, hypothetical source+u64 array minima: 21=29.23 GiB,
22=87.68 GiB, 23=263.03 GiB. Thus 22 could be a future investigation on 128 GiB
with a different approved resource budget and implementation, but it fails
this experiment's conservative budget and has not been run.
Width 30 would already need ~561.77 TiB for source+u64 array; width 60 source
alone is 14,130,386,091,738,734,504,764,812,068 bytes. 128 GiB does not approach 60
for this linear witness.

Scope is the address-frontier witness, not arbitrary fixed-width programs.
A tiny fixed-width program can touch little memory; word width does not by
itself force eager allocation of 3^w cells. No universal RAM-to-width theorem.
No OOM, no unrelated process termination, no new runtime representation.
EOF mismatch with Nagoya remains a separate result.

Raw runs.json, gates.json, command logs and environment snapshots are preserved
byte-for-byte. MEASUREMENTS.csv provides exact byte/time values for plotting.
Verification and human instructions: [GUIA](../RAM_SCALE_CI_20261008/GUIA.md).
