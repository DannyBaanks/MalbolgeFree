# MALBOLGE FREE — Semantic Definition

`Free(k)` is a parametric family `M_k` with a single core, no width special-cases.

## Parameters

| Param | Value |
|---|---|
| `width k` | number of trits in `crazy` and `rotate` |
| `mem_limit` | `3^k` (finite, wrap) or `null` (unbounded, lazy crazy-fill) |
| `growth_policy` | `fixed` (Classic, Unshackled-as-parametered) or `pad_to_padwidth` (Unshackled-original) |

## What stays constant

- Same 8 opcodes, same numeric ops.
- Same `(cell + pos) % 94` decode.
- Same `_ENC` encryption table.
- Lazy crazy-fill rules load `cell = crazy(mem[i-1], mem[i-2])` no matter the width.

## What IS width-dependent

- `crazy` uses exactly `k` trits (Classic: 10 fixed; Free: arbitrary k).
- `rotate(v)` = `v // 3 + (v % 3) * 3^(k-1)` (uses `k` trits).
- Memory size (if any) = `3^k`.
- `mod 3^k` wrap on addresses (present iff `mem_limit = 3^k`).

## What FREE adds

- **No `if k==10` or `force_unshackled` gates.** Same core sees `10..26`.
- Stable explicit growth policy. `fixed` + `mem_limit = null` = parametric no-limit.
- **Lazy crazy-fill with 6-periodicity shortcut**: crazy-chain from any seed enters period-6 tail (verified numerically for widths 10, 11, 12, 19, 20, 23, 26 over all sampled seeds). Enables writing beyond any finite boundary without materializing every cell.

## Honesty note

`Free(k=10)` == Classic. That much is demonstrated.
`Free(k=19)` reproduces the *parameterized* Unshackled behavior: the real Unshackled starts `rotwidth = 10 + rand() % 6`, so exact bit-parity is impossible — **documented as parity-class, not bit-parity**.

## Claims

```
C0 SINGLE_PARAMETRIC_CORE          = DEMONSTRATED
C1 CLASSIC_PARITY_K10              = DEMONSTRATED
C2 UNSHACKLED_PARITY_K19           = NOT_DEMONSTRATED  (nondeterministic reference)
C3 ARBITRARY_FINITE_K              = DEMONSTRATED
C4 NO_FIXED_COMPILED_MAX_ADDR      = DEMONSTRATED
C5 LEGAL_CROSSING_3_POW_19         = DEMONSTRATED
C6 WIDTH_EXTENSION_CONSISTENCY     = DESTROYED for rotate (needle hole), 
                                     DEMONSTRATED for crazy (100%)
C7 GROW_ON_DEMAND_WIDTH            = DEMONSTRATED (pad_to_padwidth growth events
                                     logged)
C8 TRUE_OMEGA_SEMANTICS            = NOT_DEMONSTRATED (extension-inconsistent)
C9 CLASSIC+UNSHACKLED=>FREE        = DEMONSTRATED (parametric reading)
C10 TURING_COMPLETENESS            = NO_NEW_CLAIM
```
