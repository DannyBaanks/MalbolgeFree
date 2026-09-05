"""Brute-force: for chains [movd]*n + rot setups, find one hitting d > 3^19."""
CRAZY = ((1, 0, 0), (1, 0, 2), (2, 2, 1))

def crazy(a, b, w):
    r, p = 0, 1
    for _ in range(w):
        r += CRAZY[b % 3][a % 3] * p
        a //= 3
        b //= 3
        p *= 3
    return r

def fill(prefix, w, depth):
    mem = [ord(c) for c in prefix]
    for i in range(len(prefix), depth):
        mem.append(crazy(mem[i - 1], mem[i - 2], w))
    return mem

def op_char(op, pos):
    for ch in range(33, 127):
        if (ch + pos) % 94 == op:
            return chr(ch)

B19 = 3 ** 19
DEPTH = 2_000_000

for n in range(2, 8):
    prefix = "".join(op_char(40, i) for i in range(n))
    mem = fill(prefix, 20, DEPTH)
    d = 0
    for _ in range(n):
        d = mem[d]
    print(f"n_movd={n} prefix={prefix!r} d_end={d} >3^19: {d > B19}")
    if d > B19:
        # record witness
        witness = prefix
        break
