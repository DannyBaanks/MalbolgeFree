"""Small product CLI for codec and deterministic witness operations."""
from __future__ import annotations

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from classic_codec import assemble, disassemble, parity, parse_plan  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(prog="malbolge-free")
    commands = parser.add_subparsers(dest="command", required=True)
    asm = commands.add_parser("assemble")
    asm.add_argument("plan")
    dis = commands.add_parser("disassemble")
    dis.add_argument("source")
    dis.add_argument("--file", action="store_true")
    commands.add_parser("verify")
    args = parser.parse_args()
    if args.command == "assemble":
        print(assemble(parse_plan(args.plan)))
        return 0
    if args.command == "disassemble":
        source = pathlib.Path(args.source).read_text(encoding="latin-1") if args.file else args.source
        items = disassemble(source)
        for item in items:
            print(f"{item.position:5d} {item.character!r:4} op={item.opcode:2d} {item.name}")
        return 0 if all(item.valid for item in items) else 1
    checked, problems = parity()
    if problems:
        print(f"VERIFY FAIL {len(problems)}/{checked}")
        return 1
    print(f"VERIFY PASS {checked} positional instruction pairs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
