#!/usr/bin/env python3
"""hell_frontend — lmao-lite frontends that emit Classic HeLL (hybrid pipeline, slice 1).

Written from the HeLL semantics described in LMAO's README (no LMAO code or examples copied).

Frontends
---------
* ``text``: print an arbitrary byte string, then halt.
  For each byte b: a Rot gadget rotates a data cell holding rotl(b) so A = b, then an Out
  gadget prints A mod 256.  Each value cell is rotated exactly once.
* ``echo``: read N input bytes and print each one right away, then halt.

Gadget protocol (per README): a data cell ``X`` stores address(X)-1, so the Jmp that reads it
lands on the X/Nop cell; the cell after the gadget pointer is the gadget's D argument; ``R_X``
re-enters at address(X), which encrypts the X/Nop cell back to X and runs the gadget's Jmp.

    py hell_frontend.py text "Hello, World!\\n" | py lmao_bridge.py ...
"""
from __future__ import annotations

import argparse
import sys

TRIT9 = 3 ** 9
MEM = 3 ** 10

GADGETS = """.CODE
ROT:
\tRot/Nop
\tJmp

OUT:
\tOut/Nop
\tJmp

IN:
\tIn/Nop
\tJmp

HLT:
\tHlt
"""


def rotl(value: int) -> int:
    """Inverse of Classic rot (rotate right one trit over 10 trits)."""
    return (value % TRIT9) * 3 + value // TRIT9


def rot(value: int) -> int:
    return value // 3 + (value % 3) * TRIT9


def text_program(data: bytes) -> str:
    lines = [GADGETS, ".DATA", "ENTRY:"]
    for b in data:
        v = rotl(b)
        assert rot(v) == b
        lines.append(f"\tROT {v} R_ROT OUT ?- R_OUT   // byte {b}")
    lines.append("\tHLT")
    return "\n".join(lines) + "\n"


def echo_program(n: int) -> str:
    lines = [GADGETS, ".DATA", "ENTRY:"]
    lines += ["\tIN ?- R_IN OUT ?- R_OUT"] * n
    lines.append("\tHLT")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="emit Classic HeLL from simple frontends")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("text")
    t.add_argument("string", help="Python-escaped string, e.g. 'Hello\\n'")
    e = sub.add_parser("echo")
    e.add_argument("n", type=int)
    args = ap.parse_args()
    if args.cmd == "text":
        sys.stdout.write(text_program(args.string.encode("latin-1").decode("unicode_escape").encode("latin-1")))
    else:
        sys.stdout.write(echo_program(args.n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
