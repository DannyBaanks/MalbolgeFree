"""Epochal differential: canonical Zig core vs the parametric Python core.

This closes EPOCHAL_PYTHON_PARITY for the epochal policy. Until now the Python
core had no `epochal` at all, so the whole ladder (10 -> 19) rested on one
engine. Two independent implementations of the same spec now have to agree.

The Python side imports src/malbolge_core.py on purpose: the claim under test is
that the two *implementations* agree, not that one matches a third transcription.
compare_m2.py keeps its inline oracle for Classic because there the point is a
specification transcription, not the shipped Python core.

Read-only: prints a verdict, writes nothing unless --output names a NEW path.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CASES = {
    # name: (width, witness length, max steps)
    "epochal_w3_multi": (3, 300, 300),
    "epochal_w4_multi": (4, 1200, 1200),
    "epochal_w10_single": (10, 60000, 60000),
}


def load_core():
    spec = importlib.util.spec_from_file_location(
        "mb_core", ROOT / "src" / "malbolge_core.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def build_witness(length: int) -> str:
    """Identical to evidence/gen_frontier_witness.py and run_epochal.zig:
    only in/out/crazy/nop at every position."""
    out = []
    for pos in range(length):
        for cv in range(33, 127):
            op = (cv + pos) % 94
            if op in (5, 23, 62, 68):
                out.append(chr(cv))
                break
    return "".join(out)


def parse(line: str) -> dict:
    fields = dict(tok.split("=", 1) for tok in line.split() if "=" in tok)
    return fields


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=pathlib.Path, help="optional NEW report path")
    args = parser.parse_args()

    proc = subprocess.run(
        [
            "zig", "run", "--dep", "malbolge_free=malbolge_free",
            "-Mroot=evidence/run_epochal.zig",
            "-Mmalbolge_free=src/malbolge_free.zig",
        ],
        cwd=ROOT, capture_output=True, text=True, timeout=900,
    )
    if proc.returncode:
        print(proc.stderr or proc.stdout, file=sys.stderr)
        return 1

    mb = load_core()
    zig_cases: dict[str, dict] = {}
    extras: list[str] = []
    for line in (proc.stdout + proc.stderr).splitlines():
        line = line.strip()
        if line.startswith("CASE "):
            zig_cases[parse(line[5:])["name"]] = parse(line[5:])
        elif line.startswith(("DETERMINISM ", "DEGENERATION ", "GUARD ")):
            extras.append(line)

    failures = []
    rows = []
    for name, (width, wlen, steps) in CASES.items():
        if name not in zig_cases:
            failures.append((name, "missing_in_zig_output"))
            continue
        z = zig_cases[name]
        src = build_witness(wlen)

        vm = mb.MalbolgeCore(width=width, mem_limit=None, growth_policy="epochal")
        vm.load(src)
        p = vm.run(steps, b"")
        py_digest = hashlib.sha256(p["stdout"].encode("latin-1")).hexdigest()

        observed = {
            "status": p["status"],
            "steps": p["steps"],
            "padwidth": vm.padwidth,
            "growth": len(vm.stats["width_growth_events"]),
            "final_c": vm.stats["final_c"],
            "final_d": vm.stats["final_d"],
            "encrypted": vm.stats["encrypted_cells"],
        }
        # Every field below is produced independently by each engine; none is
        # defaulted, so a disagreement on any of them fails the gate.
        compare = {
            "status": (z["status"], p["status"]),
            "steps": (int(z["steps"]), p["steps"]),
            "padwidth": (int(z["padwidth"]), vm.padwidth),
            "growth": (z["growth"] if z["growth"] == "-" else int(z["growth"]),
                       len(vm.stats["width_growth_events"])),
            "final_c": (int(z["final_c"]), vm.stats["final_c"]),
            "final_d": (int(z["final_d"]), vm.stats["final_d"]),
            "encrypted": (int(z["encrypted"]), vm.stats["encrypted_cells"]),
            "sha256": (z["sha256"], py_digest),
        }
        bad = {k: v for k, v in compare.items() if v[0] != v[1]}
        rows.append({
            "case": name, "width": width, "witness_len": wlen,
            "zig": {k: z[k] for k in ("status", "steps", "padwidth", "growth", "final_c", "final_d", "sha256")},
            "python": {"status": p["status"], "steps": p["steps"], "padwidth": vm.padwidth,
                       "growth": len(vm.stats["width_growth_events"]), "sha256": py_digest},
            "mismatches": bad,
        })
        if bad:
            failures.append((name, bad))

    # The Python constructor must refuse a wrapping address space for epochal,
    # otherwise the policy would be silently dead code.
    guard_ok = False
    try:
        mb.MalbolgeCore(width=10, mem_limit=3 ** 10, growth_policy="epochal")
    except ValueError:
        guard_ok = True

    report = {
        "phase": "EPOCHAL",
        "claim": "EPOCHAL_PYTHON_PARITY",
        "zig_runtime": "src/malbolge_free.zig",
        "python_runtime": "src/malbolge_core.py",
        "cases": len(rows),
        "rows": rows,
        "extras": extras,
        "python_guard_rejects_wrap": guard_ok,
        "verdict": "PASS" if not failures and guard_ok else "FAIL",
    }

    for e in extras:
        print(e)
    print(f"EPOCHAL_CASES={len(rows)}")
    print(f"PYTHON_GUARD_REJECTS_WRAP={guard_ok}")
    for r in rows:
        z, p = r["zig"], r["python"]
        print(
            f"  {r['case']}: zig steps={z['steps']} padwidth={z['padwidth']} growth={z['growth']} "
            f"| py steps={p['steps']} padwidth={p['padwidth']} growth={p['growth']} "
            f"| match={'yes' if not r['mismatches'] else 'NO'}"
        )
    if failures:
        print(f"MISMATCHES={failures}")
    print("EPOCHAL_PYTHON_PARITY=" + report["verdict"])

    if args.output:
        out = args.output if args.output.is_absolute() else ROOT / args.output
        if out.exists():
            raise SystemExit(f"refusing to overwrite existing report: {out}")
        out.write_text(__import__("json").dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())