"""Find a width=20 lazy-fill cell whose value > 3^19, for a given 5-char movd prefix.

Self-contained Python equivalent of the Zig core (width=20, lazy fill).
Then output the FIRST such address and value for the f7 cross test.
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


def lazy_fill(prefix: str, width: int, up_to: int):
    mem = [ord(c) for c in prefix]
    for i in range(len(prefix), up_to + 1):
        mem.append(crazy(mem[i - 1], mem[i - 2], width))
    return mem


prefix = "('&%$"
B = 3 ** 19

for width in (10, 20):
    mem = lazy_fill(prefix, width, 500)
    hits = [(i, v) for i, v in enumerate(mem[len(prefix):], start=len(prefix)) if v > B]
    print(f"width={width}: {len(hits)} cells >3^19 in first {500 - len(prefix)} fill cells")
    for i, v in hits[:5]:
        print(f"  addr={i:6d} value={v} ({v:>20,.0f})  >3^19 ✓")
