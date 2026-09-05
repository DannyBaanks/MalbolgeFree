# COMPOSITION — Classic + Unshackled = Free?

| Property | Classic (1998) | Unshackled (2017) | Free (2026-09) | Verdict |
|---|---|---|---|---|
| trit width | 10 fixed | initial 10-15 random, grows by padding on rot | any k, set at runtime | generalizes |
| memory addressing | wrap 3^10 | unbounded (trie) | `wrap = 3^k` or `null` | generalizes |
| memory init | eager 3^10 fill by crazy chain | lazy trie with crazy-chain initial_values | lazy map + crazy chain with 6-period proof | generalizes |
| crazy width | 10 fixed | operand-max | any k parameter | generalizes |
| rotate | 10-trit rotate | pad operand to current rotwidth, then rotate | `rotate(v, k)` with k parametric | generalizes |
| encryption xlat2 | yes | yes | yes | unchanged |
| I/O | chars (mod 256) | Unicode codepoints | byte-level (Classic fidelity) | narrower than Unshackled |

## The composition claim (Danny's version)

Under the *interpretation* Danny proposed in-session:

    ω is not a numerical bound. ω is the name of the composition
    where the runtime discovers k via the execution frontier.

That reading works — `epochal` growth policy in `src/malbolge_free.zig` does
precisely this. The earlier naive reading of ω ("no bound ever, history
rewritten freely") collapses because rotate breaks projection, but the
epochal reading survives: **history written under a given k stays fixed;
future steps use the new width.**

## Outcome table

| Claim name | What it means | Status |
|---|---|---|
| CLASSIC + UNSHACKLED = FREE | Both compositional instances match under Malbolge(k) | DEMONSTRATED |
| Malbolge^ω (old gloss) | runtime has no fixed bound and freedom to widen mid-run | DEMONSTRATED (under epochal) |
| Malbolge^ω (naive) | runtime dynamically rewrites width + history at will | DESTROYED (rotate is not injective across k) |

The seductive ω is the *epochal* one: the witness crosses 3^10 without
redoing anything, merely advancing c 59050 times.

## Chanzazo — "Desperdicio final"

Classic(10) + Unshackled(dynamic) = Free(k that detects the boundary)

Not "reach for 19." Not "pick a big number." Just: **stay true at whatever
k the execution needs**, from step 59050 on, Malbolge is allowed to
expand.

That's the language's politeness: it doesn't care what k is, it just needs
you to give it a choice.
