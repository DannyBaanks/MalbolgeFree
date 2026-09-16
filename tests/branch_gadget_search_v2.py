"""Búsqueda acotada y perezosa de gadgets CHASE sensibles a `a`.

Pregunta: ¿puede el mismo prefijo fuente dejar dos ejecuciones
(a=0 frente a a=19683=rotate(1)) en el mismo CHASE con distinto
mem[d] (distinto destino)?

Memoria Classic 3^10, semántica densa. Evaluación perezosa para no
rellenar 59049 celdas por prefijo.
"""
from itertools import product
import sys

MEM = 59049
OPS = (39, 40, 62, 68)  # ROT, MOVD, CRAZY, NOP
CRZ = ((1, 0, 0), (1, 0, 2), (2, 2, 1))
ENC = "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"


def source_for(op: int, pos: int) -> int:
    return 33 + ((op - pos - 33) % 94)


def crazy(a: int, b: int) -> int:
    r = 0
    p = 1
    for _ in range(10):
        r += CRZ[b % 3][a % 3] * p
        a //= 3
        b //= 3
        p *= 3
    return r


class LazyMem:
    def __init__(self, source):
        self.base = list(source)
        self.tail = list(source)  # se extiende bajo demanda
        self.overlay = {}

    def get(self, addr: int) -> int:
        if addr in self.overlay:
            return self.overlay[addr]
        while addr >= len(self.tail):
            # extiende de uno en uno; en la práctica sólo tocamos pocos
            a = self.get(len(self.tail) - 1)
            b = self.get(len(self.tail) - 2)
            self.tail.append(crazy(a, b))
        return self.tail[addr]

    def put(self, addr: int, val: int):
        self.overlay[addr] = val
        if addr < len(self.tail):
            self.tail[addr] = val
        else:
            # extiende hasta addr y escribe
            while len(self.tail) <= addr:
                a = self.get(len(self.tail) - 1)
                b = self.get(len(self.tail) - 2)
                self.tail.append(crazy(a, b))
            self.tail[addr] = val


def run(prefix, initial_a):
    n = len(prefix) + 1
    if n > 200:
        return None
    source = [source_for(op, pos) for pos, op in enumerate(prefix)]
    source.append(source_for(4, len(prefix)))
    m = LazyMem(source)
    a, c, d = initial_a, 0, 0
    for _ in range(len(prefix)):
        if c >= MEM or d >= MEM:
            return None
        op = (m.get(c) + c) % 94
        if op == 4:
            return None
        if op == 39:
            v = m.get(d)
            nv = v // 3 + (v % 3) * 19683
            m.put(d, nv)
            a = nv
        elif op == 40:
            d = m.get(d)
            if d >= MEM:
                return None
        elif op == 62:
            nv = crazy(a, m.get(d))
            m.put(d, nv)
            a = nv
        elif op == 81:
            return None
        # encrypt
        vc = m.get(c)
        if 33 <= vc <= 126:
            m.put(c, ord(ENC[vc - 33]))
        c = (c + 1) % MEM
        d = (d + 1) % MEM
    op = (m.get(c) + c) % 94
    if op != 4:
        return None
    tgt = m.get(d)
    return c, d, tgt, a


def main():
    max_depth = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    best = None
    small_found = 0
    for depth in range(0, max_depth + 1):
        checked = 0
        for prefix in product(OPS, repeat=depth):
            checked += 1
            z = run(prefix, 0)
            if z is None:
                continue
            nz = run(prefix, 19683)
            if nz is None:
                continue
            if z[2] == nz[2]:
                continue
            # debe coincidir la posición del CHASE para ser el mismo gadget
            if z[0] != nz[0]:
                continue
            score = max(z[2], nz[2])
            if best is None or (depth, score) < (best[0], best[1]):
                best = (depth, score, prefix, z, nz)
                print(f"BEST depth={depth} score={score} prefix={prefix} zero_tgt={z[2]} nz_tgt={nz[2]} d_z={z[1]} d_nz={nz[1]}", flush=True)
            if z[2] < 2000 and nz[2] < 2000:
                print(f"FOUND_SMALL depth={depth} prefix={prefix} zero={z} nonzero={nz}", flush=True)
                small_found += 1
                if small_found >= 5:
                    return
        print(f"depth {depth} checked={checked} best_so_far={best[1] if best else None}", flush=True)
    if best:
        print(f"FINAL_BEST depth={best[0]} score={best[1]} prefix={best[2]} zero={best[3]} nonzero={best[4]}")
    else:
        print("NOT_FOUND")


if __name__ == "__main__":
    main()
