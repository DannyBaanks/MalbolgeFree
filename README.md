# MALBOLGE_FREE_V0

Private research project. **NO PUBLICAR.**

Aliases: Malbolge Free, Malbolge ^ω^, "Gatito Feliz".

## Premise

Is the fixed trit-width `k` (10 in Classic, arbitrary-but-static in
Unshackled) *essential* to Malbolge semantics?

If not, then a parameterized `Malbolge(k)` core should reproduce both at
their respective widths, and legal execution at larger `k` (or without a
declared `k`) is a genuine generalization — **Free** — not merely a bigger
cage.

## Status

Phase 0 started. See `docs/` and `evidence/`.

**No claims yet.** Every claim lives in `evidence/VERDICT.md` and is one of
`DEMONSTRATED | NOT_DEMONSTRATED | DESTROYED | INCONCLUSIVE | NO_NEW_CLAIM`.

## Anti-Cheat List (from project brief)

FAIL if: MAX_ADDR hardcoded in the Free core; `k==10`/`k==19` semantic
special-cases; host-driven state manipulation used to cross `3^19`; dynamic
width that silently changes `crazy`/`rotate`; words like "unbounded" used
when we mean "very large".
