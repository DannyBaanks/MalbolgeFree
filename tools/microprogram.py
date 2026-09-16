#!/usr/bin/env python3
"""microprogram — primera superficie de microprogramación propia sobre Malbolge Classic (M4).

Extiende el motor de M3 (`raw_malbolge`): ahí sintetizábamos UN byte; aquí componemos una
secuencia pequeña de comportamiento en UN solo programa Malbolge, todo clean-room
(sin LMAO, sin HeLL, sin gen_init).

Geometría (derivada, no supuesta)
---------------------------------
La celda 0 lleva `(` (valor 40): decodifica a MovD en la posición 0 y su valor es 40, así
que tras la primera instrucción `d = 40`. Durante un tramo **lineal** cada instrucción
avanza c y d en 1, luego el operando de la instrucción en `c` vive en la celda `c + 40`.

**Ese invariante es local al tramo lineal.** Un `Jmp` lo rompe: la VM hace `c = mem[d]`,
cifra la celda de aterrizaje y sigue en `mem[d] + 1`, mientras `d` avanza 1. Tras saltar a
`destino`, el desplazamiento pasa a ser:

    offset = (d_del_jmp + 1) - destino

Medido: saltando a 58 desde el jmp en c=1 (d=41), el offset pasa de +40 a **-16**.
Por eso el emisor lleva `c` y `d` explícitos y nunca asume +40.

Búsqueda consciente de la posición
----------------------------------
En vez de "dado el valor, busca una celda válida" (que obligaba a rellenar con nops y hacía
chocar código y datos), preguntamos "dado dónde está `d` ahora, ¿qué valores son válidos en
carga en esa celda?" y buscamos entre ellos. El tramo lineal queda sin `goto` ninguno:
`HI\\n` pasó de 94 celdas / 42 pasos a 51 / 13.
"""
from __future__ import annotations

import collections
import functools
import importlib.util
from pathlib import Path

GIT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("mal", GIT / "MALBOLGE" / "malbolge.py")
mal = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mal)
crazy = mal.crazy


def rot(v: int) -> int:
    return v // 3 + (v % 3) * 3 ** 9


OPS = {4, 5, 23, 39, 40, 62, 68, 81}
JMP, OUT, IN, ROT, MOVD, OPR, NOP, HLT = 4, 5, 23, 39, 40, 62, 68, 81
D0 = 40                       # desplazamiento inicial que fija la celda 0
EOF_BYTE = mal.EOF_VALUE % 256        # 168 = 0xa8


def op_char(opcode: int, pos: int) -> str:
    r = (opcode - pos) % 94
    return chr(r if r >= 33 else r + 94)


def load_valid(value: int, cell: int) -> bool:
    return (value + cell) % 94 in OPS


@functools.lru_cache(maxsize=None)
def valid_values(cell: int) -> tuple:
    """Bytes imprimibles que el cargador acepta en esa celda."""
    return tuple(v for v in range(33, 127) if load_valid(v, cell))


class MicroProgram:
    """Emite Malbolge Classic crudo para una secuencia pequeña de operaciones."""

    def __init__(self):
        self.cells = {0: chr(D0)}
        self.c = 1
        self.d = D0 + 1
        self.acc = 0                      # valor conocido de A, o None si desconocido (tras IN)

    # ── colocación ────────────────────────────────────────────────────────
    def _free(self, p):
        return p >= 1 and p not in self.cells

    def _place(self, opcode, operand=None):
        if not self._free(self.c):
            raise LayoutError(f"celda de código {self.c} ocupada")
        if operand is not None:
            if not self._free(self.d):
                raise LayoutError(f"celda de datos {self.d} ocupada")
            if not load_valid(operand, self.d):
                raise LayoutError(f"operando {operand} no es válido en carga en {self.d}")
            self.cells[self.d] = chr(operand)
        self.cells[self.c] = op_char(opcode, self.c)
        self.c += 1
        self.d += 1

    # ── operaciones ───────────────────────────────────────────────────────
    def nop(self):
        self._place(NOP)

    def read(self):
        """IN: A := byte de entrada (o EOF_VALUE al agotarse)."""
        self._place(IN)
        self.acc = None                   # depende de la entrada

    def out(self):
        """OUT: emite A % 256 sin tocar A."""
        self._place(OUT)

    def halt(self):
        self._place(HLT)

    def rot_op(self, v):
        self._place(ROT, v)
        self.acc = rot(v)

    def opr_op(self, v):
        self._place(OPR, v)
        self.acc = None if self.acc is None else crazy(self.acc, v)

    # ── síntesis de un byte constante ─────────────────────────────────────
    def _search(self, target, maxlen=12):
        """Ops desde la posición actual que dejan A % 256 == target (búsqueda por posición)."""
        start = (self.c, self.acc)
        q = collections.deque([(self.c, self.acc, [])])
        seen = {start}
        while q:
            c, A, path = q.popleft()
            if path and A is not None and A % 256 == target:
                return path
            if len(path) >= maxlen:
                continue
            cell = c + (self.d - self.c)
            options = [("nop", None, A)]
            for v in valid_values(cell):
                options.append(("rot", v, rot(v)))
                if A is not None:
                    options.append(("opr", v, crazy(A, v)))
            for op, v, nA in options:
                key = (c + 1, nA)
                if key not in seen:
                    seen.add(key)
                    q.append((c + 1, nA, path + [(op, v)]))
        return None

    def emit_const(self, target):
        """Deja A % 256 == target (sin almacenar `target` como operando)."""
        path = self._search(target)
        if path is None:
            raise LayoutError(f"no se encontró receta para el byte {target} en c={self.c}")
        for op, v in path:
            if op == "nop":
                self.nop()
            elif op == "rot":
                self.rot_op(v)
            else:
                self.opr_op(v)

    def out_const(self, target):
        self.emit_const(target)
        self.out()

    # ── salto incondicional ───────────────────────────────────────────────
    def jump_targets(self):
        """Destinos alcanzables desde aquí: el puntero (destino-1) debe caber en la celda d."""
        return tuple(v + 1 for v in valid_values(self.d))

    def jmp(self, target):
        """Jmp real: pone destino-1 en la celda d; la VM salta y sigue en destino."""
        ptr = target - 1
        if not 33 <= ptr <= 126:
            raise LayoutError(f"destino {target}: el puntero {ptr} no es imprimible")
        if not self._free(self.d) or not load_valid(ptr, self.d):
            raise LayoutError(f"destino {target}: puntero no válido en la celda {self.d}")
        if not self._free(target) or target <= self.c:
            raise LayoutError(f"destino {target} ocupado o no es hacia adelante")
        self.cells[self.d] = chr(ptr)
        self.cells[self.c] = op_char(JMP, self.c)
        d_after = self.d + 1
        self.c = target                       # la VM aterriza en destino-1 y sigue en destino
        self.d = d_after
        return target

    # ── resultado ─────────────────────────────────────────────────────────
    def source(self):
        hi = max(self.cells)
        return "".join(chr(D0) if p == 0 else self.cells.get(p, op_char(NOP, p))
                       for p in range(hi + 1))


class LayoutError(RuntimeError):
    pass


# ── API de programa ───────────────────────────────────────────────────────────

def emit_program(ops):
    """Compila una lista de operaciones a UN programa Malbolge Classic.

    Operaciones:
        ("out", byte)   sintetiza el byte y lo emite
        ("in",)         lee un byte de la entrada a A
        ("out_acc",)    emite A (lo que se leyó o calculó)
        ("opr", v)      transforma A := crazy(A, v)  — v imprimible válido en la celda
        ("rot", v)      A := rot(v)
        ("jmp", label)  salto incondicional hacia adelante
        ("label", name) destino de salto
        ("halt",)       fin
    """
    labels = [name for kind, *rest in
              [(o[0], *o[1:]) for o in ops] if kind == "label" for name in rest]
    if len(set(labels)) != len(labels):
        raise LayoutError("etiquetas duplicadas")
    p = MicroProgram()
    pending = {}            # label -> posición elegida
    i = -1
    while i + 1 < len(ops):
        i += 1
        op = ops[i]
        kind = op[0]
        if kind == "out":
            p.out_const(op[1])
        elif kind == "in":
            p.read()
        elif kind == "out_acc":
            p.out()
        elif kind == "opr":
            p.opr_op(op[1])
        elif kind == "rot":
            p.rot_op(op[1])
        elif kind == "halt":
            p.halt()
        elif kind == "jmp":
            name = op[1]
            rest = ops[i + 1:]
            try:
                stop = next(j for j, o in enumerate(rest) if o[0] == "label" and o[1] == name)
            except StopIteration:
                raise LayoutError(f"etiqueta {name!r} no encontrada tras el salto")
            unreachable = rest[:stop]
            target = _pick_target(p, len(unreachable))
            saved_c = p.c
            p.jmp(target)
            _fill_unreachable(p, saved_c + 1, target, unreachable)
            pending[name] = target
            i += stop              # saltar las ops inalcanzables: ya son trampa, no código real
        elif kind == "label":
            if op[1] not in pending:
                raise LayoutError(f"etiqueta {op[1]!r} sin salto previo (v0 sólo soporta saltos hacia adelante)")
        else:
            raise LayoutError(f"operación desconocida {kind!r}")
    return p.source()


def _pick_target(p, unreachable_len):
    """Primer destino válido que deje sitio al bloque inalcanzable (política determinista)."""
    # Tras el salto, los datos siguen en d_jmp+1 mientras el código arranca en el destino:
    # `d` queda (destino - d_jmp - 1) celdas por detrás, así que ese hueco es el presupuesto
    # de instrucciones del tramo posterior. Elegimos el destino MÁS LEJANO (determinista).
    floor = max(p.c + unreachable_len, max(p.cells))
    for target in sorted(p.jump_targets(), reverse=True):
        if target > floor and p._free(target):
            return target
    raise LayoutError(f"ningún destino de salto válido desde c={p.c} (d={p.d})")


def _fill_unreachable(p, start, target, unreachable):
    """Escribe el bloque inalcanzable (trampa) entre el jmp y el destino."""
    c = start
    for op in unreachable:
        while c < target and not p._free(c):
            c += 1                            # no pisar celdas de datos ya usadas
        if c >= target:
            break
        if op[0] in ("out", "out_acc"):
            p.cells[c] = op_char(OUT, c)      # si se ejecutara emitiría A: es la trampa
        elif op[0] == "halt":
            p.cells[c] = op_char(HLT, c)
        else:
            p.cells[c] = op_char(OUT, c)
        c += 1
