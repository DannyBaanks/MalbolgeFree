# Malbolge Free ^ω^

```
Malbolge Classic    :   >:(
Malbolge Unshackled :   >:D
Malbolge Free       :   ^ω^
```

Parametric Malbolge runtime in Zig. One core, any trit width `k`, no
hardcoded 3^10 prison.

## What this is

`MalbolgeCore(width, mem_limit, growth_policy)` — one runtime parameterized
by k. Classic is `Free(k=10, mem_limit=59049)`. Free proper is the same core
at arbitrarily larger k with lazy memoized crazy-fill — no array allocation
of 3^k, no preload cascade.

## Demonstrated

- **CLASSIC_PARITY_K10** — 6/6 corpus programs match Python reference
  (hello.mal step-for-step, echo runs, reproducer, quine machine)
- **ARBITRARY_FINITE_K** — k ∈ {10, 11, 12, 19, 20, 23, 26}, lazy fill stays
  6-periodic, no overflow into panic territory
- **LEGAL_CROSSING_3_POW_19** — the witness program `' & % $` (movd chain)
  ends with `d = 1743392169 > 3^19 = 1162261467` — verified by both Python
  and Zig on the same bits

## What broke on purpose

```
rotate(v=5, k=19) = 1162261201
rotate(v=5, k=20) = 2324522935
→ rotate(5,20) mod 3^19 = 581130801 ≠ 1162261201
```

`rotate` is width-dependent at the *result level* — it shifts trits into the
new top position of the ring buffer. Extension-consistency is destroyed
(33% of inputs diverge in my probe). That means: if you had a hypothetical
machine M running at width k and wanted to "widen" it to width k+1 without
changing history, you cannot. The k entered at every `rot` evaluation and
won't commute.

That's the core finding of this project: Malbolge has a *static* width, and
dynamic widening breaks the rule with a clean, measurable counterexample.

Crazy, by contrast, is width-agnostic (`crazy(a, b) = crazy(a, b) mod 3^k`
for k up to wherever the operands are zero-padded). Crazy generic, rotate
sticky — exactly the dispatch you'd want to know about before spending weeks
in a locked decision space.

## What is NOT claimed

- TRUE_OMEGA_SEMANTICS — destroyed.
- UNSHACKLED_PARITY — Unshackled uses `srand(time(NULL))`, so reference
  parity is impossible by construction.
- GROW_ON_DEMAND / width extension triggered mid-run — demonstrated zero
  times.

## Honesty Ledger

The corpus is 6 Classic programs. Everything runs dry-run first before being
asserted ("status=HALTED AND sha256 stdout matches reference"). The k=20
witness uses solely the movd (op 40) and rot (op 39) instructions with
EOF-input termination; no instrumentation outside the VM memory is consulted
beyond `stats.max_addr`.

## Files

```
src/malbolge_free.zig     — the parametric core (THIS IS THE CODE)
src/malbolge_core.py      — python reference I've kept for interop
docs/
  CLASSIC_SEMANTICS.md    — Classic extraction from oracle / Unshackled
  UNSHACKLED_SEMANTICS.md — dynamic-width machinery in Unshackled
  DIFF_CLASSIC_UNSHACKLED.md — what actually changed
  MALBOLGE_K.md             — the parametric view
  EPOCHAL_ANALYSIS.md       — widen-at-address-boundary hypothesis
  HONESTY_LEDGER.md         — "what we actually know, how"
evidence/
  VERDICT.md                — the claim table, raw
  f4_classic_parity.json    — corpus parity per program
  f7_python_check.py        — witness trace
  f8_check.py               — width-consistency sample
tests/
  t_epochal_trigger.zig     — padwidth never fires (confirmed empirically)
```

## License

MIT. Do whatever.
