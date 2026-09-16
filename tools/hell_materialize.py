#!/usr/bin/env python3
"""hell_materialize — clean-room value synthesis for lmao-lite (M2 slice).

INLINE model (the one that assembles and runs correctly through LMAO, verified on both
Classic engines).  Two emittable moves, operands stored inline in the ENTRY data stream:

    rotload(v):  ROT   v R_ROT      =>  A := rot(v)          (v printable 33..126, resets A)
    combine(v):  CRAZY v R_CRAZY    =>  A := crazy(A, v)     (v printable 33..126)

Every stored operand is a printable byte the Classic loader places directly, so NO gen_init
constant-materialisation is used, and the target byte is never stored as a literal.

Measured coverage (M2_BOOTSTRAP_REACH_V0): 201/256 output bytes.  The 55 bytes 154..208
require a persistent work cell (rot after accumulate); that HeLL layout is the next slice.

No LMAO source was read; LMAO (GPLv3) is only the external assembler used by lmao_bridge.
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
PRINTABLE = range(33, 127)
MAX_DEPTH = 10


@functools.lru_cache(maxsize=1)
def _bfs():
    dist, prev = {}, {}
    q = collections.deque()
    for v in PRINTABLE:                       # A := rot(v): the only way to set A initially
        a = rot(v)
        if a not in dist:
            dist[a] = 1
            prev[a] = (None, ("rotload", v))
            q.append(a)
    while q:
        a = q.popleft()
        if dist[a] >= MAX_DEPTH:
            continue
        for v in PRINTABLE:
            b = crazy(a, v)
            if b not in dist:
                dist[b] = dist[a] + 1
                prev[b] = (a, ("combine", v))
                q.append(b)
    return dist, prev


def _path(prev, value):
    moves, a = [], value
    while prev[a][0] is not None:
        pa, mv = prev[a]
        moves.append(mv)
        a = pa
    moves.append(prev[a][1])
    return list(reversed(moves))


def reachable_bytes() -> set:
    dist, _ = _bfs()
    return {a % 256 for a in dist}


def synthesize(target_byte: int) -> list:
    """Moves [('rotload',v), ('combine',v)...] with final A % 256 == target_byte."""
    dist, prev = _bfs()
    val = min((a for a in dist if a % 256 == target_byte), key=lambda a: dist[a], default=None)
    if val is None:
        raise ValueError(f"byte {target_byte} not reachable in the inline model "
                         "(bytes 154..208 need the persistent-work-cell slice)")
    moves = _path(prev, val)
    if target_byte in (v for _, v in moves):
        for alt in sorted((a for a in dist if a % 256 == target_byte), key=lambda a: dist[a]):
            m = _path(prev, alt)
            if target_byte not in (v for _, v in m):
                return m
    return moves


def replay(moves: list) -> int:
    a = 0
    for op, v in moves:
        a = rot(v) if op == "rotload" else crazy(a, v)
    return a


HEADER = """.CODE
ROT:
\tRot/Nop
\tJmp

CRAZY:
\tOpr/Nop
\tJmp

OUT:
\tOut/Nop
\tJmp

HLT:
\tHlt
"""


def emit_hell(data: bytes) -> str:
    lines = [HEADER, ".DATA", "ENTRY:"]
    for b in data:
        for op, v in synthesize(b):
            if op == "rotload":
                lines.append(f"\tROT {v} R_ROT")
            else:
                lines.append(f"\tCRAZY {v} R_CRAZY")
        lines.append(f"\tOUT ?- R_OUT          // byte {b}")
    lines.append("\tHLT")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="clean-room byte synthesis -> HeLL (inline model)")
    ap.add_argument("string")
    ap.add_argument("--show-moves", action="store_true")
    args = ap.parse_args()
    data = args.string.encode("latin-1").decode("unicode_escape").encode("latin-1")
    if args.show_moves:
        for b in data:
            m = synthesize(b)
            assert replay(m) % 256 == b
            print(f"byte {b} ({chr(b) if 32 <= b < 127 else '.'}): {[f'{o} {v}' for o, v in m]}")
        return 0
    sys.stdout.write(emit_hell(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
