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

`Free` = let the width be a runtime variable `w`, initially 10, and let
rotate/crazy consume `w` instead of a global clamp. Where `w` can change:

- value-driven growth (rotate/operand overflow) was the first idea — it is
  **destroyed**, because `rotate` results do not survive a width change
  (see `evidence/f8_check.py`, 33.3% agreement).
- address-driven growth (widen when `c` or `d` reaches `3^w`) is what shipped
  as the `epochal` policy. One transition (`10 -> 11`) is demonstrated;
  repeated widening is not.

Instantiation guide:

- `Free | w=10, fixed, wrap 3^10` = Classic
- `Free | w=10, growth=det_padding` = Unshackled-like (not defended — C6)
- `Free | w=10 start, epochal, unbounded memory` = Malbolge Free ^w^

(`w` always holds a finite integer while running. Nothing here is infinite:
each epoch is just a stretch of steps executed under one value of `w`.)
