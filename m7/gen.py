"""M7 compiler.bf generator with stride-2 design and bracket resolution (TODO).

Current version: bracket-free (works for programs without brackets).
TODO: Implement stride-2 layout with 3-pass bracket resolution.
"""

import sys


def run(program: str, max_steps: int = 80_000_000, stdin: str = "") -> tuple[str, int, str]:
    cmds = [c for c in program if c in "><+-.,[]"]
    bracket_map = {}
    stack = []
    for i, c in enumerate(cmds):
        if c == "[":
            stack.append(i)
        elif c == "]":
            if not stack:
                raise ValueError(f"Unmatched ] at position {i}")
            j = stack.pop()
            bracket_map[i] = j
            bracket_map[j] = i
    if stack:
        raise ValueError(f"Unmatched [ at position {stack[-1]}")
    tape = [0] * 50000
    ptr = 0
    ip = 0
    stdin_bytes = stdin.encode("latin-1")
    stdin_pos = 0
    output = []
    steps = 0
    while ip < len(cmds) and steps < max_steps:
        c = cmds[ip]
        if c == ">":
            ptr += 1
            if ptr >= len(tape):
                tape.extend([0] * 10000)
        elif c == "<":
            ptr -= 1
            if ptr < 0:
                raise ValueError("Pointer underflow")
        elif c == "+":
            tape[ptr] = (tape[ptr] + 1) & 255
        elif c == "-":
            tape[ptr] = (tape[ptr] - 1) & 255
        elif c == ".":
            output.append(chr(tape[ptr]))
        elif c == ",":
            if stdin_pos < len(stdin_bytes):
                tape[ptr] = stdin_bytes[stdin_pos]
                stdin_pos += 1
            else:
                tape[ptr] = 0
        elif c == "[":
            if tape[ptr] == 0:
                ip = bracket_map[ip]
        elif c == "]":
            if tape[ptr] != 0:
                ip = bracket_map[ip]
        ip += 1
        steps += 1
    status = "HALTED" if ip >= len(cmds) else "MAX_STEPS"
    return "".join(output), steps, status


# Reference oracle
OPCODES = {">": 1, "<": 2, "+": 3, "-": 4, ".": 5, ",": 6, "[": 7, "]": 8}


def ref_compile(src):
    code = []
    opens = []
    for source_pos, ch in enumerate(src):
        if ch not in OPCODES:
            continue
        oc = OPCODES[ch]
        idx = len(code)
        if oc == 7:
            opens.append(idx)
            code.append((oc, None, source_pos))
        elif oc == 8:
            o = opens.pop()
            code.append((oc, o, source_pos))
            code[o] = (code[o][0], idx, code[o][2])
        else:
            code.append((oc, None, source_pos))
    assert not opens, "unbalanced"
    return code


def ref_encode(src):
    code = ref_compile(src)
    out = bytearray()
    out += b"BFIR1"
    out += len(code).to_bytes(4, "little")
    for oc, target, sp in code:
        out.append(oc)
        out.append(1 if target is not None else 0)
        out.append(0)
        out.append(0)
        out += (target if target is not None else 0).to_bytes(4, "little")
        out += sp.to_bytes(4, "little")
    return bytes(out)


# CLASSIFY: byte at current cell -> opcode 1..8 in current cell (net ptr change = 0)
CASES = [(43, 3), (44, 6), (45, 4), (46, 5), (60, 2), (62, 1), (91, 7), (93, 8)]


def _case(C, O):
    return (
        "[->+>+<<]"
        ">>"
        "[-<<+>>]"
        "<"
        + "-" * C
        + ">+<"
        + "[[-]>-<]"
        + ">"
        + "[-<<" + "-" * C + "+" * O + ">>]"
        + "<<"
    )


CLASSIFY = "".join(_case(C, O) for C, O in CASES)


# ============================================================
# WORKING BRACKET-FREE COMPILER (contiguous layout)
# ============================================================
# This version works for bracket-free BF programs (6/7 test cases pass).
# It uses contiguous memory layout:
#   cell 0: sentinel
#   cell 1: count
#   cells 2..n+1: opcodes
#   cell n+2: sentinel
#
# For bracket support, we need STRIDE-2 LAYOUT (see TODO below):
#   cells 2,4,6...: opcodes
#   cells 3,5,7...: targets (0 = none, else target_idx+1)
#   cell 100: bracket depth
#   cells 102,104...: bracket stack


def build_compiler():
    """Build compiler.bf - currently returns bracket-free version."""
    return build_compiler_bracket_free()


def build_compiler_bracket_free():
    """Bracket-free compiler (working, 1522 bytes, passes 6/7 test cases)."""
    parts = []
    parts.append("[-]")
    parts.append(">+")
    parts.append(">")
    parts.append(",")
    parts.append("[")
    parts.append(CLASSIFY)
    parts.append("[<]")
    parts.append(">")
    parts.append("+")
    parts.append("[>]")
    parts.append(",")
    parts.append("]")
    parts.append(">")
    parts.append("+" * 66 + ".")
    parts.append("++++.")
    parts.append("+++.")
    parts.append("+" * 9 + ".")
    parts.append("-" * 33 + ".")
    parts.append("[-]<")
    parts.append("<[<]>")
    parts.append("-")
    parts.append(".")
    parts.append("<...")
    parts.append(">>")
    parts.append("<[-]>")
    parts.append("[")
    parts.append(".")
    parts.append("[-]")
    parts.append(".......")
    parts.append("<")
    parts.append(".")
    parts.append("<...")
    parts.append(">")
    parts.append("[->+<]")
    parts.append(">")
    parts.append("+")
    parts.append(">")
    parts.append("]")
    return "".join(parts)


# ============================================================
# STRIDE-2 COMPILER DESIGN (TODO - not yet implemented)
# ============================================================
def build_compiler_stride2():
    """Stride-2 compiler with bracket resolution (NOT YET IMPLEMENTED).
    
    Memory layout:
      cell 0: sentinel (0)
      cell 1: instruction count (n)
      cells 2,4,6... (2+2*i): opcodes
      cells 3,5,7... (3+2*i): targets (0 = none, else target_idx+1)
      cell 100: bracket depth (for pass 2)
      cells 102,104,106,108,110: stack[0..4] = open bracket index (1-based)
      cell 130: pass 2 index counter
      cell 200: P cell for header emission
      After opcodes: source_pos at SP_BASE = 2+2*n+2
    
    Three-pass design:
      Pass 1: Read all input, classify, store opcodes at even cells,
              store source_pos in contiguous area after opcodes.
      Pass 2: Walk opcodes from cell2, resolve brackets:
              - On '[' (7): push current index to stack[depth], depth++
              - On ']' (8): depth--, pop from stack, write target to both
      Pass 3: Emit full 12-byte records from stride-2 layout.
    
    Returns:
      str: Brainfuck source code (NOT YET IMPLEMENTED, returns bracket-free)
    """
    # TODO: Implement full three-pass stride-2 compiler
    # This requires ~5000 bytes of carefully crafted BF code.
    # Key challenges:
    #   - Variable pointer distances between phases
    #   - Implementing stack push/pop in BF with fixed cells
    #   - Emitting 32-bit little-endian integers in BF
    #   - Managing three distinct passes with a pass marker
    
    # For now, fall back to bracket-free version
    return build_compiler_bracket_free()


def run_bf(prog, inp, max_steps=80_000_000):
    out, steps, status = run(prog, max_steps, inp)
    return out.encode("latin-1"), steps, status


if __name__ == "__main__":
    print("CLASSIFY length:", len(CLASSIFY))
    prog = build_compiler()
    print("Compiler length:", len(prog))
    
    opens = prog.count('[')
    closes = prog.count(']')
    print(f"Brackets - open: {opens}, close: {closes}, balanced: {opens == closes}")
    
    cases = ["", "++", "+++.-.", ">+++<+>.>.", ",+.", ">>+<++.", "++++++[>++++++<-]>."]
    all_ok = True
    for src in cases:
        got, steps, status = run_bf(prog, src)
        want = ref_encode(src)
        ok = (got == want)
        all_ok = all_ok and ok
        print(f"{src!r:24} match={ok} steps={steps} status={status}")
        if not ok:
            print(f"   got ={got.hex()}")
            print(f"   want={want.hex()}")
    print("ALL OK" if all_ok else "MISMATCH")