#!/usr/bin/env python3
"""lmao_bridge — hybrid lmao-lite backend: HeLL -> Classic Malbolge via external LMAO, verified.

LMAO (Matthias Lutter, GPLv3) is invoked as a separate process.  No LMAO code is imported,
linked or copied.  Location: env LMAO_EXE, else ../../_external/LMAO/lmao.exe
(see `_external/README.md` next to this repository for the pinned commit and build).

Every assembled program can be checked on two independent Classic engines of this toolkit:
MALBOLGE/malbolge.py (oracle) and MALBOLGE/intermediate_vm_runner.exe (Zig).

    py lmao_bridge.py assemble prog.hell -o prog.mb
    py lmao_bridge.py verify prog.hell --stdin 414243 --expect 414243
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
GIT = HERE.parents[1]
DEFAULT_LMAO = GIT / "_external" / "LMAO" / "lmao.exe"
ZIG_RUNNER = GIT / "MALBOLGE" / "intermediate_vm_runner.exe"

_spec = importlib.util.spec_from_file_location("classic_oracle", GIT / "MALBOLGE" / "malbolge.py")
oracle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oracle)


class BridgeError(RuntimeError):
    pass


def lmao_exe() -> Path:
    exe = Path(os.environ.get("LMAO_EXE", DEFAULT_LMAO))
    if not exe.exists():
        raise BridgeError(f"LMAO not found at {exe}; build it (see _external/README.md) or set LMAO_EXE")
    return exe


def assemble(hell_text: str) -> str:
    """Assemble HeLL source text with LMAO; return Classic Malbolge source (whitespace kept)."""
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "program.hell"
        out = Path(tmp) / "program.mb"
        src.write_text(hell_text, encoding="utf-8")
        p = subprocess.run([str(lmao_exe()), "-o", str(out), str(src)], capture_output=True, text=True, timeout=600)
        if p.returncode != 0 or not out.exists():
            raise BridgeError(f"LMAO failed (exit {p.returncode}): {(p.stderr + p.stdout).strip()[-500:]}")
        return out.read_text(encoding="latin-1")


@dataclass
class Run:
    status: str
    steps: int
    output: bytes


def run_oracle(source: str, stdin: bytes, fuel: int = 50_000_000) -> Run:
    status, steps, out = oracle.run(source, stdin, fuel)
    return Run(status, steps, out)


def run_zig(source: str, stdin: bytes, fuel: int = 500_000_000) -> Run | None:
    if not ZIG_RUNNER.exists():
        return None
    with tempfile.NamedTemporaryFile("w", suffix=".mb", delete=False, encoding="latin-1") as fh:
        fh.write(source)
        path = fh.name
    try:
        p = subprocess.run([str(ZIG_RUNNER), "10", "@" + path, stdin.hex(), str(fuel), "0", "0", "0"],
                           capture_output=True, text=True, timeout=3600)
    finally:
        Path(path).unlink()
    line = next((l for l in (p.stderr + p.stdout).splitlines() if l.startswith("RESULT")), None)
    if line is None:
        raise BridgeError("Zig runner produced no RESULT line")
    kv = dict(t.split("=", 1) for t in line.split()[1:])
    hexout = kv.get("out_hex", "")
    return Run(kv["status"], int(kv.get("steps", 0)), bytes.fromhex("" if hexout == "-" else hexout))


def verify(source: str, stdin: bytes, expected: bytes) -> tuple[bool, list[str]]:
    lines = []
    o = run_oracle(source, stdin)
    z = run_zig(source, stdin)
    ok_o = o.status == "HALTED" and o.output == expected
    lines.append(f"{'PASS' if ok_o else 'FAIL'}  oracle: {o.status} steps={o.steps} output={o.output[:40]!r}")
    ok = ok_o
    if z is not None:
        ok_z = z.status == "HALTED" and z.output == expected and z.steps == o.steps
        lines.append(f"{'PASS' if ok_z else 'FAIL'}  zig:    {z.status} steps={z.steps} (== oracle: {z.steps == o.steps})")
        ok = ok and ok_z
    return ok, lines


def main() -> int:
    ap = argparse.ArgumentParser(description="HeLL -> Classic via external LMAO, verified on our engines")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("assemble")
    a.add_argument("file", type=Path)
    a.add_argument("-o", "--output", type=Path)
    v = sub.add_parser("verify")
    v.add_argument("file", type=Path)
    v.add_argument("--stdin", default="", help="input bytes as hex")
    v.add_argument("--expect", required=True, help="expected output bytes as hex")
    args = ap.parse_args()
    try:
        source = assemble(args.file.read_text(encoding="utf-8"))
        if args.cmd == "assemble":
            if args.output:
                args.output.write_text(source, encoding="latin-1")
            else:
                print(source)
            print(f"cells={len(''.join(source.split()))} sha256={hashlib.sha256(source.encode('latin-1')).hexdigest()}", file=sys.stderr)
            return 0
        ok, lines = verify(source, bytes.fromhex(args.stdin), bytes.fromhex(args.expect))
        print("\n".join(lines))
        print(f"BRIDGE_VERIFY={'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1
    except BridgeError as exc:
        print(f"BRIDGE_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
