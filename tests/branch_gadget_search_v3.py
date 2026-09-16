"""Búsqueda dirigida: prefijo cuyo CHASE salte a TargetA si a=0 y a TargetB si a!=0.

Modelo Classic 3^10 con memoria perezosa (igual que v2). Uso:
  py tests/branch_gadget_search_v3.py <target_zero> <target_nonzero> [max_depth]
Ejemplo para `[` de `[+]`: zero->183 (HALT), nonzero->91 (cuerpo).
"""
from itertools import product
import sys

MEM = 59049
OPS = (39, 40, 62, 68)
CRZ = ((1, 0, 0), (1, 0, 2), (2, 2, 1))
ENC = "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"


def source_for(op, pos):
    return 33 + ((op - pos - 33) % 94)


def crazy(a, b):
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
        self.tail = list(source)
        self.overlay = {}

    def get(self, addr):
        if addr in self.overlay:
            return self.overlay[addr]
        while addr >= len(self.tail):
            a = self.get(len(self.tail) - 1)
            b = self.get(len(self.tail) - 2)
            self.tail.append(crazy(a, b))
        return self.tail[addr]

    def put(self, addr, val):
        self.overlay[addr] = val
        if addr < len(self.tail):
            self.tail[addr] = val
        else:
            while len(self.tail) <= addr:
                a = self.get(len(self.tail) - 1)
                b = self.get(len(self.tail) - 2)
                self.tail.append(crazy(a, b))
            self.tail[addr] = val


def run(prefix, initial_a):
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
        vc = m.get(c)
        if 33 <= vc <= 126:
            m.put(c, ord(ENC[vc - 33]))
        c = (c + 1) % MEM
        d = (d + 1) % MEM
    if (m.get(c) + c) % 94 != 4:
        return None
    return c, d, m.get(d), a


def main():
    if len(sys.argv) < 3:
        print("uso: branch_gadget_search_v3.py <target_zero> <target_nonzero> [max_depth]")
        return
    tz = int(sys.argv[1])
    tnz = int(sys.argv[2])
    max_depth = int(sys.argv[3]) if len(sys.argv) > 3 else 7
    print(f"buscando zero->{tz} nonzero->{tnz} hasta profundidad {max_depth}", flush=True)
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
            if z[0] != nz[0]:
                continue
            if z[2] == tz and nz[2] == tnz:
                print(f"FOUND depth={depth} prefix={prefix} c={z[0]} d_z={z[1]} d_nz={nz[1]}", flush=True)
                return
        print(f"depth {depth} checked={checked} sin hit", flush=True)
    print("NOT_FOUND objetivos exactos en este espacio", flush=True)


if __name__ == "__main__":
    main()
