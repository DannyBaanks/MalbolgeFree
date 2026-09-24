"""Verify READ stage tape layout: opcodes contiguous in cells 2..n+1, n in cell1."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen import build_compiler


def trace(src, inp, size=64, max_steps=200_000):
    tape = [0] * size
    ptr = 0
    ip = 0
    st = []
    table = {}
    for i, ch in enumerate(src):
        if ch == "[":
            st.append(i)
        elif ch == "]":
            j = st.pop()
            table[i] = j
            table[j] = i
    ipos = 0
    out = []
    steps = 0
    while ip < len(src) and steps < max_steps:
        c = src[ip]
        if c == ">":
            ptr = (ptr + 1) % size
        elif c == "<":
            ptr = (ptr - 1) % size
        elif c == "+":
            tape[ptr] = (tape[ptr] + 1) & 255
        elif c == "-":
            tape[ptr] = (tape[ptr] - 1) & 255
        elif c == ".":
            out.append(tape[ptr])
        elif c == ",":
            tape[ptr] = ord(inp[ipos]) if ipos < len(inp) else 0
            ipos += 1
        elif c == "[":
            if tape[ptr] == 0:
                ip = table[ip]
        elif c == "]":
            if tape[ptr] != 0:
                ip = table[ip]
        ip += 1
        steps += 1
    return tape, ptr, out, steps


p = build_compiler()
for src in ["+++[-].", "++[>++<-]>.", ",[.,]"]:
    tape, ptr, out, steps = trace(p, src)
    print(f"src={src!r}")
    print(f"  n(cell1)={tape[1]}  full_tape={tape[:18]}  ptr={ptr}")
    print(f"  steps={steps}")