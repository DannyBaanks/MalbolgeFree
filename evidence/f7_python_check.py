"""F7 crossing workbench — pure Python equivalent, exact same semantics as the
Zig core. movd chain = (' & % $ over positions 0..3.

Positions:
  c=0: '(' = 40  -> op=(40+0)%94=40 movd
  c=1: 39  = 39 -> op=(39+1)%94=40 movd
  c=2: 38  = 38 -> op=(38+2)%94=40 movd
  c=3: 37  = 37 -> op=(37+3)%94=40 movd
Each movd reads mem[d] and moves d. Confirms max_addr > 3^19 legally.
"""
CRAZY = ((1, 0, 0), (1, 0, 2), (2, 2, 1))

def crazy(a, b, w):
    r, p = 0, 1
    for _ in range(w):
        r += CRAZY[b % 3][a % 3] * p
        a //= 3; b //= 3; p *= 3
    return r

prog = "('&%"
WIDTH = 20
mem = {}

for i, ch in enumerate(prog):
    mem[i] = ord(ch)

def lazy_cell(i):
    if i in mem:
        return mem[i]
    # record lazily
    j = i
    chain = [j]
    while j >= len(prog) and j not in mem:
        chain.append(j)
        j -= 1
    chain = chain[1:]
    while chain:
        t = chain.pop()
        mem[t] = crazy(mem[t - 1], mem[t - 2], WIDTH)
    return mem[i]

a, c, d = 0, 0, 0
max_addr = 0
best_move = None
for step in range(8):
    cell = lazy_cell(c)
    op = (cell + c) % 94
    print(f"step={step} c={c} d={d} op={op}")
    if op == 40:
        nv = lazy_cell(d)
        print(f"  movd: d = mem[{d}] = {nv}  ({'CROSS' if nv > 3**19 else '...'})")
        d = nv
    max_addr = max(max_addr, d)
    c += 1; d += 1
print(f"\nmax d (address) touched = {max_addr}")
print(f"3^19 = {3**19}")
print(f"=> CROSS = {max_addr > 3**19}")
