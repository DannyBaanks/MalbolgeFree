# Pre-registration — Gate F15 (Encryption Cascade Divergence V3)

Pre-registered 2026-10-18 before execution of gate F15.

## Topic and scope

Gate F15 measures divergence **V3** (encryption alphabet, indexing offset, domain
guard, and cascade re-execution) between `MalbolgeFree` and the deterministic
third-party fixed-3^19 reference `MalbolgeLispSlop/src/bolge19.zig`.

F13 measured parity on the 8 dispatch opcodes, EOF, wrap, and 19-trit `crazy` over
Region 0 ($c < 3^{18}$) for programs of $\le 4$ cells.
F14 measured divergence V1 (regional dispatch offsets $+117$ in Region 1 and $+140$
in Region 2) for $c \ge 3^{18}$.

F15 measures the self-encryption behavior and its cascade across linear execution
and domain boundaries:
1. Canonical domain $[33, 126]$: both engines implement identical permutations and
   identical multi-step encryption orbits (cycle lengths `[68, 9, 6, 5, 4, 2]`).
2. Domain guard divergence: `MalbolgeFree` guards $33 \le \text{cell} \le 126$ (the
   canonical specification; values outside are untouched). `bolge19` guards
   $\text{cell} < 141$ (`XLAT_CONCAT.len`), encrypting sub-33 values ($0 \le v \le 32$)
   via `"SOMEBODY MAKE ME FEEL ALIVE[hj9>,"` and high bytes ($127 \le v \le 140$)
   via `"AND SHATTER ME"`.
3. Alignment mechanism: the 33-byte prefix of `XLAT_CONCAT` ($27 + 6 = 33$) exactly
   shifts index $v$ to match canonical `TRANSLATED[v - 33]` on $[33, 126]$.
4. Multi-step cascades: 3 programs with 2, 4, and 6 consecutive encrypted cells
   agree across all three machines, while a sub-33 cell mutation program (`b"'bO"`)
   empirically demonstrates the domain guard divergence on real execution.

## The peer and pinned files

The external reference is `MalbolgeLispSlop/src/bolge19.zig` (SHA-256
`47758a3f667f4089f6029d86130b94f14f082d4c113a212b8ff571d84113e8a3`) under
`profiles/fixed19.json` (SHA-256
`6cc0afa10b050a36673e131b2efc69fa29e9589136f52b5f27a7dabe23b6ac1f`).
Compiled binary: `../MalbolgeLispSlop/build/bolge19`.

The reference is **not vendored**. When the sibling checkout is missing, the gate
exits 3 (`SKIP (NOT_DEMONSTRATED, missing external input)`).

## V3 Structural Analysis

```
Domain               MalbolgeFree (Canonical)       bolge19 (fast20 profile)       Divergence
---------------------------------------------------------------------------------------------
v in [0, 32]         Untouched (identity v -> v)    XLAT_CONCAT[v] in [32, 112]    DIVERGES (33 values)
v in [33, 126]       TRANSLATED[v - 33]             XLAT_CONCAT[v]                 AGREES (94 values)
v in [127, 140]      Untouched (identity v -> v)    XLAT_CONCAT[v] in [32, 85]     DIVERGES (14 values)
v in [141, 3^19-1]   Untouched (identity v -> v)    Untouched (identity v -> v)    AGREES
```

## Case set

| Case | Source (bytes) | Stdin | Steps (ref / ours) | Expected stdout | Description |
|---|---|---|---|---|---|
| `C1` | `b"ubO"` (3B) | empty | 2 / 3 | `0xda` | Baseline control: in -> out -> halt (2 cells encrypted in [33..126]) |
| `C5` | `b"ubs`M"` (5B) | `b"AB"` | 4 / 5 | `b"AB"` | 5-cell linear cascade: 4 cells encrypted in [33..126] |
| `C7` | `b"ubs`q^K"` (7B) | `b"XYZ"` | 6 / 7 | `b"XYZ"` | 7-cell linear cascade: 6 cells encrypted in [33..126] |
| `C_SUB33` | `b"'bO"` (3B) | empty | 2 / 3 | `0x0d` (`\r`) | Sub-33 mutation witness: `rot(39)=13` skips encryption on ours |

## Pre-registered expectations (21)

### Section 1: Table & Geometry Proofs (D1 – D5)
- `D1_CANONICAL_TABLE`: `TRANSLATED` has length 94, matching `canonical_malbolge_py` and `malbolge_free.zig`.
- `D2_REFERENCE_TABLE`: `XLAT_CONCAT` has length 141, matching `bolge19.zig` (27 prefix + 100 mid + 14 suffix).
- `D3_CANONICAL_SLICE_IDENTITY`: `XLAT_CONCAT[33:127] == TRANSLATED` (94/94 byte-exact match).
- `D4_DISAGREEMENT_SET`: Disagreement set over $[0, 255]$ is exactly $[0, 32] \cup [127, 140]$ (cardinality 47). Over $[141, 255]$, both are identity.
- `D5_FINITE_CONVERGENCE`: All 141 values in $[0, 140]$ reach $[33, 126]$ under reference iteration in $\le 2$ steps.

### Section 2: Property & Orbit Verification (P1 – P4)
- `P1_CYCLE_ISOMORPHISM`: Canonical permutation has 6 disjoint cycles of lengths `[68, 9, 6, 5, 4, 2]`. Iteration depths $k \in \{1, 2, 5, 10, 50, 100\}$ agree 100% on all 94 values (0 mismatches).
- `P2_SUB33_DIVERGENCE`: 33/33 values in $[0, 32]$ diverge: ours = $v$, reference = $\text{XLAT\_CONCAT}[v] \ne v$ (100% divergence).
- `P3_HIGHBYTE_DIVERGENCE`: 14/14 values in $[127, 140]$ diverge: ours = $v$, reference = $\text{XLAT\_CONCAT}[v] \ne v$ (100% divergence).
- `P4_RANDOM_GRID_CANONICAL`: 100 000 random samples in $[33, 126]$ (`Random(20261018)`) match between `encrypt_ours` and `encrypt_ref` with 0 mismatches.

### Section 3: Execution Cascades & Domain Divergence (R1 – R4)
- `R1_C1_STATUS`: `C1` halts on all three machines with identical final $c=2, d=2$, stdout `0xda`.
- `R1_C1_ENCRYPTED_COUNT`: `C1` records 2 encrypted cells on our cores.
- `R1_C1_ENCRYPTED_VALUES`: `C1` cells 0..1 encrypted to `[111, 84]` across all three machines.

- `R2_C5_STATUS`: `C5` halts on all three machines with identical final $c=4, d=4$, stdout `b"AB"`.
- `R2_C5_ENCRYPTED_COUNT`: `C5` records 4 encrypted cells on our cores.
- `R2_C5_ENCRYPTED_VALUES`: `C5` cells 0..3 encrypted to `[111, 84, 82, 60]` across all three machines.

- `R3_C7_STATUS`: `C7` halts on all three machines with identical final $c=6, d=6$, stdout `b"XYZ"`.
- `R3_C7_ENCRYPTED_COUNT`: `C7` records 6 encrypted cells on our cores.
- `R3_C7_ENCRYPTED_VALUES`: `C7` cells 0..5 encrypted to `[111, 84, 82, 60, 108, 57]` across all three machines.

- `R4_SUB33_STATUS`: `C_SUB33` halts on all three machines with identical final $c=2, d=2$, stdout `0x0d` (13).
- `R4_SUB33_SKIP_ENCRYPT`: In `MalbolgeFree`, cell 0 held 13 after `rot(39, 19)`, which is outside $[33, 126]$, so `MalbolgeFree` skips encryption on cell 0 (`encrypted_cells == 1`, only cell 1 is encrypted).
- `R4_SUB33_CROSS_CORE`: Python core and Zig core agree 100% on `C_SUB33` status, steps (3), stdout, and `encrypted == 1`.

## Exit Contract
- `0`: PASS (all 21 expectations match).
- `3`: SKIP (missing external sibling checkout).
- `4`: DRIFT (pinned reference file hash mismatch).
- `1`: FAIL (falsified expectation).
