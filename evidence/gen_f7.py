"""Generate a legal Malbolge program whose execution under k=20 (lazy fill,
unbounded mem) touches an address > 3^19.

Strategy — no hack, no host writes:
  op-at-position rule: op(c) = (ord(cell[c]) + c) % 94
  Steps:
    step1: c=0, d=0. cell[0]='(' (40). op = (40+0)%94 = 40 = movd
           -> d = mem[0] = 40
    step2: c=1, d=41. cell[1]="'" (39). op = (39+1)%94 = 40 = movd
           -> d = mem[41]  (lazy-filled under k=20 -> any 20-trit value,
              up to 3**20 - 1 > 3**19)
    step3: c=2, d=mem[41]+1. cell[2]='&' (38). op = (38+2)%94 = 40 = movd
           -> touches address mem[41]+1 which can be > 3**19, then
              d = mem[mem[41]+1]
  The rest of the source is nops (any char producing 'else' opcode) so the
  run keeps stepping until a halt lands or max_steps is hit.

The whole point: every cell touched is produced by the honest lazy crazy-fill
in the same width as the run; the host never injects any value.
"""
import pathlib

def op_char(c_target: int, pos: int) -> str:
    # find a printable char c: (ord(c) + pos) % 94 == op
    for ch in range(33, 127):
        if (ch + pos) % 94 == c_target:
            return chr(ch)
    raise ValueError("no char")

# prefix: movd, movd, movd
prefix = [op_char(40, 0), op_char(40, 1), op_char(40, 2)]
program = "".join(prefix)

# Then a sea of nops: use '68' opcode occasionally but simple: any char
# whose mapped op is in the "else" class. ch with (ch+pos)%94 in {66,..,80}\{81}
# We'll just take 'z' repeated — check it:
op_z2 = (ord('z') + 3) % 94
program += 'z' * 200

out = pathlib.Path(r"C:\Development\ISyCo Git\malbolge-free\corpus\free")
out.mkdir(parents=True, exist_ok=True)
(out / "cross_3pow19.mal").write_text(program, encoding="ascii")
print("program:", repr(program[:20]), "len:", len(program))
print("ops:", [(i, (ord(c) + i) % 94, 'movd' if (ord(c) + i) % 94 == 40 else 'other') for i, c in enumerate(program[:6])])
