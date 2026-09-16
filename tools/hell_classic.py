#!/usr/bin/env python3
"""hell_classic — clean-room HeLL assembler for Malbolge Classic (lmao-lite, milestone M1).

Written from the HeLL language description in LMAO's README only (no LMAO source code was
read or copied; LMAO is GPLv3 and is used exclusively as an external behavioural oracle).

MEASURED RESULT (2026-09-13): load-time layouts are a dead end.  For LMAO's
example_simple_cat, all 1,504 non-overlapping placements of the MovD/In/Out gadgets
(addresses <= 126, the only ones whose R_ values are printable) and of the 9-cell data
block were enumerated: 0 have every data cell load-valid; the best reaches 5/9.
Runtime initialization code is therefore mandatory even for the simplest HeLL program.
This module is kept as the verified parser/cell-physics layer for milestone M2.

M1 scope: LOAD-TIME layouts.  Every memory cell the program needs must be representable as a
source character that passes the Classic loader, so there is no runtime initialization code.
Programs that need it (large constants, U_ offsets, cycles without a load-valid start
character) are rejected with an explicit reason instead of being miscompiled.

HeLL execution model implemented (per the README):
  * Data value `LABEL` stores address(LABEL) - 1; `R_LABEL` stores address(LABEL).
  * A code cell is an xlat2 cycle `A/B/...`: its effective command on successive executions.
    `Nop` in a cycle means "no effect" (the Nop opcode or any non-command value).
    A single command such as `Jmp` is executed without being encrypted when it is a Jmp
    (the VM encrypts the *landing* cell), so Jmp cells are naturally loop-resistant.
  * Every referenced code label L gets a landing cell L-1 that no block may use.
  * Start state required by HeLL: the next executed instruction is a Jmp with D = ENTRY.
    Startup generated here: cell 0 is a Jmp reading itself (value 98), the VM lands on 98,
    runs RNop-free plain Nop cells 99..97+ENTRY and reaches a Jmp at 98+ENTRY with D = ENTRY.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

MEM = 59049
C2 = MEM - 1
CONSTS = {"C0": 0, "C1": 29524, "C2": C2, "C20": 59046, "C21": 59047, "EOF": C2}
COMMANDS = {"Jmp": 4, "Out": 5, "In": 23, "Rot": 39, "MovD": 40, "Opr": 62, "Nop": 68, "Hlt": 81}
OPCODES = set(COMMANDS.values())
ORIGINAL = r"""!"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~"""
TRANSLATED = r"""5z]&gqtyfr$(we4{WP)H-Zn,[%\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G"i@"""
ENC = {ord(o): ord(t) for o, t in zip(ORIGINAL, TRANSLATED)}


class HellError(ValueError):
    pass


# ── parsing ───────────────────────────────────────────────────────────────────

@dataclass
class Cell:
    kind: str                      # code: "cycle"; data: "num", "label", "rlabel", "free", "reserved"
    value: object = None           # cycle tuple, int, or label name
    line: int = 0


@dataclass
class Block:
    section: str
    labels: dict[str, int] = field(default_factory=dict)   # label -> offset inside block
    cells: list[Cell] = field(default_factory=list)
    offset: int | None = None


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    out = []
    for line in text.splitlines():
        in_q = None
        cut = len(line)
        i = 0
        while i < len(line):
            ch = line[i]
            if in_q:
                if ch == "\\":
                    i += 2
                    continue
                if ch == in_q:
                    in_q = None
            elif ch in "'\"":
                in_q = ch
            elif ch in ";%#" or line.startswith("//", i):
                cut = i
                break
            i += 1
        out.append(line[:cut])
    return "\n".join(out)


TOKEN = re.compile(r"""\s*(?:(?P<str>"(?:\\.|[^"\\])*")|(?P<chr>'(?:\\.|[^'\\])')|(?P<sym>[{}:,@])|(?P<word>[^\s{}:,@"']+))""")
ESC = {"n": "\n", "r": "\r", "t": "\t", "\\": "\\", "'": "'", '"': '"', "0": "\0"}


def unescape(body: str) -> str:
    return re.sub(r"\\(.)", lambda m: ESC.get(m.group(1), m.group(1)), body)


def parse(text: str) -> list[Block]:
    text = strip_comments(text)
    blocks: list[Block] = []
    section = None
    current: Block | None = None
    in_brace = False

    def close():
        nonlocal current
        if current is not None and (current.cells or current.labels):
            blocks.append(current)
        current = None

    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            if not in_brace:
                close()
            continue
        pos = 0
        tokens = []
        while pos < len(raw):
            m = TOKEN.match(raw, pos)
            if not m or m.end() == pos:
                break
            tokens.append((m.lastgroup, m.group(m.lastgroup)))
            pos = m.end()
        i = 0
        while i < len(tokens):
            kind, tok = tokens[i]
            if kind == "word" and tok in (".CODE", ".DATA"):
                close()
                section = tok[1:].lower()
                i += 1
                continue
            if section is None:
                raise HellError(f"line {number}: content before .CODE/.DATA")
            if tok == "{":
                close()
                in_brace = True
                current = Block(section)
                i += 1
                continue
            if tok == "}":
                in_brace = False
                close()
                i += 1
                continue
            if current is None:
                current = Block(section)
            if tok == "@" or tok == ".OFFSET":
                word = tokens[i + 1][1]
                current.offset = CONSTS[word] if word in CONSTS else int(word, 0)
                i += 2
                continue
            if kind == "word" and i + 1 < len(tokens) and tokens[i + 1][1] == ":":
                current.labels[tok] = len(current.cells)
                i += 2
                continue
            if tok == ",":
                i += 1
                continue
            if section == "code":
                if tok == "RNop":
                    current.cells.append(Cell("cycle", ("Nop", "Nop"), number))
                else:
                    parts = tuple(tok.split("/"))
                    if not all(p in COMMANDS for p in parts):
                        raise HellError(f"line {number}: unknown code entry {tok!r}")
                    current.cells.append(Cell("cycle", parts, number))
                i += 1
                continue
            # data section
            if kind == "str":
                sep = None
                if i + 2 < len(tokens) and tokens[i + 1][1] == ",":
                    sep = tokens[i + 2]
                chars = unescape(tok[1:-1])
                for k, ch in enumerate(chars):
                    current.cells.append(Cell("num", ord(ch), number))
                    if sep is not None and k < len(chars) - 1:
                        current.cells.append(_data_word(sep, number))
                i += 3 if sep is not None else 1
                continue
            if tok.startswith("U_"):
                raise HellError(f"line {number}: U_ offsets need runtime layout support (milestone M2)")
            current.cells.append(_data_word((kind, tok), number))
            i += 1
    close()
    return blocks


def _data_word(token, number) -> Cell:
    kind, tok = token
    if kind == "chr":
        return Cell("num", ord(unescape(tok[1:-1])), number)
    if tok == "?-":
        return Cell("free", None, number)
    if tok == "?":
        return Cell("reserved", None, number)
    if tok in CONSTS:
        return Cell("num", CONSTS[tok], number)
    if re.fullmatch(r"0t[0-2]{1,10}", tok):
        return Cell("num", int(tok[2:], 3), number)
    if re.fullmatch(r"\d+", tok):
        value = int(tok)
        if value > C2:
            raise HellError(f"line {number}: constant {value} exceeds C2")
        return Cell("num", value, number)
    if re.fullmatch(r"R_[A-Za-z_]\w*", tok):
        return Cell("rlabel", tok[2:], number)
    if re.fullmatch(r"[A-Za-z_]\w*", tok):
        return Cell("label", tok, number)
    raise HellError(f"line {number}: unsupported data expression {tok!r} (arithmetic is milestone M2)")


# ── cell physics ──────────────────────────────────────────────────────────────

def orbit(ch: int) -> list[int]:
    out, x = [ch], ENC[ch]
    while x != ch:
        out.append(x)
        x = ENC[x]
    return out


def effect(value: int, position: int) -> str:
    op = (value + position) % 94
    return next((n for n, o in COMMANDS.items() if o == op and op != 68), "Nop")


def cycle_chars(cycle: tuple[str, ...], residue: int) -> list[int]:
    """Load-valid start characters at this position residue that realise the cycle."""
    found = []
    for ch in range(33, 127):
        if (ch + residue) % 94 not in OPCODES:
            continue
        orb = orbit(ch)
        if len(cycle) == 1:
            if effect(ch, residue) == cycle[0]:
                found.append(ch)
            continue
        if len(orb) % len(cycle) and len(cycle) % len(orb):
            continue
        span = max(len(orb), len(cycle))
        if all(effect(orb[i % len(orb)], residue) == cycle[i % len(cycle)] for i in range(span)) \
                and len(orb) == len(cycle):
            found.append(ch)
    return found


def legal_chars(position: int) -> list[int]:
    return [ch for ch in range(33, 127) if (ch + position) % 94 in OPCODES]


def nop_char(position: int) -> int:
    ch = (68 - position) % 94
    return ch if ch >= 33 else ch + 94


# ── layout search ─────────────────────────────────────────────────────────────

def assemble(text: str, max_address: int = 400) -> str:
    blocks = parse(text)
    code_labels = {n: b for b in blocks if b.section == "code" for n in b.labels}
    data_labels = {n: b for b in blocks if b.section == "data" for n in b.labels}
    if "ENTRY" not in data_labels:
        raise HellError("the .DATA section must define ENTRY")
    for b in blocks:
        for c in b.cells:
            if c.kind in ("label", "rlabel") and c.value not in code_labels and c.value not in data_labels:
                raise HellError(f"line {c.line}: unknown label {c.value!r}")
            if c.kind == "rlabel" and c.value not in code_labels:
                raise HellError(f"line {c.line}: R_{c.value} must reference a .CODE label")
    referenced_code = {c.value for b in blocks for c in b.cells if c.kind in ("label", "rlabel") and c.value in code_labels}
    for b in blocks:
        for c in b.cells:
            if b.section == "code":
                if not any(cycle_chars(c.value, r) for r in range(94)):
                    raise HellError(f"line {c.line}: cycle {'/'.join(c.value)} has no load-valid start character "
                                    "at any position (needs runtime initialization, milestone M2)")
            elif c.kind == "num" and not 33 <= c.value <= 126:
                raise HellError(f"line {c.line}: value {c.value} is not a printable byte "
                                "(needs runtime initialization, milestone M2)")

    order = sorted(blocks, key=lambda b: (b.section != "code", -len(b.cells)))
    placed: dict[int, int] = {}          # position -> char (fixed)
    owner: dict[int, str] = {}           # position -> role
    address: dict[int, int] = {}         # id(block) -> start

    def label_addr(name):
        b = code_labels.get(name) or data_labels[name]
        return address[id(b)] + b.labels[name]

    def try_block(k: int) -> bool:
        if k == len(order):
            return finish()
        b = order[k]
        need_landing = [off for n, off in b.labels.items() if n in referenced_code]
        starts = [b.offset] if b.offset is not None else range(1, max_address)
        for start in starts:
            cells = range(start, start + len(b.cells))
            landings = [start + off - 1 for off in need_landing]
            if any(p in owner for p in cells) or any(p in owner or p in cells for p in landings):
                continue
            if b.section == "code":
                chars = []
                for i, c in enumerate(b.cells):
                    options = cycle_chars(c.value, (start + i) % 94)
                    if not options:
                        break
                    chars.append(options[0])
                if len(chars) != len(b.cells):
                    continue
            else:
                chars = [None] * len(b.cells)
            address[id(b)] = start
            for i, p in enumerate(cells):
                owner[p] = f"{b.section}"
                if chars[i] is not None:
                    placed[p] = chars[i]
            for p in landings:
                owner[p] = "landing"
            if try_block(k + 1):
                return True
            for p in list(cells) + landings:
                owner.pop(p, None)
                placed.pop(p, None)
            del address[id(b)]
        return False

    result: dict = {}

    def finish() -> bool:
        # data values now known; check load legality of every data cell
        trial = dict(placed)
        for b in blocks:
            if b.section != "data":
                continue
            for i, c in enumerate(b.cells):
                p = address[id(b)] + i
                if c.kind == "num":
                    v = c.value
                elif c.kind == "label":
                    v = label_addr(c.value) - 1
                elif c.kind == "rlabel":
                    v = label_addr(c.value)
                else:
                    v = None
                if v is None:
                    trial[p] = legal_chars(p)[0]
                    continue
                if not 33 <= v <= 126 or (v + p) % 94 not in OPCODES:
                    return False
                trial[p] = v
        entry = label_addr("ENTRY")
        # startup: cell 0 = Jmp (char 98 reads itself), landing 98, Nop 99..97+entry, Jmp at 98+entry
        startup = {0: 98, 98: None}
        startup.update({p: nop_char(p) for p in range(99, 98 + entry)})
        jmp_at = 98 + entry
        startup[jmp_at] = (4 - jmp_at) % 94 if (4 - jmp_at) % 94 >= 33 else (4 - jmp_at) % 94 + 94
        for p, ch in startup.items():
            if p in owner:
                return False
            if ch is not None:
                trial[p] = ch
        last = max(trial)
        source = []
        for p in range(last + 1):
            source.append(chr(trial[p] if p in trial else nop_char(p)))
        result["source"] = "".join(source)
        return True

    if not try_block(0):
        raise HellError(f"no load-time layout found below address {max_address} (milestone M2 adds runtime initialization)")
    return result["source"]


def main() -> int:
    ap = argparse.ArgumentParser(description="clean-room HeLL -> Malbolge Classic (lmao-lite M1, load-time layouts)")
    ap.add_argument("file", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    args = ap.parse_args()
    try:
        source = assemble(args.file.read_text(encoding="utf-8"))
    except HellError as exc:
        print(f"HELL_ERROR: {exc}", file=sys.stderr)
        return 2
    if args.output:
        args.output.write_text(source, encoding="ascii")
    else:
        print(source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
