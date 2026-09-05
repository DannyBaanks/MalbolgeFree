"""Instrument the witness: does it ever fire rot (39)?"""
CRAZY = ((1, 0, 0), (1, 0, 2), (2, 2, 1))

def crazy(a, b, w):
    r, p = 0, 1
    for _ in range(w):
        r += CRAZY[b % 3][a % 3] * p
        a //= 3; b //= 3; p *= 3
    return r

PROG = "('&%$"
WIDTH = 20
MAX_STEPS = 200

mem = list(ord(c) for c in PROG)
present = set(range(len(PROG)))

def lazy(i):
    global mem
    if i >= len(mem):
        # extend chain
        for j in range(len(mem), i + 1):
            mem.append(crazy(mem[j - 1], mem[j - 2], WIDTH))
    return mem[i]

a, c, d = 0, 0, 0
ops = {4:0,5:0,23:0,39:0,40:0,62:0,68:0,81:0}
other = 0
max_d = 0
for step in range(MAX_STEPS):
    if c >= len(mem) and c >= len(PROG):
        lazy(c)  # materialize so we can read
    cell = lazy(c)
    op = (cell + c) % 94
    if op in ops:
        ops[op] += 1
    else:
        other += 1
        if op == 39:
            v = lazy(d)
            mem[d] = (v // 3) + (v % 3) * (3 ** (WIDTH - 1))
            a = mem[d]
        elif op == 40:
            d = lazy(d)
            if d > max_d:
                max_d = d
    c += 1

print(f"ops used in first {MAX_STEPS} steps: {ops}  other={other}")
print(f"crazy={ops[62]}  rot={ops[39]}  movd={ops[40]}  jmp={ops[4]}  out={ops[5]}")
print(f"max d (ever moved to): {max_d}")
print(f"crosses 3^19 ({3**19})? {max_d > 3**19}")
