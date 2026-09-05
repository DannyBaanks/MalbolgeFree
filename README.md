# Malbolge Free

```
Malbolge Classic    :   >:(
Malbolge Unshackled :   >:D
Malbolge Free       :   ^ω^   (Malbolgato)
```

Parametric Malbolge runtime in Zig. One core, any trit width `k`, no
hardcoded 3^10 prison. *And* execution-boundary widening works: `c`/`d`
move by `+1` per step until they touch `3^k`, at which point the runtime
widens the width **once** and carries the prior trace along. No rewriting.

## What this is

`MalbolgeCore(width, mem_limit, growth_policy)` — one core, three knobs.

| policy | width evolves? | why? |
|---|---|---|
| `fixed` | no | Classic semantics |
| `pad_to_padwidth` | yes — by value overflow | **DESTROYED** by rotate (see evidence) |
| `epochal` | yes — by address frontier | **PROVEN** viable for `widen` |

## Demonstrated

**PARITY**: classic corpus (`hello.mal`, 3 echos, reproducer, quine) — 6/6 sha256
matches against the Python reference at k=10.

**K-ARBITRARY**: memory stays sane at k ∈ {10, 11, 12, 19, 20, 23, 26}.

**FRONTIER WIDENING**: a 70000-character program of pure `in`/`out`/`nop` ops
(constructed in `evidence/gen_frontier_witness.py`) runs until `c` crosses
`3^10 = 59049`; the epochal trigger fires exactly once, `padwidth` bumps
`10 → 11`, and the trace to that point is untouched. Confirmed:

```
WIDEN at step=59049, max_addr=70136, padwidth=11
```

**3^19 CROSSING** (legal-movd witness): the program `' & % $` executes
movd twice over lazy crazy-fill and ends with `d = 1743392169 > 3^19 =
 1162261467`. Both Python and Zig agree on the exact register values.

**WIDTH-EXTENSION BROKENNESS** (`fixed` interpretation): rotate widened in-place
produces a result inconsistent across widths 33% of the time — rotate has
`v % 3` aliased onto the HI trit uniquely at width `k`, and widen after the
fact changes the value. So `pad_to_padwidth` is gone from the claim pool.

**LAZY-FILL PERIODICITY**: the crazy chain enters a period-6 cycle at
`program_len + 2` regardless of width (verified numerically across widths
10..26 and several seed pairs). This gives O(1) lazy-cell lookup.

## Not Demonstrated / Destroyed

| Claim | Status |
|---|---|
| TRUE_OMEGA_SEMANTICS | **NOT_DEMONSTRATED** |
| UNSHACKLED_PARITY | **NOT_DEMONSTRABLE** by construction (uses srand(time(NULL))) |
| VALUE-OVERFLOW WIDENING | **DESTROYED** (rotate breaks injectivity) |
| FRONTIER WIDENING | **DEMONSTRATED** ^ω^ |

## The "Purrfect" Badge

The pattern that makes this what it is: **memory values wrapped in crazy stay
in-byte**, but memory addresses (c, d) keep advancing through the address
space even when mem_limit=null. Crazy is width-agnostic. Rotate is not. So
the place your width change happens has to be "pointer advancement," not
"cell value." Built this project around Danny spotting that.

## Run

```bash
# corpus parity (Python biz op references)
py evidence/compare_f4.py

# frontier widening evidence (zig)
zig run tests/t_frontier_moment.zig

# crossing witness (validator)
zig run evidence/f7_witness.zig
```

Every evidence file prints its own verdict; nothing is dispersed in nerts-only
markdown. All raw bytes are in evidence/.

## License

MIT ^ω^

(It's the cat. It's always the cat.)
