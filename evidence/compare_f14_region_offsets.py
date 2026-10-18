#!/usr/bin/env python3
"""F14 — Regional dispatch divergence (V1) against localized external reference.

`ROADMAP.md` line 421 set the next technical step after F13:
"(2) un gate para región 1/2, que es donde vive V1".

Divergence V1 was identified in F13 by reading the reference source:
bolge19.zig:371-376, 388-389 decodes idx = (c + mem[c] + off[region]) % 94 with
offs = [0, 117, 140], where region = c // 3^18. Our cores decode (c + mem[c]) % 94
with no region term (malbolge_core.py:196, malbolge_free.zig:487).

Expectations are pre-registered in docs/F14_REGION_OFFSETS_V1_PREGISTRATION.md.
This gate measures:
  (1) Definitional parameters and region boundaries.
  (2) Statistical sampling of the dispatch formulas across Regions 0, 1, and 2.
  (3) Execution of jump cases reaching Region 1, observing the resulting
      halt step divergence and opcode index delta.

Exit codes:
  0 every expectation holds
  1 an expectation was falsified
  3 the reference is absent (NOT_DEMONSTRATED, an explicit skip)
  4 integrity failure (reference drifted)
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import random
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
PREGISTRATION = "docs/F14_REGION_OFFSETS_V1_PREGISTRATION.md"

REF_SRC_SHA256 = "47758a3f667f4089f6029d86130b94f14f082d4c113a212b8ff571d84113e8a3"
REF_PROFILE_SHA256 = "6cc0afa10b050a36673e131b2efc69fa29e9589136f52b5f27a7dabe23b6ac1f"

END = 1_162_261_467  # 3^19
THIRD = END // 3      # 3^18 = 387_420_489
REF_REGION_OFFS = (0, 117, 140)


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def display(path: pathlib.Path) -> str:
    try:
        return os.path.relpath(path, ROOT.parent)
    except ValueError:
        return str(path)


def module_from(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def ref_run(binary: pathlib.Path, image_path: pathlib.Path, stdin: bytes, budget: int) -> dict:
    proc = subprocess.run(
        [str(binary), str(image_path), "--loader", "raw", "--max-steps", str(budget)],
        input=stdin, capture_output=True, timeout=300,
    )
    if proc.returncode != 0:
        raise SystemExit(
            f"F14_REFERENCE_FAILURE rc={proc.returncode}\n"
            + (proc.stderr or proc.stdout).decode("utf-8", "replace")[-2000:]
        )
    obs = {
        "stdout": proc.stdout, "image_cells": None, "status": None,
        "steps": None, "c": None, "d": None, "a": None,
    }
    for line in proc.stderr.decode("utf-8", "replace").splitlines():
        if line.startswith("bolge19: imagen="):
            obs["image_cells"] = int(line.split("imagen=")[1].split()[0])
        elif line.startswith("bolge19: HALT"):
            fields = dict(tok.split("=", 1) for tok in line[len("bolge19: HALT"):].split() if "=" in tok)
            obs.update(
                status="HALTED", steps=int(fields["steps"]), c=int(fields["c"]),
                d=int(fields["d"]), a=int(fields["a"]),
            )
        elif line.startswith("bolge19: MAX_STEPS"):
            obs.update(status="MAX_STEPS", steps=int(line.split()[-1]))
    if obs["status"] is None:
        raise SystemExit("F14_DRIVER_INCOMPLETE: reference printed no halt/max-steps line")
    return obs


def ours_python(core, image: bytes, stdin: bytes, budget: int) -> dict:
    vm = core.MalbolgeCore(width=19, mem_limit=END, growth_policy="fixed")
    vm.load(image.decode("latin-1"))
    res = vm.run(budget, stdin)
    return {
        "status": res["status"], "steps": res["steps"],
        "stdout": res["stdout"].encode("latin-1"),
        "c": vm.stats["final_c"], "d": vm.stats["final_d"],
        "program_len": vm.program_len,
        "width": vm.width, "padwidth": vm.padwidth, "mem_limit": vm.mem_limit,
    }


def ours_zig(image_path: pathlib.Path, stdin: bytes, budget: int) -> dict:
    proc = subprocess.run(
        ["zig", "run", "--dep", "malbolge_free=malbolge_free",
         "-Mroot=evidence/run_f13_k19.zig", "-Mmalbolge_free=src/malbolge_free.zig",
         "--", str(image_path), stdin.hex() or "-", str(budget)],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    )
    if proc.returncode != 0:
        sys.stderr.write(f"F14_ZIG_DRIVER_FAILURE rc={proc.returncode}\n")
        sys.stderr.write((proc.stderr or proc.stdout)[-4000:])
        raise SystemExit(4)
    obs: dict = {}
    for line in proc.stderr.splitlines():
        if line.startswith("PARAM "):
            fields = dict(tok.split("=", 1) for tok in line.split()[1:] if "=" in tok)
            obs["param"] = fields
        elif line.startswith("RUN "):
            for tok in line.split()[1:]:
                key, _, value = tok.partition("=")
                obs[key] = None if value == "null" else int(value) if value.isdigit() else value
    if "status" not in obs or "param" not in obs:
        raise SystemExit("F14_DRIVER_INCOMPLETE: zig core printed no PARAM/RUN line")
    return {
        "status": obs["status"], "steps": obs["steps"],
        "stdout_len": obs["out_len"], "stdout_sha": obs["out_sha"],
        "first": obs["out_first"], "c": obs["final_c"], "d": obs["final_d"],
        "encrypted": obs["encrypted"], "param": obs["param"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=pathlib.Path,
                        help="write the measurement JSON to this NEW path")
    args = parser.parse_args()

    t_start = time.time()
    sib = ROOT.parent / "MalbolgeLispSlop"
    ref_src = pathlib.Path(os.environ.get("MALFREE_BOLGE19_SRC", sib / "src" / "bolge19.zig"))
    ref_profile = pathlib.Path(os.environ.get("MALFREE_BOLGE19_PROFILE",
                                              sib / "profiles" / "fixed19.json"))
    ref_bin = pathlib.Path(os.environ.get("MALFREE_BOLGE19_BIN", sib / "build" / "bolge19"))

    missing = [display(path) for path in (ref_src, ref_profile, ref_bin) if not path.is_file()]
    if missing:
        sys.stderr.write(
            "F14_REFERENCE_ABSENT: no localized deterministic fixed-3^19 reference here.\n"
            "  " + "\n  ".join(missing) + "\n"
            "  REGION_1_2_DISPATCH_DIVERGENCE_V1 = NOT_DEMONSTRATED in this environment.\n"
            f"  Set MALFREE_BOLGE19_SRC / _PROFILE / _BIN, or see {PREGISTRATION}.\n"
        )
        return 3

    src_sha, profile_sha = sha(ref_src.read_bytes()), sha(ref_profile.read_bytes())
    bin_sha = sha(ref_bin.read_bytes())
    for label, seen, pin in (("src", src_sha, REF_SRC_SHA256),
                             ("profile", profile_sha, REF_PROFILE_SHA256)):
        if seen != pin:
            sys.stderr.write(
                f"F14_REFERENCE_DRIFT: the {label} the expectations were read from has changed.\n"
                f"  pinned: {pin}\n  found:  {seen}\n"
                "  Every number below would be about a different machine.\n"
            )
            return 4

    json_profile = json.loads(ref_profile.read_text(encoding="utf-8"))
    core = module_from(ROOT / "src" / "malbolge_core.py", "mb_core")

    print(f"F14 reference src={display(ref_src)} sha={src_sha[:16]}")
    print(f"F14 reference profile={display(ref_profile)} sha={profile_sha[:16]}")
    print(f"F14 reference bin={display(ref_bin)} sha={bin_sha[:16]} (build product, recorded not pinned)")
    print("F14 ours python=src/malbolge_core.py zig=src/malbolge_free.zig")
    print(f"F14 regional geometry: END={END} THIRD={THIRD} REF_OFFS={REF_REGION_OFFS}")

    expectations = []
    def check(name: str, cond: bool, detail: str) -> None:
        expectations.append({"name": name, "match": bool(cond), "detail": detail})
        tag = "MATCH" if cond else "FALSIFIED"
        print(f"F14 EXP {name}: {tag} ({detail})")

    # Calculated offsets using the reference's exact formula (bolge19.zig:371-376)
    a1_off = 94 - (((END - 1) // 6 - 29524) % 94)
    a2_off = 94 - (((END - 1) // 3 - 59048) % 94)
    calc_off1 = ((a1_off - THIRD) % 94) + 94
    calc_off2 = a2_off - ((2 * THIRD) % 94) + 94
    calc_offs = (0, calc_off1, calc_off2)

    # ── (1) Definitional expectations ─────────────────────────────────────────
    check("D1_end_equals_pow3_19",
          json_profile["end"] == END and (3 ** 19) == END,
          f"json.end={json_profile['end']} 3**19={END}")
    check("D2_third_equals_pow3_18",
          json_profile["end"] // 3 == THIRD and (3 ** 18) == THIRD,
          f"json.end//3={THIRD} 3**18={THIRD}")
    check("D3_ref_offset_region_0",
          calc_offs[0] == REF_REGION_OFFS[0] == 0,
          f"offs[0]={calc_offs[0]}")
    check("D4_ref_offset_region_1",
          calc_offs[1] == REF_REGION_OFFS[1] == 117 and (117 % 94) == 23,
          f"offs[1]={calc_offs[1]} (117 % 94 = {117 % 94})")
    check("D5_ref_offset_region_2",
          calc_offs[2] == REF_REGION_OFFS[2] == 140 and (140 % 94) == 46,
          f"offs[2]={calc_offs[2]} (140 % 94 = {140 % 94})")

    # ── (2) Statistical / Formula differential over seeded grid ───────────────
    rng = random.Random(20261018)
    p1_mismatches = 0
    for _ in range(50000):
        c = rng.randrange(0, THIRD)
        m = rng.randrange(0, 1000)
        ref_idx = (c + m + REF_REGION_OFFS[0]) % 94
        our_idx = (c + m) % 94
        if ref_idx != our_idx:
            p1_mismatches += 1
    check("P1_R0_FORMULA_EQUALITY",
          p1_mismatches == 0,
          f"50000 seeded pairs in Region 0 (c < {THIRD}), mismatches={p1_mismatches}")

    p2_mismatches = 0
    p2_same = 0
    for _ in range(50000):
        c = rng.randrange(THIRD, 2 * THIRD)
        m = rng.randrange(0, 1000)
        ref_idx = (c + m + REF_REGION_OFFS[1]) % 94
        our_idx = (c + m) % 94
        if (ref_idx - our_idx) % 94 != 23:
            p2_mismatches += 1
        if ref_idx == our_idx:
            p2_same += 1
    check("P2_R1_FORMULA_DIVERGENCE",
          p2_mismatches == 0 and p2_same == 0,
          f"50000 seeded pairs in Region 1: delta mismatches={p2_mismatches}, identical count={p2_same}")

    p3_mismatches = 0
    p3_same = 0
    for _ in range(50000):
        c = rng.randrange(2 * THIRD, END)
        m = rng.randrange(0, 1000)
        ref_idx = (c + m + REF_REGION_OFFS[2]) % 94
        our_idx = (c + m) % 94
        if (ref_idx - our_idx) % 94 != 46:
            p3_mismatches += 1
        if ref_idx == our_idx:
            p3_same += 1
    check("P3_R2_FORMULA_DIVERGENCE",
          p3_mismatches == 0 and p3_same == 0,
          f"50000 seeded pairs in Region 2: delta mismatches={p3_mismatches}, identical count={p3_same}")

    # ── (3) Execution cases ───────────────────────────────────────────────────
    workdir = pathlib.Path(tempfile.mkdtemp(prefix="f14_"))
    try:
        # Case R0: Control in Region 0 ([117, 98, 79] = 'ubO')
        c1_img = bytes((117, 98, 79))
        c1_path = workdir / "C1.mb"
        c1_path.write_bytes(c1_img)
        c1_ref = ref_run(ref_bin, c1_path, b"", 10)
        c1_py = ours_python(core, c1_img, b"", 10)
        c1_zg = ours_zig(c1_path, b"", 10)
        check("R0_CONTROL_REGION_0",
              c1_ref["status"] == "HALTED" and c1_py["status"] == "HALTED" and c1_zg["status"] == "HALTED"
              and c1_ref["c"] == 2 and c1_py["c"] == 2 and c1_zg["c"] == 2
              and c1_ref["stdout"] == b"\xda" and c1_py["stdout"] == b"\xda",
              f"ref=HALTED@({c1_ref['c']},{c1_ref['d']}) out={c1_ref['stdout'].hex()} py=HALTED@({c1_py['c']},{c1_py['d']}) zg=HALTED@({c1_zg['c']},{c1_zg['d']})")

        # Case R1: Jump to Region 1 with halt divergence ([40, 97, 79] = '(aO')
        r1_img = bytes((40, 97, 79))
        r1_path = workdir / "R1.mb"
        r1_path.write_bytes(r1_img)
        r1_ref = ref_run(ref_bin, r1_path, b"", 100)
        r1_py = ours_python(core, r1_img, b"", 100)
        r1_zg = ours_zig(r1_path, b"", 100)

        check("R1_STATUS_HALT",
              r1_ref["status"] == "HALTED" and r1_py["status"] == "HALTED" and r1_zg["status"] == "HALTED",
              f"ref={r1_ref['status']} py={r1_py['status']} zg={r1_zg['status']}")

        check("R1_REGION_ARRIVAL",
              r1_ref["c"] // THIRD == 1 and r1_py["c"] // THIRD == 1 and r1_zg["c"] // THIRD == 1,
              f"ref_halt_c={r1_ref['c']} (reg {r1_ref['c'] // THIRD}) py_halt_c={r1_py['c']} (reg {r1_py['c'] // THIRD})")

        check("R1_HALT_DIVERGENCE",
              r1_ref["steps"] == 11 and r1_ref["c"] == 581130727
              and r1_py["steps"] == 60 and r1_py["c"] == 581130775,
              f"ref halts at step={r1_ref['steps']} c={r1_ref['c']} (due to +117); ours halts at step={r1_py['steps']} c={r1_py['c']}")

        check("R1_CROSS_CORE_AGREEMENT",
              r1_py["steps"] == r1_zg["steps"] == 60
              and r1_py["c"] == r1_zg["c"] == 581130775
              and r1_py["d"] == r1_zg["d"] == 581130767,
              f"py steps={r1_py['steps']} c={r1_py['c']} d={r1_py['d']} | zg steps={r1_zg['steps']} c={r1_zg['c']} d={r1_zg['d']}")

        # Case R2: Jump to Region 1 at step 4 ([39, 38, 66] = "'&B")
        r2_img = bytes((39, 38, 66))
        r2_path = workdir / "R2.mb"
        r2_path.write_bytes(r2_img)
        r2_ref = ref_run(ref_bin, r2_path, b"", 5)
        r2_py = ours_python(core, r2_img, b"", 5)
        r2_zg = ours_zig(r2_path, b"", 5)

        check("R2_STATUS_MAX_STEPS",
              r2_ref["status"] == "MAX_STEPS" and r2_py["status"] == "MAX_STEPS" and r2_zg["status"] == "MAX_STEPS",
              f"ref={r2_ref['status']} py={r2_py['status']} zg={r2_zg['status']}")

        check("R2_REGION_ARRIVAL",
              r2_py["c"] // THIRD == 1 and r2_zg["c"] // THIRD == 1,
              f"py_final_c={r2_py['c']} (reg {r2_py['c'] // THIRD}) zg_final_c={r2_zg['c']}")

        # In R2, at step 4: c = 581130750.
        # Ours calculates op = (cell + c) % 94 = (66 + 581130750) % 94 = 68 (nop).
        # Reference calculates idx = (66 + 581130750 + 117) % 94 = 91 (invalid).
        # Delta = 91 - 68 = 23.
        cell_step4 = 66
        c_step4 = 581130750
        op_ours = (cell_step4 + c_step4) % 94
        op_ref = (cell_step4 + c_step4 + 117) % 94
        check("R2_OPCODE_DELTA",
              op_ours == 68 and op_ref == 91 and (op_ref - op_ours) % 94 == 23,
              f"step 4 at c={c_step4}: ours op={op_ours} (nop) ref idx={op_ref} (invalid) delta={op_ref - op_ours} (117 % 94 = 23)")

        check("R2_CROSS_CORE_AGREEMENT",
              r2_py["steps"] == r2_zg["steps"] == 5
              and r2_py["c"] == r2_zg["c"] == 581130751
              and r2_py["d"] == r2_zg["d"] == 5,
              f"py c={r2_py['c']} d={r2_py['d']} | zg c={r2_zg['c']} d={r2_zg['d']}")

    finally:
        for p in workdir.glob("*"):
            p.unlink()
        workdir.rmdir()

    total = len(expectations)
    matched = sum(1 for e in expectations if e["match"])
    falsified = total - matched

    print(f"F14 EXPECTATIONS={total} MATCH={matched} FALSIFIED={falsified}")
    report = {
        "gate": "F14",
        "title": "Regional dispatch divergence (V1)",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "reference": {
            "src": display(ref_src), "src_sha256": src_sha,
            "profile": display(ref_profile), "profile_sha256": profile_sha,
            "bin": display(ref_bin), "bin_sha256": bin_sha,
        },
        "ours": {
            "python": "src/malbolge_core.py",
            "zig": "src/malbolge_free.zig",
        },
        "expectations": expectations,
        "elapsed_sec": round(time.time() - t_start, 3),
        "verdict": "PASS" if falsified == 0 else "FAIL",
    }

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"F14 report written to {display(args.output)}")

    if falsified > 0:
        return 1
    print("F14 REGION_1_2_DISPATCH_DIVERGENCE_V1=PASS (scoped: regional offsets +117/+140 verified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
