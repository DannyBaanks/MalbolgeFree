"""Deterministic, non-searching Classic witness builder.

This tool deliberately builds only opcode plans. It does not claim to solve
arbitrary control-flow synthesis or compile Brainfuck.
"""
from __future__ import annotations

from classic_codec import assemble, parse_plan


def build(plan: str) -> str:
    """Encode a comma/space-separated opcode plan at its actual positions."""
    return assemble(parse_plan(plan))


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Build a deterministic Classic opcode witness")
    parser.add_argument("plan")
    parser.add_argument("--output")
    args = parser.parse_args()
    source = build(args.plan)
    if args.output:
        with open(args.output, "w", encoding="latin-1", newline="") as handle:
            handle.write(source)
    print(f"PLAN={args.plan}")
    print(f"SOURCE={source!r}")
    print(f"BYTES={len(source)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
