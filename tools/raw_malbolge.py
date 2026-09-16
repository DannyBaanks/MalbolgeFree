#!/usr/bin/env python3
"""raw_malbolge — clean-room Malbolge Classic emitter (lmao-lite own layout engine, M2/M3).

Emits raw Classic Malbolge source directly: NO LMAO, NO HeLL, no gen_init.  Our own layout,
verified on the two Classic engines of the toolkit.

Layout
------
Cell 0 holds char 40 ('('), which decodes to MovD at position 0 and whose *value* is 40, so
the first instruction sets d = 40.  From then on d = c + 40 while execution is linear, so an
op at code position p operates on data cell 40 + p and the accumulator A carries across ops.

Two synthesis models are emitted:

* inline chain  — `Rot v` (A := rot(v)) then `Opr v` (A := crazy(A, v)) over fresh operand
  cells.  Reaches 201/256 output bytes.
* accumulator chain — keeps a persistent cell ACC and can revisit it, which needs a d rewind:
  a MovD whose pointer cell (placed wherever d happens to be, after NOP padding) holds
  ACC - 1.  MovD may jump d backwards, which is what lets the same cell be rotated again.
  This closes the remaining 55 bytes (154..208).

Every stored operand and pointer is a printable byte that is load-valid at its own cell
((value + cell) % 94 must be a valid opcode); the target byte is never stored.
"""
from __future__ import annotations

import argparse
import collections
import functools
import importlib.util
import sys
from pathlib import Path

GIT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("mal", GIT / "MALBOLGE" / "malbolge.py")
mal = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mal)
crazy = mal.crazy
rot = lambda v: v // 3 + (v % 3) * 3 ** 9

OPS = {4, 5, 23, 39, 40, 62, 68, 81}
PRINTABLE = range(33, 127)
D_OFFSET = 40
ROT, OUT, MOVD, OPR, NOP, HLT = 39, 5, 40, 62, 68, 81


def op_char(opcode: int, pos: int) -> str:
    r = (opcode - pos) % 94
    return chr(r if r >= 33 else r + 94)


def load_valid(value: int, pos: int) -> bool:
    return (value + pos) % 94 in OPS


# ── model A: inline chain (A := rot(v) / A := crazy(A, v)) ────────────────────

@functools.lru_cache(maxsize=1)
def _inline_bfs():
    dist, prev = {}, {}
    q = collections.deque()
    for v in PRINTABLE:
        a = rot(v)
        if a not in dist:
            dist[a] = 1
            prev[a] = (None, ("rotload", v))
            q.append(a)
    while q:
        a = q.popleft()
        if dist[a] >= 10:
            continue
        for v in PRINTABLE:
            b = crazy(a, v)
            if b not in dist:
                dist[b] = dist[a] + 1
                prev[b] = (a, ("combine", v))
                q.append(b)
    return dist, prev


# ── model B: persistent accumulator cell (W := crazy(rot(v), W) / W := rot(W)) ─

@functools.lru_cache(maxsize=1)
def _acc_bfs():
    dist, prev = {}, {}
    q = collections.deque()
    for w0 in PRINTABLE:
        if w0 not in dist:
            dist[w0] = 0
            prev[w0] = (None, ("start", w0))
            q.append(w0)
    while q:
        x = q.popleft()
        if dist[x] >= 5:
            continue
        moves = [(("rotW", 0), rot(x))] + [(("combine", v), crazy(rot(v), x)) for v in PRINTABLE]
        for mv, nw in moves:
            if nw not in dist:
                dist[nw] = dist[x] + 1
                prev[nw] = (x, mv)
                q.append(nw)
    return dist, prev


def _path(prev, value):
    moves, a = [], value
    while prev[a][0] is not None:
        pa, mv = prev[a]
        moves.append(mv)
        a = pa
    moves.append(prev[a][1])
    return list(reversed(moves))


class _Layout:
    """Places code on the c path and data on the d path, tracking both registers."""

    def __init__(self):
        self.cells = {0: chr(D_OFFSET)}      # MovD at 0 whose value sets d = 40
        self.c = 1
        self.d = D_OFFSET + 1
        self.acc = None

    def free(self, p):
        return p >= 1 and p not in self.cells

    def goto(self, X, maxpad=94):
        """Make d == X when the next instruction runs (MovD may jump backwards)."""
        if self.d == X:
            return True
        ptr = X - 1
        if not 33 <= ptr <= 126:
            return False
        for k in range(maxpad):
            if (load_valid(ptr, self.d + k) and self.free(self.d + k)
                    and all(self.free(self.c + j) for j in range(k + 1))):
                for _ in range(k):                       # NOP padding advances c and d together
                    self.cells[self.c] = op_char(NOP, self.c)
                    self.c += 1
                    self.d += 1
                self.cells[self.d] = chr(ptr)
                self.cells[self.c] = op_char(MOVD, self.c)
                self.c += 1
                self.d = X
                return True
        return False

    def op(self, opcode, X, operand=None):
        if not self.goto(X):
            return False
        if operand is not None:
            if not self.free(X) or not load_valid(operand, X):
                return False
            self.cells[X] = chr(operand)
        if not self.free(self.c):
            return False
        self.cells[self.c] = op_char(opcode, self.c)
        self.c += 1
        self.d = X + 1
        return True

    def finish(self):
        for opcode in (OUT, HLT):
            if not self.free(self.c):
                return None
            self.cells[self.c] = op_char(opcode, self.c)
            self.c += 1
        hi = max(self.cells)
        return "".join(chr(D_OFFSET) if p == 0 else self.cells.get(p, op_char(NOP, p))
                       for p in range(hi + 1))


def _emit_inline(moves):
    L = _Layout()
    for op, v in moves:
        X = next((x for x in range(L.d, 200) if L.free(x) and load_valid(v, x)), None)
        if X is None or not L.op(ROT if op == "rotload" else OPR, X, v):
            return None
    return L.finish()


def _emit_acc(moves, acc):
    L = _Layout()
    w0 = moves[0][1]
    if not load_valid(w0, acc):
        return None
    for op, v in moves[1:]:
        if op == "combine":
            X = next((x for x in range(L.d, 200) if L.free(x) and load_valid(v, x) and x != acc), None)
            if X is None or not L.op(ROT, X, v):
                return None
            if L.acc is None:
                if not L.free(acc) or not L.op(OPR, acc, w0):
                    return None
                L.acc = acc
            elif not L.op(OPR, L.acc):
                return None
        else:                                            # rotW
            if L.acc is None:
                if not L.free(acc):
                    return None
                L.cells[acc] = chr(w0)
                L.acc = acc
            if not L.op(ROT, L.acc):
                return None
    return L.finish()


def emit_byte(target: int, verify=True) -> str:
    """Raw Classic Malbolge source printing `target` (one byte) and halting."""
    dist, prev = _inline_bfs()
    for val in sorted((a for a in dist if a % 256 == target), key=lambda a: dist[a])[:40]:
        moves = _path(prev, val)
        if target in (v for _, v in moves):
            continue
        src = _emit_inline(moves)
        if src and (not verify or _runs_to(src, target)):
            return src
    adist, aprev = _acc_bfs()
    for val in sorted((x for x in adist if x % 256 == target), key=lambda x: adist[x])[:60]:
        moves = _path(aprev, val)
        if target in (v for op, v in moves if op != "rotW"):
            continue
        for acc in range(D_OFFSET + 1, 128):
            src = _emit_acc(moves, acc)
            if src and (not verify or _runs_to(src, target)):
                return src
    raise ValueError(f"no raw layout found for byte {target}")


def _runs_to(src: str, target: int) -> bool:
    status, _, out = mal.run(src, b"", 300_000)
    return status == "HALTED" and out == bytes([target])


def main() -> int:
    ap = argparse.ArgumentParser(description="clean-room raw Classic Malbolge emitter")
    ap.add_argument("byte", type=lambda s: int(s, 0), help="output byte 0..255")
    ap.add_argument("-o", "--output")
    args = ap.parse_args()
    src = emit_byte(args.byte)
    if args.output:
        Path(args.output).write_text(src, encoding="latin-1")
        print(f"{len(src)} cells -> {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(src + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
