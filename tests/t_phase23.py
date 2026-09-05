"""Phase 2 + F3 tests: core sanity, lazy-vs-eager parity, width=10 == Classic classical loader."""
import sys, io
sys.path.insert(0, r"C:\Development\ISyCo Git\malbolge-free\src")
from malbolge_core import MalbolgeCore, crazy, rotate, _ENC, _CRAZY

# ── lazy-vs-eager fill parity on small width ───────────────────────────────
def eager_fill(width, mem_limit):
    core = MalbolgeCore(width=width, mem_limit=mem_limit)
    core.load("(!#")  # arbitrary short program
    last = core.mem[core.program_len - 1]
    second_last = core.mem[core.program_len - 2]
    fill = []
    for i in range(core.program_len, min(mem_limit or 200, 200)):
        fill.append(crazy(last, second_last, width))
        second_last = last
        last = fill[-1]
    return fill

def lazy_fill(width, mem_limit):
    core = MalbolgeCore(width=width, mem_limit=mem_limit)
    core.load("(!#")
    out = []
    for i in range(core.program_len, min(mem_limit or 200, 200)):
        out.append(core._cell(i))
    return out

for k in (10, 11, 12, 19):
    mlim = None  # unbounded; cap checked range to 200 cells for speed
    e = eager_fill(k, mlim)
    l = lazy_fill(k, mlim)
    assert e == l, (k, e[:10], l[:10])
    print(f"k={k}: lazy == eager  OK  ({len(e)} cells)")

# ── width=10 parity with reference Classic loader ───────────────────────────
ref_crazy = None
src = "(!hi#"  # small
ref__crazy_table = ((1,0,0),(1,0,2),(2,2,1))
def ref_crazy(a, b):
    r = 0; p = 1
    for _ in range(10):
        r += ref__crazy_table[b % 3][a % 3] * p
        a //= 3; b //= 3; p *= 3
    return r

ref_mem = [ord(c) for c in src]
while len(ref_mem) < 59049:
    ref_mem.append(ref_crazy(ref_mem[-1], ref_mem[-2]))

core = MalbolgeCore(width=10, mem_limit=59049)
core.load(src)
our = [core._cell(i) for i in range(59049)]
assert our == ref_mem, "lazy fill at k=10 != reference Classic"
print("k=10: lazy == Classic eager loader (59049 cells bit-for-bit)  OK")

# ── width=19: no wrap ────────────────────────────────────────────────────────
core19 = MalbolgeCore(width=19, mem_limit=None)
core19.load(src)
vals = [core19._cell(i) for i in range(2, 30)]
print("k=19 no-wrap first cells:", vals[:8], "...")
# src = "(!hi#"  program_len = 5
boundary = 3 ** 12   # 531441; semantically identical recomputation carries through
check_cells = [5, 6, 7, 500, boundary - 1]
for cc in check_cells:
    # materialize the full chain up to cc first, then verify the crazy recurrence
    ref_mem = [core19.mem[i] for i in range(core19.program_len)]
    p1 = core19._cell(core19.program_len - 1)
    p2 = core19._cell(core19.program_len - 2)
    while len(ref_mem) <= cc:
        nxt = crazy(p1, p2, 19)
        ref_mem.append(nxt)
        p2, p1 = p1, nxt
    got = core19._cell(cc)
    want = ref_mem[cc]
    assert got == want, (cc, got, want)
print(f"k=19 lazy fill correct at {check_cells}  OK")

# ── op-count test with rot on k=19 using growth policy ───────────────────────
core19g = MalbolgeCore(width=19, mem_limit=None, growth_policy="pad_to_padwidth")
core19g.load(src)
core19g.mem[200] = 1234567  # 7-trit value at addr 200 (legal: within 3^19)
v = [core19g._cell(200)]
w_before = core19g.padwidth
core19g.run(max_steps=100, stdin_data=b"A")  # should not crash
print("k=19 padwidth before:", w_before, "after:", core19g.padwidth)

print("\nPHASE 2 + LAZY/EAGER: PASS")
