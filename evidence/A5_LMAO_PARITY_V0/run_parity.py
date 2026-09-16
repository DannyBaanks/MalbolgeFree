#!/usr/bin/env python3
"""A5: LMAO (Lutter) vs lmao-lite (ours), judged by LMAO's own testcases on our Classic engines.

    py run_parity.py --lmao-dir <LMAO clone with lmao.exe built> --driver <lmaolite_driver.exe>

LMAO sources are NOT copied into this repository (GPLv3); they are read from --lmao-dir and
checked against the SHA-256 values frozen in PREREGISTRATION.json.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
GIT = HERE.parents[2]
PRE = json.loads((HERE / "PREREGISTRATION.json").read_text(encoding="utf-8"))

spec = importlib.util.spec_from_file_location("oracle", GIT / "MALBOLGE" / "malbolge.py")
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)
ZIG = GIT / "MALBOLGE" / "intermediate_vm_runner.exe"
# Deviation declared before running: the infinite cat would print hundreds of MB at the
# preregistered fuel, so its fuel is capped for both engines.
SIMPLE_CAT_FUEL = 5_000_000


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def cases(name: str):
    rng = random.Random(20260913)
    rnd = bytes(rng.randrange(256) for _ in range(256))
    s = PRE["spec"][name]
    if name in ("example_simple_hello_world", "example_hello_world"):
        return [(b"", ("halt_exact", bytes.fromhex("48656c6c6f2c20576f726c64210a")))]
    if name == "example_simple_cat":
        return [(rnd, ("prefix", rnd))]
    if name == "example_cat_halt_on_eof":
        return [(rnd, ("halt_exact", rnd))]
    return [(k.encode(), ("halt_strip", v.encode())) for k, v in s.items()]


def judge(kind_expected, status, out):
    kind, expected = kind_expected
    if kind == "prefix":
        return "PASS" if out[:len(expected)] == expected else "FAIL"
    if status == "OUT_OF_FUEL":
        return "NOT_EVALUABLE"
    if status != "HALTED":
        return "FAIL"
    got = out.rstrip(b"\r\n") if kind == "halt_strip" else out
    return "PASS" if got == expected else "FAIL"


def run_oracle(source: str, stdin: bytes, fuel: int):
    status, steps, out = oracle.run(source, stdin, fuel)
    return status, steps, out


def run_zig(source: str, stdin: bytes, fuel: int):
    with tempfile.NamedTemporaryFile("w", suffix=".mb", delete=False, encoding="latin-1") as fh:
        fh.write(source)
        path = fh.name
    try:
        p = subprocess.run([str(ZIG), "10", "@" + path, stdin.hex(), str(fuel), "0", "0", "0"],
                           capture_output=True, text=True, timeout=3600)
    finally:
        Path(path).unlink()
    line = next((l for l in (p.stderr + p.stdout).splitlines() if l.startswith("RESULT")), None)
    if line is None:
        return "RUNNER_ERROR", 0, (p.stderr + p.stdout)[-300:].encode()
    kv = dict(t.split("=", 1) for t in line.split()[1:])
    hexout = kv.get("out_hex", "")
    status = {"HALTED": "HALTED", "OUT_OF_FUEL": "OUT_OF_FUEL"}.get(kv["status"], kv["status"])
    return status, int(kv.get("steps", 0)), bytes.fromhex("" if hexout == "-" else hexout)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lmao-dir", type=Path, required=True)
    ap.add_argument("--driver", type=Path, required=True)
    args = ap.parse_args()

    lmao = args.lmao_dir / "lmao.exe"
    if sha256(lmao) != PRE["external_oracle"]["lmao_exe_sha256"]:
        print("LMAO_EXE_CHANGED")
        return 2
    for name, digest in PRE["examples_sha256"].items():
        if sha256(args.lmao_dir / name) != digest:
            print(f"EXAMPLE_CHANGED {name}")
            return 2
    for key in ("oracle_python", "zig_runner"):
        if sha256(GIT / PRE["engines"][key]["path"]) != PRE["engines"][key]["sha256"]:
            print(f"ENGINE_CHANGED {key}")
            return 2
    if sha256(GIT / "malbolge-free" / "src" / "hell.zig") != PRE["lmaolite"]["hell_zig_sha256"]:
        print("HELL_ZIG_CHANGED")
        return 2

    t0 = time.time()
    results = {"H1": {}, "H2": {}}
    for hell_file in sorted(PRE["examples_sha256"]):
        name = hell_file[:-5]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / f"{name}.mb"
            subprocess.run([str(lmao), "-o", str(out), str(args.lmao_dir / hell_file)], capture_output=True, text=True)
            lmao_src = out.read_text(encoding="latin-1")
        py_fuel = SIMPLE_CAT_FUEL if name == "example_simple_cat" else PRE["engines"]["oracle_python"]["fuel"]
        zig_fuel = SIMPLE_CAT_FUEL if name == "example_simple_cat" else PRE["engines"]["zig_runner"]["fuel"]

        h1 = []
        for stdin, exp in cases(name):
            zs, zsteps, zout = run_zig(lmao_src, stdin, zig_fuel)
            os_, osteps, oout = run_oracle(lmao_src, stdin, py_fuel)
            h1.append({"stdin": stdin[:24].hex(), "zig": [judge(exp, zs, zout), zs, zsteps],
                       "oracle": [judge(exp, os_, oout), os_, osteps],
                       "engines_agree": (zs, zsteps, zout) == (os_, osteps, oout) or "OUT_OF_FUEL" in (zs, os_)})
            print(f"H1 {name} stdin={stdin[:12]!r} zig={h1[-1]['zig']} oracle={h1[-1]['oracle']} ({time.time() - t0:.0f}s)", flush=True)
        results["H1"][name] = {"lmao_source_cells": len("".join(lmao_src.split())),
                               "lmao_source_sha256": hashlib.sha256(lmao_src.encode("latin-1")).hexdigest(), "cases": h1}

        d = subprocess.run([str(args.driver), str(args.lmao_dir / hell_file)], capture_output=True, text=True)
        text = d.stderr + d.stdout
        stage = next((l.split("=", 1)[1].split()[0] for l in text.splitlines() if l.startswith("STAGE=")), "driver_crash")
        entry = {"stage": stage, "driver_tail": text[-300:] if stage != "ok" else ""}
        if stage == "ok":
            src = next(l[len("SOURCE="):] for l in text.splitlines() if l.startswith("SOURCE="))
            entry["source_cells"] = len(src)
            load_status = oracle.run(src, b"", 1)[0]
            if load_status == "INVALID":
                entry["stage"] = "load"
                entry["load_error"] = oracle.run(src, b"", 1)[2].decode(errors="replace")
            else:
                entry["cases"] = []
                for stdin, exp in cases(name):
                    os_, osteps, oout = run_oracle(src, stdin, py_fuel)
                    entry["cases"].append({"stdin": stdin[:24].hex(), "oracle": [judge(exp, os_, oout), os_, osteps],
                                           "out_head": oout[:32].hex()})
                entry["stage"] = "behaviour"
        results["H2"][name] = entry
        print(f"H2 {name} -> {json.dumps({k: v for k, v in entry.items() if k != 'cases'})[:300]}", flush=True)

    h1_checks = [c[e][0] for p in results["H1"].values() for c in p["cases"] for e in ("zig", "oracle")]
    h1 = "PASS" if h1_checks and all(x == "PASS" for x in h1_checks) else ("FAIL" if "FAIL" in h1_checks else "PARTIAL_NOT_EVALUABLE")
    per = {}
    for name, e in results["H2"].items():
        ok = e["stage"] == "behaviour" and all(c["oracle"][0] == "PASS" for c in e["cases"])
        per[name] = "PASS" if ok else f"FAIL at {e['stage']}"
    h2 = "PARITY_PASS" if all(v == "PASS" for v in per.values()) else "FALSIFIED"
    report = {"preregistration_sha256": sha256(HERE / "PREREGISTRATION.json"), "runtime_seconds": round(time.time() - t0, 1),
              "deviations": [f"example_simple_cat fuel capped at {SIMPLE_CAT_FUEL} for both engines (declared in code before running)", "first run (run_log_first_run_bug.txt) built the cat input with a fresh Random per byte, giving 256 copies of 0x30 instead of 256 random bytes; fixed and rerun, both logs kept"],
              "results": results,
              "verdicts": {"H1_LUTTER_ON_OUR_MACHINERY": h1, "H1_check_counts": {s: h1_checks.count(s) for s in set(h1_checks)},
                           "H2_per_program": per, "H2_LMAOLITE_PARITY": h2,
                           "A5_GATE": "PASS" if h1 == "PASS" and h2 == "PARITY_PASS" else "FAIL"}}
    (HERE / "RESULTS.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["verdicts"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
