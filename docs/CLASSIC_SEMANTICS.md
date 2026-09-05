# CLASSIC semantics — extracted from vendored `malbolge.py` (Iizawa 2005 / malbolge.c lineage)

Source audited: `MALDOOM/vendor/malbolge/malbolge.py` (PROVENANCE: public-language
description, Iizawa 2005 Appendix C, transcription of 1998 `malbolge.c`).

## Machine state

- Registers: `a` (accumulator), `c` (code ptr), `d` (data ptr). Start 0,0,0.
- Memory: exactly `3^10 = 59049` cells.
- All values are k=10 trit values (non-negative ints < 3^10).

## Loader

1. Strip whitespace from source.
2. Each remaining char must have `33 <= ord(c) <= 126`; else `INVALID` (load error, before execution).
   (vendor impl rejects the entire program)
3. `mem[i] = ord(char)` for program chars; **then every remaining cell**
   `mem[i] = crazy(mem[i-1], mem[i-2])` for `i >= len(program)` — the crazy-fill
   tail. This is what makes "unwritten memory" deterministic under Classic.

## Instruction decode

`op = (mem[c] + c) % 94`; jump table:

| op | name | semantics |
|---|---|---|
| 4  | jmp  | `c = mem[d]` (via `c_target`) |
| 5  | out  | emit `a % 256` |
| 23 | in   | `a = ord(ch)` or `a = -1` on EOF |
| 39 | rot  | `mem[d] = v//3 + (v%3) * 3^9; a = mem[d]` (10-trit rotate) |
| 40 | movd | `d = mem[d]` |
| 62 | crazy| `mem[d] = crazy(a, mem[d]); a = mem[d]` |
| 68 | nop  | nothing |
| 81 | hlt  | halt (status HALTED) |
| other |   | nop (pass) |

## Width-dependent pieces

| element | k-dependence |
|---|---|
| memory size | `3^k` |
| encode/dec | none — 94-ASCII alphabet only |
| crazy | tritwise over exactly `k=10` positions (`for _ in range(10)`) |
| rotate | `// 3 + (mod 3) * 3^(k-1)` — uses `3^9` because `k=10` |
| `mem[c] % 94` | none |
| `% 256` output | none |

## Halt / error

- `81` → HALTED
- `MAX_STEPS` bound is the host driver's, not semantic.
- Invalid source char → INVALID, program never runs.

## Self-encryption

After executing instruction at `c`: if `33 <= mem[c] <= 126`, replace with
`_ENC[mem[c]]` (fixed table, width-independent).
