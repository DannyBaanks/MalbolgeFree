"""Bounded search for Classic Malbolge state-dependent CHASE gadgets.

This is deliberately an experiment, not part of the VM contract. It asks a
specific question: can the same short source prefix leave two executions,
starting with different accumulator values, at the same CHASE instruction
with different target cells?
"""

from itertools import product

MEM = 59049
OPS = (39, 40, 62, 68)  # ROT, MOVD, CRAZY, NOP
CRZ = ((1, 0, 0), (1, 0, 2), (2, 2, 1))
ENC = "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"


def source_for(op: int, pos: int) -> int:
    value = 33 + ((op - pos - 33) % 94)
    if not 33 <= value <= 126:
        raise ValueError((op, pos, value))
    return value


def crazy(a: int, b: int) -> int:
    result = 0
    power = 1
    for _ in range(10):
        result += CRZ[b % 3][a % 3] * power
        a //= 3
        b //= 3
        power *= 3
    return result


def run(prefix: tuple[int, ...], initial_a: int):
    source = [source_for(op, pos) for pos, op in enumerate(prefix)]
    source.append(source_for(4, len(prefix)))
    mem = source + [0] * (MEM - len(source))
    for i in range(len(source), MEM):
        mem[i] = crazy(mem[i - 1], mem[i - 2])

    a, c, d = initial_a, 0, 0
    for pos in range(len(prefix)):
        op = (mem[c] + c) % 94
        if op == 4:
            return None
        if op == 39:
            value = mem[d]
            mem[d] = value // 3 + (value % 3) * 19683
            a = mem[d]
        elif op == 40:
            d = mem[d]
        elif op == 62:
            mem[d] = crazy(a, mem[d])
            a = mem[d]
        if 33 <= mem[c] <= 126:
            mem[c] = ord(ENC[mem[c] - 33])
        c = (c + 1) % MEM
        d = (d + 1) % MEM

    op = (mem[c] + c) % 94
    if op != 4:
        return None
    return c, d, mem[d], a, tuple(mem[: len(source)])


def main() -> None:
    best = None
    for depth in range(0, 11):
        checked = 0
        for prefix in product(OPS, repeat=depth):
            checked += 1
            zero = run(prefix, 0)
            nonzero = run(prefix, 1)
            if zero is None or nonzero is None:
                continue
            if zero[2] != nonzero[2]:
                score = max(zero[2], nonzero[2])
                if best is None or (depth, score) < (best[0], best[1]):
                    best = (depth, score, prefix, zero, nonzero)
                if zero[2] < 1000 and nonzero[2] < 1000:
                    print("FOUND_SMALL", "depth", depth, "prefix", prefix)
                    print("zero", zero[:4])
                    print("nonzero", nonzero[:4])
                    return
        print("NOT_FOUND depth", depth, "checked", checked)
    if best is None:
        print("NOT_FOUND all depths")
    else:
        _, score, prefix, zero, nonzero = best
        print("FOUND_BEST", "score", score, "prefix", prefix)
        print("zero", zero[:4])
        print("nonzero", nonzero[:4])


if __name__ == "__main__":
    main()
