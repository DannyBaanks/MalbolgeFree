"""F8 dramatization: measure the inconsistency between width-k and width-(k+1).

Question: does treating a value at width k and then padding it to width k+1
before the op give the same low trits as operating at width k?

For crazy: no — crazy(a, 0-pad-b, k+1) writes into position k+1 the value
CRZ[0][b % 3] which is 1 when b%3 == 0, changing low trits were untouched.
For rotate: no — rotate(v, k) = v//3 + (v%3)*3^(k-1), rotate(v, k+1) =
v//3 + (v%3)*3^k; these differ unless v%3 == 0.

We quantify directly: fraction of (a, b) pairs on which crazy at width w and
width w+1 agree in their low w trits.
"""
CRAZY = ((1, 0, 0), (1, 0, 2), (2, 2, 1))

def crazy(a, b, w):
    r, p = 0, 1
    for _ in range(w):
        r += CRAZY[b % 3][a % 3] * p
        a //= 3; b //= 3; p *= 3
    return r

def rotate(v, w):
    return v // 3 + (v % 3) * 3 ** (w - 1)

results = []
for w in (10, 11, 19):
    limit_w = 3 ** w
    # crazy inconsistency over a grid
    total = 0
    same = 0
    for a in range(0, limit_w, 97):
        for b in range(0, limit_w, 97):
            total += 1
            same += crazy(a, b, w) == crazy(a, b, w + 1) % limit_w
    # rotate inconsistency
    rot_total = rot_same = 0
    for v in range(0, limit_w, 13):
        rot_total += 1
        rot_same += rotate(v, w) == rotate(v, w + 1) % limit_w
    results.append((w, total, same, rot_total, rot_same))

print("crazy(a,b,w) == crazy(a,b,w+1) % 3^w  consistency rate:")
for w, t, s, rt, rs in results:
    print(f"  w={w:2d}: {s}/{t} = {s/t*100:.2f}%")
print()
print("rotate(v,w) == rotate(v,w+1) % 3^w  consistency rate:")
for w, t, s, rt, rs in results:
    print(f"  w={w:2d}: {rs}/{rt} = {rs/rt*100:.2f}%")
