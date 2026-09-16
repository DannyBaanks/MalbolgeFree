"""M7 compiler.bf generator + BFIR1 reference oracle (Python mirror of the Zig
bf_to_ir.zig + bf_ir_image.zig semantics), for differential testing.

The compiler we emit is a pure Brainfuck program (operator-only, no comments)
that reads BF source on stdin and writes its BFIR1 image on stdout.

Design (cell-verified against MEOW-ENGINE/interpreters/brainfuck.py):
  - cell 0 : LEFT SENTINEL (always 0)
  - cell 1 : n (instruction count)
  - cells 2..(n+1) : opcode array (contiguous)
  - cell n+2 : right sentinel (0)
  - cells n+3.. : scratch (P=print, depth, temps)
"""
import sys

sys.path.insert(0, r"C:\Development\ISyCo Git\MEOW-ENGINE\interpreters")
from brainfuck import run as _run

# ----------------------------------------------------------------------------
# Reference oracle (mirror of the Zig compiler + encoder)
# ----------------------------------------------------------------------------
OPCODES = {
    ">": 1, "<": 2, "+": 3, "-": 4, ".": 5, ",": 6, "[": 7, "]": 8,
}
OP_BY_CODE = {v: k for k, v in OPCODES.items()}


def ref_compile(src):
    """-> list of (opcode, target|None, source_pos)."""
    code = []
    opens = []
    for source_pos, ch in enumerate(src):
        if ch not in OPCODES:
            continue
        oc = OPCODES[ch]
        idx = len(code)
        if oc == 7:  # jump_if_zero = '['
            opens.append(idx)
            code.append((oc, None, source_pos))
        elif oc == 8:  # jump_if_nonzero = ']'
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


# ----------------------------------------------------------------------------
# BF idiom: classify a byte at the current cell into opcode 1..8.
# Pre:  pointer at A (byte 43..93). Scratch A+1, A+2 are 0.
# Post: pointer at A (opcode 1..8, or unchanged if not an operator).
#       A+1, A+2 are 0.
# ----------------------------------------------------------------------------
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


def _emit_header():
    # Emits "BFIR1" = 66,70,73,82,49 via relative arithmetic from P (sentinel+1).
    return (
        ">"
        + "+" * 66 + "."          # 'B' 66
        + "++++" + "."            # 'F' 70
        + "+++" + "."             # 'I' 73
        + "+" * 9 + "."           # 'R' 82
        + "-" * 33 + "."          # '1' 49
        + "[-]<"                   # clear P, back to sentinel (home)
    )


def _emit_count():
    # Emits count = (cell1 - 1) as 4 LE bytes, ends pointer at cell2.
    return (
        "<"                        # last opcode (or cell1 if n==0)
        + "[<]"                    # -> cell0
        + ">"                      # -> cell1 (n+1)
        + "-"                      # n
        + "."                      # emit n (low byte)
        + "<"                      # cell0
        + "..."                    # 3 zero bytes
        + ">>"                     # -> cell2
        + "<[-]>"                  # zero cell1 (i=0 for record loop)
    )


def _emit_records():
    # Bracket-free: 12-byte record = op + 7 zeros + i + 3 zeros. Mobile i counter.
    return (
        "["                        # while opcode != 0
        + "."                      # byte0 = opcode
        + "[-]"                    # zero current cell
        + "......."                # bytes 1..7 = 0
        + "<"                      # -> counter cell (i)
        + "."                      # byte8 = i
        + "<"                      # -> cell0 / zeroed prev  (zero)
        + "..."                    # bytes 9..11 = 0
        + ">"                      # -> counter
        + "[->+<]"                 # move i to current (zeroed) cell
        + ">"                      # -> new counter cell
        + "+"                      # i+1
        + ">"                      # -> next opcode
        + "]"
    )


def build_compiler():
    """Assemble the full compiler.bf (operator-only, bracket-free emission)."""
    p = []
    # READ: read + classify + count. cell1 = counter (init 1, so never 0),
    # opcodes contiguous in cells 2..n+1, sentinel at cell n+2.
    p.append(">+")            # cell1 = 1 (counter init)
    p.append(">")             # cell2
    p.append(",")             # cell2 <- first byte
    p.append("[")             # while byte != 0
    p.append(CLASSIFY)        # char -> opcode at current cell
    p.append("[<]")           # -> cell0 (left sentinel, permanent 0)
    p.append(">")             # -> cell1 (counter, nonzero)
    p.append("+")             # counter++
    p.append("[>]")           # -> next free slot (first 0 right)
    p.append(",")             # read next byte
    p.append("]")
    # EMIT: header + count + records. Pointer is at sentinel (cell n+2) after read.
    p.append(_emit_header())
    p.append(_emit_count())
    p.append(_emit_records())
    return "".join(p)


def write_compiler(path):
    with open(path, "w", newline="") as f:
        f.write(build_compiler())


def run_bf(prog, inp, max_steps=30_000_000):
    out, steps, status = _run(prog, max_steps, inp)
    return out.encode("latin-1"), steps, status


if __name__ == "__main__":
    cases = ["", "++", "+++.-.", ">+++<+>.>.", ",+.", ">>+<++.", "++++++[>++++++<-]>."]
    prog = build_compiler()
    print("compiler.bf len =", len(prog))
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