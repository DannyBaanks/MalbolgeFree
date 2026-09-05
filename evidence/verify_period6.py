"""Verify crazy-chain periodicity EXACTLY for the F7 witness program ('&%)
under multiple widths. Proof criterion: the materialized chain for i in
[program_len .. program_len + 60] is 6-periodic from index program_len + 2.
"""
CRAZY = ((1, 0, 0), (1, 0, 2), (2, 2, 1))

def crazy(a, b, w):
    r, p = 0, 1
    for _ in range(w):
        r += CRAZY[b % 3][a % 3] * p
        a //= 3; b //= 3; p *= 3
    return r

prefix = "('&%"
for w in (10, 11, 12, 19, 20, 23, 26):
    mem = [ord(c) for c in prefix]
    while len(mem) < len(prefix) + 60:
        mem.append(crazy(mem[-1], mem[-2], w))
    base = len(prefix) + 2
    period = None
    for cand in range(1, 7):
        if all(mem[base + j] == mem[base + j + cand] for j in range(0, min(40, len(mem) - base - cand))):
            period = cand
            break
    vals = mem[base:base + 6]
    print(f"w={w:2d} base={base} period={period} cycle={vals}")
