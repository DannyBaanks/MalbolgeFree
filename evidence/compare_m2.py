"""M2: compare the core's internal Classic trace with an independent oracle."""
from __future__ import annotations

import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
TRANSLATED = "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"
CRZ = ((1, 0, 0), (1, 0, 2), (2, 2, 1))
EOF = (1 << 128) - 1
LIMIT = 3**10


def crazy(a: int, b: int) -> int:
    out = 0
    p = 1
    for _ in range(10):
        out += CRZ[b % 3][a % 3] * p
        a //= 3
        b //= 3
        p *= 3
    return out


def oracle(source: bytes, stdin: bytes, max_steps: int = 16):
    mem = [ch for ch in source if ch not in b" \t\r\n"]
    mem += [None] * (LIMIT - len(mem))
    program_len = sum(ch is not None for ch in mem)
    for i in range(2, LIMIT):
        if mem[i] is None:
            mem[i] = crazy(mem[i - 1], mem[i - 2])

    a = c = d = 0
    input_index = 0
    output = bytearray()
    trace = []
    for step in range(1, max_steps + 1):
        cc = c % LIMIT
        cell_before = mem[cc]
        op = (cell_before + cc) % 94
        ab, cb, db = a, c, d
        enc_addr = enc_value = EOF
        halted = op == 81
        if op == 4:
            c = mem[d % LIMIT]
        elif op == 5:
            output.append(a % 256)
        elif op == 23:
            if input_index < len(stdin):
                a = stdin[input_index]
                input_index += 1
            else:
                a = EOF
        elif op == 39:
            dd = d % LIMIT
            mem[dd] = mem[dd] // 3 + (mem[dd] % 3) * (3**9)
            a = mem[dd]
        elif op == 40:
            d = mem[d % LIMIT]
        elif op == 62:
            dd = d % LIMIT
            aa = LIMIT - 1 if a == EOF else a % LIMIT
            mem[dd] = crazy(aa, mem[dd])
            a = mem[dd]
        if not halted:
            cc2 = c % LIMIT
            mc = mem[cc2]
            if 33 <= mc <= 126:
                enc_addr, enc_value = cc2, ord(TRANSLATED[mc - 33])
                mem[cc2] = enc_value
            c = (c + 1) % LIMIT
            d = (d + 1) % LIMIT
        trace.append((step, ab, cb, db, op, cell_before, a, c, d, enc_addr, enc_value))
        if halted:
            return "HALTED", step, bytes(output), trace
    return "MAX_STEPS", max_steps, bytes(output), trace


def parse(line: str):
    head, trace_text = line.rstrip().split(" trace=", 1)
    fields = head.split()
    name = fields[1]
    values = {key: value for key, value in (x.split("=", 1) for x in fields[2:])}
    actual = [tuple(map(int, item.split(","))) for item in trace_text.split(";") if item]
    return name, values["status"], int(values["steps"]), bytes.fromhex(values["stdout"]), actual


proc = subprocess.run(
    ["zig", "run", "--dep", "malbolge_free=malbolge_free", "-Mroot=evidence/run_m2.zig", "-Mmalbolge_free=src/malbolge_free.zig"],
    cwd=ROOT, capture_output=True, text=True, timeout=900,
)
if proc.returncode:
    raise SystemExit(proc.stderr or proc.stdout)

cases = {
    "out": b"cP", "input": b"uP", "eof": b"uP", "rot": b"'P",
    "movd": b"(P", "crazy": b">P", "jmp": b"bP", "nop": b"DC",
}
inputs = {"input": b"A", "eof": b""}
failures = []
seen = set()
seen_errors = {}
for line in (proc.stdout + proc.stderr).splitlines():
    if line.startswith("ERROR "):
        _, name, error = line.split()
        seen_errors[name] = error.split("=", 1)[1]
        continue
    if not line.startswith("CASE "):
        continue
    name, status, steps, stdout, actual = parse(line)
    seen.add(name)
    expected_status, expected_steps, expected_stdout, expected_trace = oracle(cases[name], inputs.get(name, b""))
    if (status, steps, stdout, actual) != (expected_status, expected_steps, expected_stdout, expected_trace):
        failures.append((name, status, steps, len(actual), expected_status, expected_steps, len(expected_trace)))
        for index, (got, want) in enumerate(zip(actual, expected_trace)):
            if got != want:
                print(f"MISMATCH_FIRST name={name} index={index} actual={got} expected={want}")
                break

expected_errors = {
    "non_printable": "InvalidSource",
    "positional_opcode": "InvalidSourceOpcode",
    "too_short": "ProgramTooShort",
}
if seen != set(cases):
    failures.append(("missing_valid_cases", sorted(set(cases) - seen)))
if seen_errors != expected_errors:
    failures.append(("load_errors", seen_errors, expected_errors))

print(f"M2_VALID_CASES={len(cases)}")
print(f"M2_ERROR_CASES={len(expected_errors)}")
print(f"M2_TRACE_STEPS={sum(len(oracle(cases[n], inputs.get(n, b''))[3]) for n in cases)}")
print("M2_TRACE_DIFFERENTIAL=" + ("PASS" if not failures else "FAIL"))
if failures:
    print(f"MISMATCHES={failures}")
    raise SystemExit(1)
