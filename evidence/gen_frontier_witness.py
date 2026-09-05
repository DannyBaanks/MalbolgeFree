"""Generate a witness program that NEVER halts (at least 60k steps) and contains
zero movd/jmp, so c reaches 3^10 by raw d++ increment alone.

Operations we allow: 5 (out), 23 (in), 62 (crazy), 68 (nop). 
Forbidden in cell decoding: 40 (movd), 4 (jmp), 81 (hlt). Every position gets
a char whose `(ord + c) % 94` satisfies the constraint. Since the cell stores
ord(c) and we control its value, we simply enumerate allowable chars that
produce a non-forbidden op character at that position:
"""

OP_OK = {5, 23, 62, 68}
OP_FORBIDDEN = {4, 40, 81}

TARGET_LEN = 70_000  # > 3^10 = 59049

def op_for_char(char_val, pos):
    return (char_val + pos) % 94

program = []
for pos in range(TARGET_LEN):
    # first printable char that yields a legal op at this position
    for cv in range(33, 127):
        op = op_for_char(cv, pos)
        if op in OP_OK:
            program.append(chr(cv))
            break
    else:
        raise SystemExit(f"no char survives at position {pos}")

src = "".join(program)
open("70000char_witness.out", "w", encoding="latin-1").write(src)
# print the first 100 chars' ops so reviewers can verify
for i in range(80):
    print(f"pos={i:3d} char={src[i]!r} op={op_for_char(ord(src[i]), i)}")
print("...")
print(f"length={len(src)} (capped at {TARGET_LEN})")
