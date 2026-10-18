# F14 — `REGION_1_2_DISPATCH_DIVERGENCE_V1`: pre-registered expectations

Status: **PRE-REGISTERED BEFORE EXECUTION** (2026-10-18). Written, then run, then
sealed.

## Why this gate exists

In gate F13 (`docs/F13_UNSHACKLED_K19_PREGISTRATION.md`, HONESTY_LEDGER entry 39),
divergence V1 was identified by reading the reference source:

> "V1: `(c + mem[c]) % 94` in our cores vs `+ 117` in region 1, `+ 140` in region 2
> in `bolge19.zig:371-376, 388-389`. Out of scope for F13 (F13 declared scope
> $c < 3^{18}$, Region 0 only). V1 left identified by reading and untested."

`ROADMAP.md` (lines 420–423) explicitly set the real next step:
"(2) un gate para región 1/2, que es donde vive V1".

This gate implements that measurement. It provides both statistical proof over
the dispatch formula and an execution witness in runtime binaries where $c$
actually jumps into Region 1 ($c \ge 3^{18}$) and exercises the divergence.

## The two machines

| | ours | reference |
|---|---|---|
| artifact | `src/malbolge_core.py`, `src/malbolge_free.zig` | `../MalbolgeLispSlop/src/bolge19.zig` (pinned sha256 `47758a3f…`), binary `build/bolge19` |
| profile | `initUnshackledK19` ($w=19, \text{mem\_limit}=3^{19}, \text{fixed}$) | `../MalbolgeLispSlop/profiles/fixed19.json` (pinned sha256 `6cc0afa1…`) |
| region dispatch | $(c + \text{mem}[c]) \bmod 94$ everywhere | $(c + \text{mem}[c] + \text{off}[\text{region}]) \bmod 94$, with $\text{region} = c / 3^{18}$ |
| regional offsets | $0$ unconditionally for all $c \in [0, 3^{19})$ | $\text{offs} = [0, 117, 140]$ |

## Regional geometry

* `END` = $3^{19} = 1\,162\,261\,467$
* `THIRD` = $3^{18} = 387\,420\,489$
* **Region 0:** $0 \le c < 387\,420\,489$. Both machines use offset 0.
* **Region 1:** $387\,420\,489 \le c < 774\,840\,978$. Our offset = 0; reference offset = 117 ($117 \equiv 23 \pmod{94}$).
* **Region 2:** $774\,840\,978 \le c < 1\,162\,261\,467$. Our offset = 0; reference offset = 140 ($140 \equiv 46 \pmod{94}$).

## Execution cases

Malbolge programs load as printable bytes, and initial crazy tails alternate
between Region 1 and Region 0 inside the page window. Jump targets are
constructed by loading registers and jumping into tail cells that reside in
Region 1:

1. **Control Case C1 (`ubO`, decimal `[117, 98, 79]`):**
   Executes in Region 0. Both machines agree on halt status and halt position.

2. **Case R1 (`(aO`, decimal `[40, 97, 79]`):**
   * Cell 0: opcode 40 (`movd`), sets $d = 40$.
   * Cell 1: opcode 4 (`jmp`), jumps to $\text{mem}[41] = 581\,130\,699$ (Region 1).
   * Step 2 arrival: $c = 581\,130\,700$ (Region 1).
   * Execution diverges on halt: `bolge19`'s $+117$ offset hits opcode 81 (`HALT`)
     at step 11 ($c = 581\,130\,727$). Our cores (no offset) evaluate step 11 as
     opcode 58 (NOP) and continue to step 60 ($c = 581\,130\,775$).

3. **Case R2 (`'&B`, decimal `[39, 38, 66]`):**
   * Cell 0: opcode 39 (`rot`).
   * Cell 1: opcode 39 (`rot`).
   * Cell 2: opcode 68 (`nop`).
   * Cell 3: opcode 4 (`jmp`), jumps to $581\,130\,749$ (Region 1).
   * Step 4 arrival: $c = 581\,130\,750$ (Region 1).
   * At step 4, our core decodes opcode 68 (`nop`). The reference decodes
     $(68 + 117) \bmod 94 = 91$ (`invalid`), exhibiting exactly the $+23$ delta.

## Pre-registered expectations (17)

* `D1` `pow3(19) == json.end == 1 162 261 467`.
* `D2` `pow3(18) == json.end // 3 == 387 420 489`.
* `D3` `json.dispatch_offsets[0] == 0`.
* `D4` `json.dispatch_offsets[1] == 117` and `117 % 94 == 23`.
* `D5` `json.dispatch_offsets[2] == 140` and `140 % 94 == 46`.

* `P1_R0_FORMULA_EQUALITY`: across 50 000 seeded pairs $(c, \text{mem})$ in Region 0 ($c < 3^{18}$), $(c + \text{mem} + 0) \bmod 94 == (c + \text{mem}) \bmod 94$, exactly **0** mismatches.
* `P2_R1_FORMULA_DIVERGENCE`: across 50 000 seeded pairs $(c, \text{mem})$ in Region 1 ($3^{18} \le c < 2 \cdot 3^{18}$), the reference index equals $(\text{ours} + 23) \bmod 94$ for **100%** of samples, and differs from ours on **100%** of samples.
* `P3_R2_FORMULA_DIVERGENCE`: across 50 000 seeded pairs $(c, \text{mem})$ in Region 2 ($2 \cdot 3^{18} \le c < 3^{19}$), the reference index equals $(\text{ours} + 46) \bmod 94$ for **100%** of samples, and differs from ours on **100%** of samples.

* `R0_CONTROL_REGION_0`: Case C1 halts on all three machines at $(c=2, d=2)$ with identical stdout `0xda`.
* `R1_STATUS_HALT`: Case R1 reaches `HALT` / `HALTED` on `bolge19`, `malbolge_core.py`, and `malbolge_free.zig`.
* `R1_REGION_ARRIVAL`: Case R1 arrives in Region 1 at step 2 ($c = 581\,130\,700$, $c / 3^{18} == 1$) across all machines.
* `R1_HALT_DIVERGENCE`: Case R1 halt steps differ as predicted: `bolge19` halts at step 11 ($c = 581\,130\,727$) due to the $+117$ offset, while our cores do not halt at step 11 and halt at step 60 ($c = 581\,130\,775$).
* `R1_CROSS_CORE_AGREEMENT`: `malbolge_core.py` and `malbolge_free.zig` agree identically on Case R1: steps=60, final_c=581130775, final_d=581130767.
* `R2_STATUS_MAX_STEPS`: Case R2 reaches MAX_STEPS at budget 5 on all three machines.
* `R2_REGION_ARRIVAL`: Case R2 executes in Region 1 at step 4 ($c = 581\,130\,750$, $c / 3^{18} == 1$) across all machines.
* `R2_OPCODE_DELTA`: Case R2 decodes at step 4 to opcode 68 (`nop`) in our core and opcode index 91 (`invalid`) in the reference, delta $91 - 68 = 23 \equiv 117 \pmod{94}$.
* `R2_CROSS_CORE_AGREEMENT`: `malbolge_core.py` and `malbolge_free.zig` agree identically on Case R2 at budget 5: status=MAX_STEPS, final_c=581130751, final_d=5.

## Exit contract

`0` all 17 expectations hold · `3` the reference source, profile or binary is
absent (`NOT_DEMONSTRATED`, an explicit skip, never a green) · `4` the reference
bytes drifted from the hashes recorded in the run report (integrity failure).
A falsified expectation exits `1` with the expectation ID printed.

## What F14 does not claim

Not Turing completeness. Not full emulation of Lutter's original `Unshackled.c`
(which remains nondeterministic). Not equivalence in encryption cascades (V3).
The claim is strictly: **the regional dispatch formula divergence V1 (+117 in Region 1,
+140 in Region 2) is mathematically verified and demonstrated under execution in
both runtime cores against the localized deterministic third-party reference.**
