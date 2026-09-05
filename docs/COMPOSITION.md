# COMPOSITION — Classic + Unshackled = Free?

| Property | Classic (1998) | Unshackled (2017) | Free (2026-09) | Verdict |
|---|---|---|---|---|
| trit width | 10 fixed | initial 10-15 random, grows by padding on rot | any k, set at runtime or grown | generalizes |
| memory addressing | wrap 3^10 | unbounded (trie) | `wrap = 3^k` or `null` | generalizes |
| memory init | eager 3^10 fill by crazy chain | lazy trie with crazy-chain initial_values | lazy map + crazy chain with 6-period proof | generalizes |
| crazy width | 10 fixed | operand-max | any k parametric | generalizes |
| rotate | 10-trit rotate | pad operand to current rotwidth, then rotate | `rotate(v, k)` with k parametric | generalizes |
| encryption xlat2 | yes | yes | yes | unchanged |
| I/O | chars (mod 256) | Unicode codepoints | byte-level (to inherit Classic fidelity) | narrower than Unshackled |

## What the composition generates

`weird placements` — Classic's `HALT` insight (impossible under classic)
showed up at k=10 fixed + memory unbounded, because we key-decouple k and
wrap: `M_10(mem_limit=null) != Classic(kept: 59049)`. In classic, `c` wraps at
`% 59049`; Free does not wrap unless configured to. So `M_k(mem=unbounded)
extends Classic in a way Unshackled didn't try: not "big array", but "any
width + no bound."

## Status

Composition works in the parametric (non-conditional) sense only:

    FREE = union over M_k(k finite) with consistent lazy-fill

(True dynamic-ω collapse fails via rotate destruction shown in
`evidence/f8_check.py`. Only reflexive-unbounded parametric generation survives.)
