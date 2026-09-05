# Anchored / epochal width transitions — investigated, blocked by the structure

## Danny's point

Epochal widening: run at fixed `k`, freeze state as an **anchor**, widen to
`k'` prospectively (preflight) before executing ops that would exhaust the
current width, keep future transitions under `k'`, NEVER rewrite the past.

## Result: this is semantically sound but structurally blocked.

Why? Because under width `k`, **every op produces a k-trit value**:

- `crazy(a, b)` = k-trit output (k-trit inputs)
- `rotate(v)` = k-trit output
- `movd d = mem[d]` reads a k-trit cell
- I/O fits in 8 trits
- Lazy crazy-fill values: also k-trit

Under any current width `k`, you'd never legitimately see a value whose
`tritlen > k` — so the trigger "value doesn't fit" never fires. The machine
is structurally *monostable*.

The witness that crosses 3^19 works because we START at `k=20`, not because
we widened to it. The lazy fill there is already 20-trit large because the
width was 20 from the start. It demonstrates the *parametric family* is non-trivial;
it does NOT demonstrate dynamic widening from a small k.

## Honest verdict on the epochal variant

`ANCHORED_GROW_ON_DEMAND = NOT_DEMONSTRATED` (and honestly,
BORDERING ON `NOT_POSSIBLE` under Malbolge semantics: nothing in the
language produces a >k-trit value given only k-trit inputs).

But the epochal machine is still valid:

```
epochal(start_k=20) ≡ fixed(20)
epochal(start_k=10) ≡ fixed(10) ∀ever
```

That's parametric degeneration confirmed, not a bug.

## The rotate point stands

`rotate` was the only historical/observable candidate for widening (pad).
In `epochal`, `rotwidth` is fixed at the current epoch — rotate behaves
exactly as in `fixed`. Because the padding effect is only pro-growth when
width increases AFTER rotate, and our rule is preflight-only, epochal rotate
never grows.

## Naming

To avoid confusion:

- **MalbolgeFree(k)** — parametric core over arbitrary k + optional
  unbounded memory. C0-C5 work. This is the deliverable.
- **MalbolgeFreeEpochal(k₀)** — machine starting at k₀; blocked from
  widening by Malbolge's own closed-width design *on the value side*.
  (See the correction below: the shipped trigger is address-based and did
  fire once, `10 -> 11`.)

## Correction (2026-09-05)

This document analyzed **value-triggered** widening (widen when an op would
produce a value that does not fit in the current width). That analysis still
stands: inside a width-`w` machine no op produces a value wider than `w`
trits, so a value trigger can never fire.

The `epochal` policy that actually ships in `src/malbolge_free.zig` is
**address-triggered**: with `mem_limit = null` the pointers `c`/`d` advance
by one cell per step with no wrap, so `c` does reach `3^w`. The trigger fires
there and widens `w` by one. Measured once (`tests/t_frontier_moment.zig`):
`WIDEN step=59050 c=59049 d=59049 old_w=10 new_w=11`. So "epochal widening is
structurally impossible" is wrong as stated; the right statement is:
*value-triggered* widening is structurally dead, *address-frontier* widening
works and one transition is demonstrated. Repeated widening
(`11 -> 12 -> ...`) remains NOT_DEMONSTRATED.

Naming note: earlier drafts called the composition idea `ω` (`MalbolgeFreeω`,
`^ω^`). Retired on 2026-09-05 — the width is a finite-integer variable `w`,
and the omega naming suggested claims this project does not make.
