"""Acceptance harness for the m7 BF->BFIR1 compiler.

Purpose: be the oracle-driven target that any regenerated compiler must pass, and
keep the CURRENT limits measured rather than assumed. Every case states what is
required; the summary separates "required and true today" from "required and not
yet true", so the second group is a work list instead of a surprise.

The oracle is `ref_encode` below, a direct transcription of the documented
BFIR1 semantics (src of truth: tests/bf_to_ir.zig + tests/bf_ir_image.zig). It
shares no code with the compiler under test, which is a ~1500-character
Brainfuck program, so agreement is real evidence.

Run directly for a report:
    python3 evidence/m7_compiler_acceptance.py

Exit code is 0 when every case that is expected to pass today does pass. Cases
marked future=True are reported and never fail the run.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPILER = ROOT / "m7" / "compiler.bf"

# ── oracle ────────────────────────────────────────────────────────────────────
OPCODES = {">": 1, "<": 2, "+": 3, "-": 4, ".": 5, ",": 6, "[": 7, "]": 8}


def ref_compile(src: str):
    code, opens = [], []
    for source_pos, ch in enumerate(src):
        if ch not in OPCODES:
            continue
        oc = OPCODES[ch]
        idx = len(code)
        if oc == 7:
            opens.append(idx)
            code.append([oc, None, source_pos])
        elif oc == 8:
            if not opens:
                raise ValueError("unbalanced ]")
            o = opens.pop()
            code.append([oc, o, source_pos])
            code[o][1] = idx
        else:
            code.append([oc, None, source_pos])
    if opens:
        raise ValueError("unbalanced [")
    return code


def ref_encode(src: str) -> bytes:
    code = ref_compile(src)
    out = bytearray(b"BFIR1")
    out += len(code).to_bytes(4, "little")
    for oc, target, sp in code:
        out.append(oc)
        out.append(1 if target is not None else 0)
        out.append(0)
        out.append(0)
        out += (target if target is not None else 0).to_bytes(4, "little")
        out += sp.to_bytes(4, "little")
    return bytes(out)


# ── brainfuck interpreter (independent of both) ──────────────────────────────
def run_bf(prog_src: str, inp: bytes, max_steps: int = 60_000_000):
    prog = [c for c in prog_src if c in "+-<>.,[]"]
    tape = [0] * 8192
    ptr = ip = steps = ipos = 0
    out = bytearray()
    jump, stack = {}, []
    for i, c in enumerate(prog):
        if c == "[":
            stack.append(i)
        elif c == "]":
            j = stack.pop()
            jump[i], jump[j] = j, i
    while steps < max_steps and ip < len(prog):
        c = prog[ip]
        steps += 1
        ip += 1
        if c == ">":
            ptr += 1
        elif c == "<":
            ptr = max(0, ptr - 1)
        elif c == "+":
            tape[ptr] = (tape[ptr] + 1) % 256
        elif c == "-":
            tape[ptr] = (tape[ptr] - 1) % 256
        elif c == ".":
            out.append(tape[ptr])
        elif c == ",":
            tape[ptr] = inp[ipos] if ipos < len(inp) else 0
            ipos += 1
        elif c == "[":
            if tape[ptr] == 0:
                ip = jump[ip - 1] + 1
        elif c == "]":
            if tape[ptr] != 0:
                ip = jump[ip - 1]
    return bytes(out), steps


# ── acceptance table ──────────────────────────────────────────────────────────
# future=True means: required for a correct compiler, NOT true today.
# Those are the acceptance criteria for a regenerated stride-N compiler.
CASES = [
    # name, source, must_match_today
    ("empty",              "",                          True),
    ("plus_plus",          "++",                        True),
    ("mixed_ops",          "+++.-.",                    True),
    ("pointers",           ">+++<+>.>.",                True),
    ("io",                 ",+.",                       True),
    ("nested_pointers",    ">>+<++.",                   True),
    ("at_cap_254",         "+" * 254,                   True),   # last count that fits a byte
    ("over_cap_255",       "+" * 255,                   False),  # wraps the 1-byte counter
    ("over_cap_300",       "+" * 300,                   False),
    ("simple_loop",        "++++++[>++++++<-]>.",       False),  # brackets unresolved
    ("nested_loop",        "+[>+[>++<-]<-]>>.",         False),
    ("bracket_nested3",    "+[[[->+<]]]>+.",                 False),
]


def classify(got: bytes, want: bytes) -> str:
    if got == want:
        return "MATCH"
    if len(got) < 9 or got[:5] != b"BFIR1":
        return "BROKEN_NO_HEADER"
    if len(got) == 9:
        return "EMPTY_IMAGE"
    count = int.from_bytes(got[5:9], "little")
    records = (len(got) - 9) // 12
    if count != records:
        return f"INCONSISTENT(count={count},records={records})"
    return "PLAUSIBLE_BUT_WRONG"


def main() -> int:
    compiler = COMPILER.read_text(encoding="utf-8")
    required_today_ok = True
    future_failures = []

    print(f"compiler: {COMPILER.relative_to(ROOT)} ({len(compiler)} chars)")
    print(f"{'case':18} {'required today':>15} {'verdict':>22} {'steps':>10}")
    print("-" * 70)

    for name, src, must_today in CASES:
        want = ref_encode(src)
        got, steps = run_bf(compiler, src.encode("latin-1"))
        verdict = classify(got, want)
        ok = verdict == "MATCH"
        label = "yes" if must_today else "no (future)"
        print(f"{name:18} {label:>15} {verdict:>22} {steps:>10}")
        if must_today and not ok:
            required_today_ok = False
        if not must_today and not ok:
            future_failures.append((name, verdict))

    print("-" * 70)
    print(f"required-today cases passing: {'ALL' if required_today_ok else 'BROKEN'}")
    print(f"future criteria not yet met: {len(future_failures)}")
    for name, verdict in future_failures:
        print(f"  - {name}: {verdict}")
    print()
    print("ACCEPTANCE_REQUIRED_TODAY=" + ("PASS" if required_today_ok else "FAIL"))
    print("ACCEPTANCE_FUTURE_CRITERIA_MET=" + f"{len(CASES) - 2 - len(future_failures)}/{len(CASES) - 2}")
    return 0 if required_today_ok else 1


if __name__ == "__main__":
    sys.exit(main())