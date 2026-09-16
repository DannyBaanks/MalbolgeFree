"""Autonomous positional codec for Malbolge Classic source."""
from __future__ import annotations

import argparse
from dataclasses import dataclass

MEMORY_SIZE = 3 ** 10
OPCODES = {4: "jmp", 5: "out", 23: "in", 39: "rot", 40: "movd", 62: "opr", 68: "nop", 81: "end"}
NAME_TO_OPCODE = {name: opcode for opcode, name in OPCODES.items()}


@dataclass(frozen=True)
class Instruction:
    position: int
    character: str
    opcode: int
    name: str
    valid: bool


def encode(opcode: int, position: int) -> str:
    if not 0 <= opcode <= 93:
        raise ValueError("opcode must be in 0..93")
    residue = (opcode - position) % 94
    return chr(residue if residue >= 33 else residue + 94)


def decode(character: str, position: int) -> int:
    if len(character) != 1 or not 33 <= ord(character) <= 126:
        raise ValueError("character must be printable ASCII 33..126")
    return (ord(character) + position) % 94


def assemble(opcodes: list[int]) -> str:
    if len(opcodes) > MEMORY_SIZE:
        raise ValueError(f"program exceeds Classic memory ({MEMORY_SIZE} cells)")
    return "".join(encode(opcode, position) for position, opcode in enumerate(opcodes))


def disassemble(source: str) -> list[Instruction]:
    chars = [char for char in source if not char.isspace()]
    if len(chars) > MEMORY_SIZE:
        raise ValueError(f"program exceeds Classic memory ({MEMORY_SIZE} cells)")
    result = []
    for position, char in enumerate(chars):
        opcode = decode(char, position)
        result.append(Instruction(position, char, opcode, OPCODES.get(opcode, "invalid"), opcode in OPCODES))
    return result


def parse_plan(text: str) -> list[int]:
    result = []
    for token in text.replace(",", " ").split():
        lowered = token.lower()
        result.append(NAME_TO_OPCODE[lowered] if lowered in NAME_TO_OPCODE else int(token))
    return result


def parity() -> tuple[int, list[str]]:
    checked = 0
    problems = []
    for position in range(MEMORY_SIZE):
        for opcode in OPCODES:
            char = encode(opcode, position)
            checked += 1
            if decode(char, position) != opcode:
                problems.append(f"position={position} opcode={opcode} char={char!r}")
    return checked, problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Malbolge Classic positional codec")
    commands = parser.add_subparsers(dest="command", required=True)
    asm = commands.add_parser("assemble")
    asm.add_argument("plan")
    dis = commands.add_parser("disassemble")
    dis.add_argument("source")
    dis.add_argument("--file", action="store_true")
    commands.add_parser("parity")
    args = parser.parse_args()
    if args.command == "assemble":
        print(assemble(parse_plan(args.plan)))
        return 0
    if args.command == "disassemble":
        source = open(args.source, encoding="latin-1").read() if args.file else args.source
        items = disassemble(source)
        for item in items:
            print(f"{item.position:5d} {item.character!r:4} ASCII={ord(item.character):3d} op={item.opcode:2d} {item.name}")
        return 0 if all(item.valid for item in items) else 1
    checked, problems = parity()
    if problems:
        print(f"PARITY FAIL: {len(problems)} / {checked}")
        print(problems[0])
        return 1
    print(f"PARITY PASS: {checked} positional instruction pairs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
