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

## Correction (2026-10-18) — appended; the third bullet above is stale, and a real
program reaches the frontier far earlier than the synthetic witness

Two things changed since the 2026-09-05 correction. Neither rewrites the text
above: it stays exactly as it was written, and this section is what supersedes it.

**1. Repeated widening is no longer `NOT_DEMONSTRATED`.** The bullet "Repeated
widening (`11 -> 12 -> ...`): NOT_DEMONSTRATED" is superseded by
`evidence/f9_repeated_frontier.json` (phase M5, claim `REPEATED_WIDTH_WIDENING`,
`status: DEMONSTRATED`, `verdict: PASS`): witness `tests/frontier_witness.txt`,
190 000 bytes, sha256 `3370003c…`, `policy: epochal`, `memory_limit: null`, boot
width 10 — two events, `10 -> 11` at step 59050 (`c = d = 59049`) and `11 -> 12`
at step 177148 (`c = d = 177147`), `final_width: 12`. `docs/FREE_SEMANTICS.md`
already carried this row as C8; this document had not caught up, and that
inconsistency is the drift being closed here. Still unclaimed: any behaviour
**beyond** `w = 12`.

**2. On a real program the frontier is not reached by walking to it.** The F9
witness is a linear pointer march, so its crossing lands exactly on `3^w`. Real
Malbolge assigns pointers (`movd d`, `jmp c`), so it can land on the frontier far
earlier. Measured on Lutter's quine in `evidence/f10_quine_epochal_20261018.json`:
the earliest Zig trace divergence between `classic` and `pure_fixed` is step
**1229** — `d` becomes `3^10 = 59049` there, and Classic wraps it to address 0
while the unbounded profiles read the cell at `3^10` — and the Python core's event
log widens at step **1230** (`{from: 10, to: 11, step: 1230, c: 1344, d: 59049}`).
Not 59050. So the *step* recorded by the synthetic witnesses does not generalise;
the invariant does. (The Zig core counts `WIDEN` events without timestamping them,
which is why the widening step is quoted from the Python log; `compare_quine_epochal.py`
first established that the two cores agree on every profile at the bounded budget.)

**3. What this document cannot say, and F10 can.** Everything above holds on the
value machine: at width `k` no operation produces a value with more than `k` trits.
That proof says nothing about whether the unbounded profiles *behave* like Classic on
a program that actually runs. On Lutter's quine they do not. `classic` halts at
69 547 437 steps printing its own 59 852 bytes, and the stdout sha256 equals the
input program's — the quine reproduces under our Zig core. `pure_fixed`, which has
**no growth policy at all** and only the address wrap removed, halts at 6 521 steps
having emitted 1 byte. `epochal` halts at 8 761 steps having emitted none. The
pre-execution memory images are identical for all three profiles (`c455d288…`, with
no first addressed difference), so this is an addressing effect produced during
execution, not a load effect — and the `pure_fixed` control localises the cause to
removing the wrap, not to widening. `docs/HONESTY_LEDGER.md` entry 29 records the
measurement.

**Reading it as "a new Malbolge".** `Free` with `mem_limit = null` is now a
measurably different machine from Classic on a real self-reproducing program, not
merely a re-parametrisation of it. The other half of the statement matters just as
much: the difference is the removal of the address wrap, which is part of the Classic
definition, so `epochal` is not a *falsification* of Classic-compatible growth — it
is a different family member, and `fixed` with `mem_limit = 3^k` remains Classic
(entry 24, F4c).

