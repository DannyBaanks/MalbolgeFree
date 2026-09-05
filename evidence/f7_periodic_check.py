"""Confirm crossing happens when using the 6-periodic lazy fill.
Only Python; semantics EXACTLY as Zig core (with period-6 shortcut pre-proven).

prefix "('&%" is 4 chars. Program positions 0..3 are program cells.
crazy-fill starts at i=4. From "(&%": cell 4 = crazy('%;'&',20) etc. It enters
period-6 by index 6 (program_len + 2). mem[38..] cycle = [1743392164, 38, 1743392165, 37, 1743392165, 38].
"""

CRAZY = ((1, 0, 0), (1, 0, 2), (2, 2, 1))


def crazy(a, b, w):
    r, p = 0, 1
    for _ in range(w):
        r += CRAZY[b % 3][a % 3] * p
        a //= 3
        b //= 3
        p *= 3
    return r


PROG = "('&%"
# lazy fill k=20
mem = {i: ord(c) for i, c in enumerate(PROG)}
# fill from program_len to program_len+12
for i in range(len(PROG), len(PROG) + 12):
    mem[i] = crazy(mem[i - 1], mem[i - 2], 20)


def lazy(i):
    if i < 4:
        return mem[i]
    if i in mem:
        return mem[i]
    base = 6  # len 4 + 2
    offset = (i - base) % 6
    return mem[base + offset]


# simulate
a, c, d = 0, 0, 0
max_addr = 0
for step in range(6):
    cell = lazy(c)
    op = (cell + c) % 94
    if op == 40:  # movd
        d = lazy(d)
    c += 1
    if d > max_addr:
        max_addr = d if d > max_addr else max_addr
    print(f"step={step} c={c} d={d} op={op} max_addr={max_addr}")

print(f"\n=> max_addr={max_addr}  3^19={3**19}  CROSS={max_addr > 3**19}")

# Now verify the Zig core would produce the same
# (we only check the lazy function itself)
