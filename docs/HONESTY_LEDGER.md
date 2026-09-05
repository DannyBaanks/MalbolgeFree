# HONESTY LEDGER

What we got, how we got it, and where we know we cheated.

| # | Claim | Evidence | Cheat check |
|---|---|---|---|
| 1 | Core is parametric without k-special-cases | `src/malbolge_free.zig` has no `if (k == 10) ...` | Search: `if.*k ?= 10` or `19` — clean |
| 2 | Classic parity on corpus | `evidence/f4_classic_parity.json` (6 programs, sha256 match) | stdout sampled, all 6 PASS |
| 3 | Lazy fill == eager fill | `t_phase23.py` 4 widths, 197 cells each | Python-side check pre-Jason update; fresh 59049-cell verifications under k=10..20 can't be brute-forced. I claim parity up to where I measured |
| 4 | Period-6 lazy fill is correct | `evidence/crazy_periodicity.py`, verified w=10,19,20,26 | NOT universally proven; the shortcut is a *consequence of observed* fixed-point stability |
| 5 | LEGAL_3^19_CROSSING | `f7_witness.zig` — `('&%` runs, max_addr=1743392210 | movd-set d takes *any* value; reading mem[d=1743392210] is lazy-legal (not an explicit write). --γ**
| 6 | Rotation inconsistency at k vs k+1 | `f8_check.py` — rotate ~33% consistent, crazy 100% | rotate isn't extension-consistent; growth under `pad_to_padwidth` is *safe only if width never fires during seeds-lazy-fill path* |

## Legitimate ambiguity on C3/C7

The lazy fill is seeded by the last two "program" values, not by rounds. "lazy
cells = crazy(mem[i-1], mem[i-2])" — standard. No weasel. But the periodicity
proof stage: the chain after program_len+2 exhibits period 6 for the *specific
patterns in our corpus*. Could be a contraction — but the practical outcome is
verified on the corpus. We accept "period 6 evidenced, not proven for all
seeds" as an outstanding bound, not a bug.

## Where we did NOT cheat

- No `--patch memory` tail. The core never writes `memory[d] = value_ge_3^19`,
  only `movd` reads.
- Rot/growth are invocations of the operand widths, not direct assignments from
  host constants.
- The `('&%` witness runs fully and reports the crossing without instrumentation
  white RNA.
