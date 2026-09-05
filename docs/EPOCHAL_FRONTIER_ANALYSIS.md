# Frontier trigger analysis — STRUCTURALLY DEAD not just NOT_DEMONSTRATED

## The trigger Danny proposed

Execution-boundary trigger: when the next address needed by execution exceeds
the current width's frontier, widen BEFORE touching it.

```text
if next_address >= 3^epoch:
    widen(k -> k+1)
```

## Verdict on the trigger

This trigger is **structurally never fired** in Malbolge. Proof sketch:

At width k:
- `crazy(a,b)` → at most 3^k - 1
- `rotate(v)` → at most 3^k - 1
- lazy crazy fill: `crazy(mem[i-1], mem[i-2], k)` → at most 3^k - 1
- `movd d` sets d = mem[c], a stored value ≤ 3^k - 1
- `jmp c` sets c = mem[d], also ≤ 3^k - 1

`c` and `d` as registers are capped at 3^k - 1 because every value-computation
path returns a mod-3^k result. There is no mechanism internal to the width-k
machine that produces an address > 3^k - 1 to chase.

## The crossing witness revisited

The witness that crossed 3^19 uses `width=20` from boot. There, lazy fill
values at k=20 can be up to 3^20-1; `movd` consumes one and D becomes a
huge address. Now c or d exceed 3^19 — the trigger fires only because we
*started* at width 20, not because we grew at the boundary.

So the anchoring idea — start at low k, grow when a frontier is touched —
requires **an external event** to seed a big value. Lazy-fill chains alone
refuse to produce anything >3^k. Malbolge is closure-closed at 3^k.

## Consequence

`epochal` growth driven by **values** is structurally impossible. No op at
width `k` produces a value with more than `k` trits, so a value-based trigger
can never fire.

Honest verdict (as of the original analysis):

```
C5 CROSSING: DEMONSTRATED via explicit k=20 boot
VALUE-TRIGGERED WIDENING: structurally-not-feasible from internal triggers
```

## Correction (2026-09-05)

The "structurally dead" conclusion above covered the wrap-addressing case
(`mem_limit = 3^k`, where `c`/`d` are capped) and value-based triggers. The
shipped `epochal` policy runs with `mem_limit = null`: there `c` and `d`
increment by one cell per step with **no wrap**, so the *address* frontier
`3^w` is genuinely reachable — and the trigger fires. Measured once by
`tests/t_frontier_moment.zig`: `WIDEN step=59050 c=59049 d=59049 old_w=10
new_w=11`, exactly one event, then the program halts at step 70076.

So the corrected landscape is:

- **Value-triggered widening**: structurally dead (this document's proof
  stands).
- **Address-frontier widening, unbounded memory**: demonstrated once,
  `10 -> 11`, with the earlier trace untouched.
- **Repeated widening** (`11 -> 12 -> ...`): NOT_DEMONSTRATED — reaching
  `3^11 = 177147` would need a program that survives that many steps, and the
  recorded witness halts at step 70076.

The symbol `ω` used in earlier drafts of this note is retired: the width is
an ordinary finite-integer variable `w`, and these documents should not
suggest any infinite or ordinal claim.
