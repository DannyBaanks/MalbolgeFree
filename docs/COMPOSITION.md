# COMPOSITION — Classic + Unshackled = Free?

| Property | Classic (1998) | Unshackled (2017) | Free (2026-09) | Verdict |
|---|---|---|---|---|
| trit width | 10 fixed | initial 10-15 random, grows by padding on rot | a variable `w`, initially 10 | generalizes |
| memory addressing | wrap 3^10 | unbounded (trie) | `wrap = 3^k` or `null` | generalizes |
| memory init | eager 3^10 fill by crazy chain | lazy trie with crazy-chain initial_values | lazy map + crazy chain with 6-period shortcut | generalizes |
| crazy width | 10 fixed | operand-max | any width parameter | generalizes |
| rotate | 10-trit rotate | pad operand to current rotwidth, then rotate | `rotate(v, w)` with `w` parametric | generalizes |
| encryption xlat2 | yes | yes | yes | unchanged |
| I/O | chars (mod 256) | Unicode codepoints | byte-level (Classic fidelity) | narrower than Unshackled |

## What composition means here: FIXED WIDTH -> VARIABLE WIDTH

Classic has a constant: the width is 10, full stop. Free replaces that
constant with a variable `w`. One run of Free can be *composed* of stretches
executed under different values of `w`:

```
EPOCH 1   steps where c, d < 3^10        w = 10
              |
              | frontier: c reaches 3^10 = 59049
              | anchor: everything produced under w=10 is kept, untouched
              v
EPOCH 2   steps from there on            w = 11
```

Composition does **not** mean infinity. It means a single execution can be
made of segments, each segment running under one finite value of the same
variable. `w=10` during epoch 1, `w=11` during epoch 2. Each individual step
always runs under one ordinary finite integer.

## Why the past is not redone

Measured fact (`evidence/f8_check.py`):

```
rotate(v, 10)  compared across widths:  agrees 9/27  (33.3%)
crazy(a, b)    compared across widths:  agrees 729/729 (100%)
```

So `rotate(v, 10)` does **not** have to equal a width-11 rendering of
`rotate(v, 10)`. The two widths are not interchangeable views of one run.
If Free claimed "the run at `w=10` and the run at `w=11` are the same
computation", rotate would destroy that claim on the spot.

Free claims something narrower and sequential:

    first the run is at w = 10
    then the run is at w = 11
    and the steps already executed at 10 are never reinterpreted at 11.

The rotate counterexample stays in the repo precisely because it draws this
line: no simultaneous-equivalence claim survives. Sequential-execution claims
do.

## Outcome table

| Claim name | What it means | Status |
|---|---|---|
| CLASSIC + UNSHACKLED = FREE | Both are instances of the parametric machine | DEMONSTRATED |
| FRONTIER_WIDTH_WIDENING | one run, two widths (`10 -> 11`), history intact | DEMONSTRATED (`tests/t_frontier_moment.zig`) |
| REPEATED_WIDTH_WIDENING | frontier after frontier, `11 -> 12 -> ...` | DEMONSTRATED for `10 -> 11 -> 12`; beyond 12 unclaimed |
| rewrite history under a new width | recompute the past at `w+1` | DESTROYED (rotate is inconsistent across widths) |

## Chanzazo — "Desperdicio final"

Classic(10) + Unshackled(dynamic) = Free(a variable `w` that notices the wall
when it gets there).

Not "reach for 19". Not "pick a big number". Just: **stay honest at whatever
`w` the execution actually needs**, from the step where `c` crosses the old
frontier on, Malbolge is allowed to run wider.

That's the language's politeness: it doesn't care what `w` is. It just needs
you to give it a choice.
