# DIFF: Classic vs Unshackled

| Axis | Classic (malbolge.py) | Unshackled (Unshackled.c) | Semantically load-bearing? |
|---|---|---|---|
| Memory size | `3^10 = 59049` | unbounded (trie, lazy) | YES (this is the entire question) |
| Width | always 10 trits | `rotwidth` starts in [10,15], grows | YES |
| rotate | fixed 10-trit rotate | rotate padded to rotwidth | YES |
| crazy | width 10 fixed loop `range(10)` | over width of operands, `n->width` | YES |
| addressing | `c % MEM_SIZE` implicit via array | trie; no wrap | YES (wrap = (3^10)-behavior) |
| memory init | full array, crazy-fill | lazy trie, crazy-fill via `initial_values` | NO — shape differs, result same for k=10 |
| eager vs lazy | eager allocation | lazy trie | NO (optimization) |
| `pos` accumulator | `c` only | `pos = c` after jmp; explicit `pos` reg | NO (equivalent, observable) |
| I/O | `ord(c)` / `a % 256` | Unicode codepoints, EOF = -1, `\n` special | YES but orthogonal |
| determinism | yes | no — `srand(time(NULL))` | YES for reproducibility |

## Conclusions

1. **All width-dependent behavior is in: crazy loop bound, rotate multiplier,
   memory size / wrap modulus.** Everything else is syntax or host I/O.
2. `Unshackled` is NOT a `Malbolge(k=19)`. It's `Malbolge(dynamic_width,
   growth_policy, unicode_io)`. Parameterizing k alone doesn't reach
   Unshackled; you also need the `det_growth_policy`.
3. **Free = parametric width + pluggable growth policy.** `M_10 = Classic`
   is `Free(10, fixed, ascii_io)`. `M_19 = Unshackled` only if we also adopt
   its growth policy and Unicode I/O. Whether `M_19` reproduces Unshackled
   bit-for-bit depends on whether the `srand(time(NULL))` path matters for
   tested programs.
