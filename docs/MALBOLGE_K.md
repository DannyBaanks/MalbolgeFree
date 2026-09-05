# MALBOLGE(k) — the parametric model

## Definition

`Malbolge(k, init_policy, crazy_width, rotate_width, io_policy)` where:

- **k**: initial/total width parameter (integer ≥ 1). In Classic, `k = 10`.
- **init_policy**: how memory cell values are derived when first accessed
  (eager `3^k` array vs lazy trie).
- **crazy_width(w1, w2) → width**: how many trits `crazy(a, b)` consumes
  (Classic: always k; Unshackled: max(w1, w2)).
- **rotate_width(w) → width**: how many trits `rotate(v)` produces
  (Classic: k; Unshackled: pad to rotwidth).
- **io_policy**: passthrough width (Classic: byte-sized-ish; Unshackled: Unicode).

## Byte code mapping (width-independent)

| op | meaning | width touches |
|---|---|---|
| 4  | jmp  | none (load `c = mem[d]`) |
| 5  | out  | none (α-fold of `a % 256`) |
| 23 | in   | none |
| 39 | rot  | YES — result width := rotate_width(w(v)) |
| 40 | movd | none (`d = mem[d]`) |
| 62 | crazy| YES — width(crazy_width(w(a), w(mem[d]))) |
| 68 | nop  | none |
| 81 | hlt  | none |

## Key insight: rot is the width valve

Classic: `rot(v, k) = v // 3 + (v % 3) * 3^(k-1)`. `w = k` fixed.

Unshackled's trick: `rotate_r(n, rotwidth)` ensures `n.width ≥ rotwidth`
**before** rotating. A rot is `v // 3 + (v % 3) * 3^(rotwidth - 1)`. If `v`
was small (10 trits) and rotwidth is 20, the result has 20 trits, then any
crazy using it inherits width 20.

**Therefore dynamic width = rotate-injected width + data flow.** The "memory grows
when values grow" story is driven by `rot`.

## What M_k looks like

For `Malbolge(k)`:
- cells: values in `[0, 3^k)`
- happen to need wrap around `3^k` for address arithmetic (`c = (c + 1) % 3^k`)

So `M_k` exists iff `3^k` is representable. This is the finite memory that
Classic called "the whole machine".

## Proposed free

`Free` = let k be a runtime value, initially 10, and let `rotate_width(w)` and
`crazy_width` be pure functions of the operands, NOT a global clamp. Then
grow `k` only when a rotation produces a value whose width exceeds it.

If this works:

- `Free | k=10, growth=off` = Classic
- `Free | k=10, growth=det_padding` = Unshackled-like
- `Free | k=None, growth=det_padding` = Free ^ω^
