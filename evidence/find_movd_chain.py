"""Synthesize a legal Malbolge program with the movd chain and a final 'use d' instruction.

Program layout (all instructions at fixed c-positions, chosen to decode to op):
  c=0..4: movd  — d walks chain of lazy cells
  c=5:     any op that forces a READ at the current d (rot is cleanest: it reads mem[d])

With width=20 lazy fill, the chain of movd's picks out values >3^19; the rot
then reads mem[d] where d>3^19. THAT's the crossing.
"""

CRAZY = ((1, 0, 0), (1, 0, 2), (2, 2, 1))


def crazy(a, b, w):
    r = 0
    p = 1
    for _ in range(w):
        r += CRAZY[b % 3][a % 3] * p
        a //= 3
        b //= 3
        p *= 3
    return r


def op_char(op: int, pos: int) -> str:
    for ch in range(33, 127):
        if (ch + pos) % 94 == op:
            return chr(ch)
    raise ValueError("none")


B19 = 3 ** 19

# Try several movd-chain lengths; find one where d overshoots 3^19.
for n_movd in range(2, 8):
    prefix = "".join(op_char(40, i) for i in range(n_movd))
    # simulate the chain
    mem0 = [ord(c) for c in prefix]
    # lazy-fill to a depth covering all reachable addresses
    # but only up to ~1e6, to let the chain iterate fast
    target_depth = 2_000_000
    mem = list(mem0)
    for i in range(len(prefix), target_depth + 2):
        mem.append(crazy(mem[i - 1], mem[i - 2], 20))

    # simulate movd chain
    d = 0
    for _ in range(n_movd):
        d = mem[d]
    if d > B19:
        print(f"n_movd={n_movd}: prefix={prefix!r}  d overshoots 3^19: d={d}  ({d:,})")
        break
else:
    print("no overshoot with movd chains of length 2..7")
