"""F8 reduced: sample grid of manageable size."""
CRAZY = ((1, 0, 0), (1, 0, 2), (2, 2, 1))

def crazy(a, b, w):
    r, p = 0, 1
    for _ in range(w):
        r += CRAZY[b % 3][a % 3] * p
        a //= 3; b //= 3; p *= 3
    return r

def rotate(v, w):
    return v // 3 + (v % 3) * 3 ** (w - 1)

# Use small-ish widths where brute force is fine
for w in (3, 4, 6, 8):
    lim = 3 ** w
    total = same = 0
    for a in range(0, lim, max(1, lim // 97)):
        for b in range(0, lim, max(1, lim // 97)):
            total += 1
            same += crazy(a, b, w) == crazy(a, b, w + 1) % lim
    rot_total = rot_same = 0
    for v in range(0, lim, max(1, lim // 1313)):
        rot_total += 1
        rot_same += rotate(v, w) == rotate(v, w + 1) % lim
    print(f"w={w:2d}  crazy same={same}/{total} ({same/total*100:.1f}%)   "
          f"rotate same={rot_same}/{rot_total} ({rot_same/rot_total*100:.1f}%)")
    assert same < total and rot_same < rot_total, "extension consistency FAILED"
print("=> projection_map(step_(k+1)(state_k)) != step_k(state_k) — INCONSISTENT for both ops")
