#!/usr/bin/env python3
"""M4 — primera superficie de microprogramación: verificación en los dos motores."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
GIT = HERE.parents[2]
sys.path.insert(0, str(GIT / "malbolge-free" / "tools"))
import microprogram as mp      # noqa: E402
import raw_malbolge as rm      # noqa: E402

_spec = importlib.util.spec_from_file_location("mal", GIT / "MALBOLGE" / "malbolge.py")
mal = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mal)
ZIG = GIT / "MALBOLGE" / "intermediate_vm_runner.exe"


def sha(src: str) -> str:
    return hashlib.sha256(src.encode("latin-1")).hexdigest()


def zig(src: str, stdin: bytes):
    if not ZIG.exists():
        return None
    p = subprocess.run([str(ZIG), "10", src.encode("latin-1").hex(), stdin.hex(),
                        "500000", "0", "0", "0"], capture_output=True, text=True, timeout=300)
    line = next((l for l in (p.stderr + p.stdout).splitlines() if l.startswith("RESULT")), None)
    if line is None:
        return None
    kv = dict(t.split("=", 1) for t in line.split()[1:])
    hx = kv.get("out_hex", "")
    return kv["status"], int(kv.get("steps", -1)), (b"" if hx == "-" else bytes.fromhex(hx))


def check(name, src, stdin, expected, out):
    status, steps, got = mal.run(src, stdin, 500_000)
    z = zig(src, stdin)
    entry = {
        "case": name, "cells": len(src), "steps": steps, "sha256": sha(src),
        "stdin": stdin.hex(), "expected": expected.hex(), "oracle": got.hex(),
        "oracle_status": status,
        "oracle_ok": status == "HALTED" and got == expected,
        "zig": None if z is None else {"status": z[0], "steps": z[1], "out": z[2].hex()},
        "parity": z is not None and (z[0], z[1], z[2]) == (status, steps, got),
    }
    out.append(entry)
    flag = "OK " if entry["oracle_ok"] and entry["parity"] else "FAIL"
    print(f"  {flag} {name}: celdas={len(src)} steps={steps} out={got.hex()} paridad={entry['parity']}", flush=True)
    return entry


def main() -> int:
    t0 = time.time()
    results = {"milestones": {}}

    print("M4A multi-output")
    a = []
    for data in [b"A", b"AB", b"HI\n", bytes([0, 255, 127]), b">A\n"]:
        src = mp.emit_program([("out", b) for b in data] + [("halt",)])
        check(f"out {data!r}", src, b"", data, a)
    results["milestones"]["M4A_multi_output"] = a

    print("M4B input")
    b = []
    src = mp.emit_program([("in",), ("out_acc",), ("halt",)])
    for inp in [b"\x00", b"A", b"\x7f", b"\xff"]:
        check(f"echo {inp.hex()}", src, inp, inp, b)
    check("EOF", src, b"", bytes([mp.EOF_BYTE]), b)
    results["milestones"]["M4B_input"] = b
    results["eof_semantics"] = (f"sin entrada, IN deja A = {mal.EOF_VALUE} (C2); "
                                f"OUT emite {mal.EOF_VALUE} % 256 = 0x{mp.EOF_BYTE:02x}")

    print("M4C estado (IN -> crazy -> OUT)")
    c = []
    p = mp.MicroProgram()
    p.read()
    v = mp.valid_values(p.d)[0]
    p.opr_op(v)
    p.out()
    p.halt()
    src = p.source()
    results["m4c_operand"] = v
    for inp in [b"A", b"\x00", b"\xff", b"z"]:
        expected = bytes([mal.crazy(inp[0], v) % 256])
        check(f"crazy({inp[0]},{v})", src, inp, expected, c)
    results["milestones"]["M4C_state"] = c

    print("M4D salto incondicional")
    d = []
    src = mp.emit_program([("out", 0x41), ("jmp", "done"), ("out", 0x58),
                           ("label", "done"), ("out", 0x42), ("halt",)])
    e = check("A jmp X done B", src, b"", b"AB", d)
    e["trap_byte_absent"] = b"X" not in bytes.fromhex(e["oracle"])
    results["milestones"]["M4D_jump"] = d

    print("M4E microprograma compuesto")
    m = []
    prog = [("out", 0x3e), ("in",), ("out_acc",), ("jmp", "done"), ("out", 0x58),
            ("label", "done"), ("out", 0x0a), ("halt",)]
    src = mp.emit_program(prog)
    results["m4e_source"] = src
    results["m4e_sha256"] = sha(src)
    for inp in [b"A", b"\x00", b"z", b"\xff"]:
        check(f"prompt+echo {inp.hex()}", src, inp, b">" + inp + b"\n", m)
    results["milestones"]["M4E_microprogram"] = m

    print("determinismo y regresión")
    results["determinism"] = {
        "m4e_sha_stable": len({sha(mp.emit_program(prog)) for _ in range(5)}) == 1,
        "m4a_sha_stable": len({sha(mp.emit_program([("out", x) for x in b"HI\n"] + [("halt",)]))
                               for _ in range(5)}) == 1,
    }
    ok3 = sum(1 for x in range(256)
              if mal.run(rm.emit_byte(x, verify=False), b"", 300_000)[2] == bytes([x]))
    results["m3_regression"] = f"{ok3}/256"

    sizes = []
    for n in (1, 2, 3, 5, 8):
        data = bytes(range(65, 65 + n))
        s = mp.emit_program([("out", x) for x in data] + [("halt",)])
        st, steps, _ = mal.run(s, b"", 500_000)
        sizes.append({"bytes": n, "cells": len(s), "steps": steps,
                      "cells_per_byte": round(len(s) / n, 1)})
    results["growth"] = sizes

    every = [e for lst in results["milestones"].values() for e in lst]
    results["summary"] = {
        "cases": len(every),
        "oracle_ok": sum(e["oracle_ok"] for e in every),
        "parity_ok": sum(e["parity"] for e in every),
        "verdict": "M4_PASS" if all(e["oracle_ok"] and e["parity"] for e in every)
                   and results["m3_regression"] == "256/256"
                   and all(results["determinism"].values()) else "PARTIAL",
        "runtime_seconds": round(time.time() - t0, 1),
    }
    (HERE / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({**results["summary"], "m3_regression": results["m3_regression"],
                      "determinism": results["determinism"]}, indent=1))
    print("crecimiento:", results["growth"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
