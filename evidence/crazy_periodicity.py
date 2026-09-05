"""Verify: crazy-fill sequence x_i = crazy(x_{i-1}, x_{i-2}, w) is eventually
periodic, period dividing 6, for programmatic seeds. If true, lazy memory in
Free can be O(1)-computed for untouched cells (like Unshackled initial_values)."""
CRAZY = ((1, 0, 0), (1, 0, 2), (2, 2, 1))

def crazy(a, b, w):
    r, p = 0, 1
    for _ in range(w):
        r += CRAZY[b % 3][a % 3] * p
        a //= 3
        b //= 3
        p *= 3
    return r

def check(aw, bw, w):
    seq = [aw, bw]
    for _ in range(60):
        seq.append(crazy(seq[-1], seq[-2], w))
    # find smallest period in tail
    tail = seq[-30:]
    for per in (2, 3, 6):
        if all(tail[i] == tail[i + per] for i in range(len(tail) - per)):
            return per
    return None

results = {}
for w in (10, 19, 20, 26):
    pers = set()
    for a in (0, 1, 36, 99, 3 ** w - 1):
        for b in (0, 1, 42, 3 ** w - 1, 12345):
            p = check(a, b, w)
            pers.add(p)
    results[w] = pers
    print(f"width={w}: periods seen = {sorted(x for x in pers if x)}")

# Also: how soon does periodicity start?
for w in (10, 20):
    for a, b in [(40, 39), (0, 1), (3**w - 1, 42)]:
        seq = [a, b]
        for _ in range(200):
            seq.append(crazy(seq[-1], seq[-2], w))
        tail = seq[-12:]
        # find tail period 6 matches
        on = None
        for start in range(0, 100):
            if all(seq[start + i] == seq[start + i + 6] for i in range(0, 12)):
                on = start
                break
        print(f"w={w} seed=({a},{b}): tail 6-periodic from index {on}")
