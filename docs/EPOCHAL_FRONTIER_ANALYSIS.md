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

`epochal` growth **from within** is structurally impossible. Width changes
must come from outside the machine (a reload event, a new phase, a program
signal). There is no semantically-grounded way to "grow" mid-run without
injecting a >k value by external action.

Honest verdict:

```
C5 CROSSING: DEMONSTRATED via explicit k=20 boot
ANCHORED_GROW_ON_DEMAND: structurally-not-feasible from internal triggers
```

Reframing `Free` uses of "ω": the parametric family `M_k` for any k is
REACHABLE, and on each run k is max. The trigger that a *Malbolge program
internally* decides to upgrade width does not exist, and this is a proof
not an omission.
