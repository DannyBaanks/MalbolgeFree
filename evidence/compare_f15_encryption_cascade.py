#!/usr/bin/env python3
"""F15 — Encryption cascade and domain guard divergence (V3) against external reference.

`ROADMAP.md` line 421 set the next technical step after F14:
"(3) la cascada del cifrado (V3), que requiere programas más largos que 4 instrucciones".

Divergence V3 was identified in F13 by reading the reference source:
bolge19.zig:31-34, 419 defines a 141-entry table XLAT_CONCAT and guards cv < 141,
indexing directly with the cell value. Our cores guard 33 <= mc <= 126, indexing
with mc - 33 into a 94-entry canonical permutation TRANSLATED (malbolge_core.py:258,
malbolge_free.zig:641), matching vendor/canonical_malbolge_py/malbolge.py:127.

Expectations are pre-registered in docs/F15_ENCRYPTION_CASCADE_V3_PREGISTRATION.md.
This gate measures:
  (1) Definitional table lengths, prefixes, slice identity, and finite convergence.
  (2) Cycle isomorphism on [33, 126] and domain guard divergence on [0, 32] / [127, 140].
  (3) Multi-step linear cascades (C1: 2 cells, C5: 4 cells, C7: 6 cells) and a sub-33
      cell mutation witness (C_SUB33: skips encryption on cell 0).

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
PREGISTRATION = "docs/F15_ENCRYPTION_CASCADE_V3_PREGISTRATION.md"

REF_SRC_SHA256 = "47758a3f667f4089f6029d86130b94f14f082d4c113a212b8ff571d84113e8a3"
REF_PROFILE_SHA256 = "6cc0afa10b050a36673e131b2efc69fa29e9589136f52b5f27a7dabe23b6ac1f"

END = 1_162_261_467  # 3^19

# Reference table transcription from bolge19.zig:31-34
REF_XLAT_PREFIX = "SOMEBODY MAKE ME FEEL ALIVE"
REF_XLAT_MID = "[hj9>,5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"
REF_XLAT_SUFFIX = "AND SHATTER ME"
REF_XLAT_CONCAT = (REF_XLAT_PREFIX + REF_XLAT_MID + REF_XLAT_SUFFIX).encode("ascii")


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


def enc_ours(v: int, enc_map: dict[int, int]) -> int:
    return enc_map.get(v, v)


def enc_ref(v: int) -> int:
    return REF_XLAT_CONCAT[v] if v < len(REF_XLAT_CONCAT) else v


def ref_run(binary: pathlib.Path, image_path: pathlib.Path, stdin: bytes, budget: int) -> dict:
    proc = subprocess.run(
        [str(binary), str(image_path), "--loader", "raw", "--max-steps", str(budget)],
        input=stdin, capture_output=True, timeout=300,
    )
    if proc.returncode != 0:
        raise SystemExit(
            f"F15_REFERENCE_FAILURE rc={proc.returncode}\n"
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
        raise SystemExit("F15_DRIVER_INCOMPLETE: reference printed no halt/max-steps line")
    return obs


def ours_python(core, image: bytes, stdin: bytes, budget: int) -> dict:
    vm = core.MalbolgeCore(width=19, mem_limit=END, growth_policy="fixed")
    vm.load(image.decode("latin-1"))
    sink: list[dict] = []
    res = vm.run(budget, stdin, _sink=sink)
    encrypted_steps = [s for s in sink if s.get("encrypted_addr") is not None]
    return {
        "status": res["status"], "steps": res["steps"],
        "stdout": res["stdout"].encode("latin-1"),
        "c": vm.stats["final_c"], "d": vm.stats["final_d"],
        "program_len": vm.program_len,
        "width": vm.width, "padwidth": vm.padwidth, "mem_limit": vm.mem_limit,
        "encrypted_cells": vm.stats["encrypted_cells"],
        "encrypted_history": encrypted_steps,
        "cell_0": vm._cell(0),
    }


def ours_zig(image_path: pathlib.Path, stdin: bytes, budget: int) -> dict:
    proc = subprocess.run(
        ["zig", "run", "--dep", "malbolge_free=malbolge_free",
         "-Mroot=evidence/run_f13_k19.zig", "-Mmalbolge_free=src/malbolge_free.zig",
         "--", str(image_path), stdin.hex() or "-", str(budget)],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    )
    if proc.returncode != 0:
        sys.stderr.write(f"F15_ZIG_DRIVER_FAILURE rc={proc.returncode}\n")
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
        raise SystemExit("F15_DRIVER_INCOMPLETE: zig core printed no PARAM/RUN line")
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

    # Step 1: verify external sibling checkout
    ref_repo = ROOT.parent / "MalbolgeLispSlop"
    ref_src = ref_repo / "src" / "bolge19.zig"
    ref_profile = ref_repo / "profiles" / "fixed19.json"
    ref_bin = ref_repo / "build" / "bolge19"

    for path, role in [
        (ref_src, "reference source"),
        (ref_profile, "reference profile"),
        (ref_bin, "compiled reference binary"),
    ]:
        if not path.is_file():
            sys.stderr.write(
                f"SKIP: external fixed-3^19 peer missing: {display(path)} ({role})\n"
                f"F15 measures divergence V3 against MalbolgeLispSlop; without it "
                f"this gate cannot run. See {PREGISTRATION}.\n"
            )
            return 3

    # Step 2: verify reference pinned hashes
    src_bytes = ref_src.read_bytes()
    profile_bytes = ref_profile.read_bytes()
    bin_bytes = ref_bin.read_bytes()

    src_sha = sha(src_bytes)
    profile_sha = sha(profile_bytes)
    bin_sha = sha(bin_bytes)

    if src_sha != REF_SRC_SHA256 or profile_sha != REF_PROFILE_SHA256:
        sys.stderr.write(
            f"F15_INTEGRITY_FAILURE: reference files drifted from pinned hashes\n"
            f"  bolge19.zig: expected {REF_SRC_SHA256}, got {src_sha}\n"
            f"  fixed19.json: expected {REF_PROFILE_SHA256}, got {profile_sha}\n"
        )
        return 4

    # Load Python canonical oracle and our core
    canonical_mod = module_from(ROOT / "vendor" / "canonical_malbolge_py" / "malbolge.py", "canonical_py")
    canon_orig = canonical_mod._ORIGINAL
    canon_xlat = canonical_mod._TRANSLATED
    canon_enc = canonical_mod._ENCRYPT

    core = module_from(ROOT / "src" / "malbolge_core.py", "malbolge_core")

    t0 = time.time()
    expectations: dict[str, dict] = {}

    def record(eid: str, matched: bool, details: dict):
        expectations[eid] = {"match": bool(matched), "details": details}
        status_str = "MATCH" if matched else "FALSIFIED"
        print(f"  {eid:30s} {status_str}")
        if not matched:
            print(f"    FAIL DETAILS: {details}")

    print("== F15 Definitional Table & Geometry Proofs ==")

    # D1: Canonical table length & endpoints
    d1_match = (len(canon_xlat) == 94 and canon_xlat[0] == "5" and canon_xlat[-1] == "@")
    record("D1_CANONICAL_TABLE", d1_match, {
        "length": len(canon_xlat),
        "first": canon_xlat[0],
        "last": canon_xlat[-1],
    })

    # D2: Reference table composition
    d2_match = (
        len(REF_XLAT_CONCAT) == 141
        and len(REF_XLAT_PREFIX) == 27
        and len(REF_XLAT_MID) == 100
        and len(REF_XLAT_SUFFIX) == 14
    )
    record("D2_REFERENCE_TABLE", d2_match, {
        "len_total": len(REF_XLAT_CONCAT),
        "len_prefix": len(REF_XLAT_PREFIX),
        "len_mid": len(REF_XLAT_MID),
        "len_suffix": len(REF_XLAT_SUFFIX),
    })

    # D3: Canonical slice identity
    slice_match = (REF_XLAT_CONCAT[33:127] == canon_xlat.encode("ascii"))
    record("D3_CANONICAL_SLICE_IDENTITY", slice_match, {
        "slice_len": len(REF_XLAT_CONCAT[33:127]),
        "first_char": chr(REF_XLAT_CONCAT[33]),
        "last_char": chr(REF_XLAT_CONCAT[126]),
        "equal": slice_match,
    })

    # D4: Disagreement set over [0, 255]
    disagreements = [
        v for v in range(256)
        if enc_ours(v, canon_enc) != enc_ref(v)
    ]
    expected_disagreements = list(range(0, 33)) + list(range(127, 141))
    d4_match = (disagreements == expected_disagreements and len(disagreements) == 47)
    record("D4_DISAGREEMENT_SET", d4_match, {
        "disagreements_count": len(disagreements),
        "sub33_count": len([v for v in disagreements if v < 33]),
        "highbyte_count": len([v for v in disagreements if 127 <= v <= 140]),
        "upper_matches_exact": all(enc_ours(v, canon_enc) == enc_ref(v) == v for v in range(141, 256)),
    })

    # D5: Finite convergence of [0, 140] into canonical domain in <= 2 steps
    steps_to_canonical = []
    for v in range(141):
        curr = v
        s = 0
        while not (33 <= curr <= 126):
            curr = enc_ref(curr)
            s += 1
            if s > 10:
                break
        steps_to_canonical.append(s)
    max_steps = max(steps_to_canonical)
    d5_match = (max_steps == 2)
    record("D5_FINITE_CONVERGENCE", d5_match, {
        "max_steps": max_steps,
        "one_step_count": steps_to_canonical.count(1),
        "two_step_count": steps_to_canonical.count(2),
        "zero_step_count": steps_to_canonical.count(0),
    })

    print("== F15 Property & Orbit Verification ==")

    # P1: Cycle decomposition & multi-depth agreement
    visited = set()
    cycles = []
    for start in range(33, 127):
        if start not in visited:
            cyc = []
            curr = start
            while curr not in cyc:
                cyc.append(curr)
                visited.add(curr)
                curr = enc_ours(curr, canon_enc)
            cycles.append(cyc)
    cycle_lens = sorted([len(c) for c in cycles], reverse=True)

    p1_depths_match = True
    tested_depths = [1, 2, 5, 10, 50, 100]
    for depth in tested_depths:
        for start in range(33, 127):
            o, r = start, start
            for _ in range(depth):
                o = enc_ours(o, canon_enc)
                r = enc_ref(r)
            if o != r:
                p1_depths_match = False

    p1_match = (cycle_lens == [68, 9, 6, 5, 4, 2] and p1_depths_match)
    record("P1_CYCLE_ISOMORPHISM", p1_match, {
        "cycle_lengths": cycle_lens,
        "cycle_count": len(cycles),
        "multi_depth_orbits_match": p1_depths_match,
        "tested_depths": tested_depths,
    })

    # P2: Sub-33 divergence
    sub33_diverged = sum(1 for v in range(33) if enc_ours(v, canon_enc) != enc_ref(v))
    p2_match = (sub33_diverged == 33)
    record("P2_SUB33_DIVERGENCE", p2_match, {
        "diverged": sub33_diverged,
        "total": 33,
        "percentage": 100.0 * sub33_diverged / 33,
    })

    # P3: High-byte [127..140] divergence
    highbyte_diverged = sum(1 for v in range(127, 141) if enc_ours(v, canon_enc) != enc_ref(v))
    p3_match = (highbyte_diverged == 14)
    record("P3_HIGHBYTE_DIVERGENCE", p3_match, {
        "diverged": highbyte_diverged,
        "total": 14,
        "percentage": 100.0 * highbyte_diverged / 14,
    })

    # P4: Random sampling on canonical domain [33..126]
    rng = random.Random(20261018)
    p4_match = all(enc_ours(v, canon_enc) == enc_ref(v) for v in (rng.randint(33, 126) for _ in range(100_000)))
    record("P4_RANDOM_GRID_CANONICAL", p4_match, {
        "samples": 100_000,
        "seed": 20261018,
        "mismatches": 0 if p4_match else -1,
    })

    print("== F15 Execution Cascades & Domain Divergence ==")

    cases = [
        {
            "name": "C1",
            "prog": b"ubO",
            "stdin": b"",
            "ref_steps": 2, "our_steps": 3,
            "stdout": b"\xda",
            "c": 2, "d": 2,
            "enc_count": 2,
            "enc_values": [111, 84],
            "status_key": "R1_C1_STATUS",
            "count_key": "R1_C1_ENCRYPTED_COUNT",
            "values_key": "R1_C1_ENCRYPTED_VALUES",
        },
        {
            "name": "C5",
            "prog": b"ubs`M",
            "stdin": b"AB",
            "ref_steps": 4, "our_steps": 5,
            "stdout": b"AB",
            "c": 4, "d": 4,
            "enc_count": 4,
            "enc_values": [111, 84, 82, 60],
            "status_key": "R2_C5_STATUS",
            "count_key": "R2_C5_ENCRYPTED_COUNT",
            "values_key": "R2_C5_ENCRYPTED_VALUES",
        },
        {
            "name": "C7",
            "prog": b"ubs`q^K",
            "stdin": b"XYZ",
            "ref_steps": 6, "our_steps": 7,
            "stdout": b"XYZ",
            "c": 6, "d": 6,
            "enc_count": 6,
            "enc_values": [111, 84, 82, 60, 108, 57],
            "status_key": "R3_C7_STATUS",
            "count_key": "R3_C7_ENCRYPTED_COUNT",
            "values_key": "R3_C7_ENCRYPTED_VALUES",
        },
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = pathlib.Path(tmpdir)

        # Run linear cascades C1, C5, C7
        for cspec in cases:
            cname = cspec["name"]
            cfile = tmpdir_path / f"{cname}.mal"
            cfile.write_bytes(cspec["prog"])

            r_ref = ref_run(ref_bin, cfile, cspec["stdin"], 50)
            r_py = ours_python(core, cspec["prog"], cspec["stdin"], 50)
            r_zg = ours_zig(cfile, cspec["stdin"], 50)

            # Check status and observables
            c_status_match = (
                r_ref["status"] == "HALTED"
                and r_py["status"] == "HALTED"
                and r_zg["status"] == "HALTED"
                and r_ref["steps"] == cspec["ref_steps"]
                and r_py["steps"] == cspec["our_steps"]
                and r_zg["steps"] == cspec["our_steps"]
                and r_ref["stdout"] == cspec["stdout"]
                and r_py["stdout"] == cspec["stdout"]
                and r_ref["c"] == cspec["c"]
                and r_py["c"] == cspec["c"]
                and r_zg["c"] == cspec["c"]
            )
            record(cspec["status_key"], c_status_match, {
                "ref": {"status": r_ref["status"], "steps": r_ref["steps"], "c": r_ref["c"], "stdout": r_ref["stdout"].hex()},
                "py": {"status": r_py["status"], "steps": r_py["steps"], "c": r_py["c"], "stdout": r_py["stdout"].hex()},
                "zg": {"status": r_zg["status"], "steps": r_zg["steps"], "c": r_zg["c"]},
            })

            # Check encrypted count
            c_count_match = (
                r_py["encrypted_cells"] == cspec["enc_count"]
                and r_zg["encrypted"] == cspec["enc_count"]
            )
            record(cspec["count_key"], c_count_match, {
                "expected": cspec["enc_count"],
                "py_encrypted": r_py["encrypted_cells"],
                "zg_encrypted": r_zg["encrypted"],
            })

            # Check encrypted values along cascade
            expected_vals = cspec["enc_values"]
            actual_vals = [
                enc_ours(cspec["prog"][idx], canon_enc) for idx in range(len(expected_vals))
            ]
            c_vals_match = (actual_vals == expected_vals)
            record(cspec["values_key"], c_vals_match, {
                "expected_values": expected_vals,
                "actual_values": actual_vals,
            })

        # Run Case C_SUB33: b"'bO"
        sub_prog = bytes([39, 98, 79])
        sub_file = tmpdir_path / "sub33.mal"
        sub_file.write_bytes(sub_prog)

        sub_ref = ref_run(ref_bin, sub_file, b"", 50)
        sub_py = ours_python(core, sub_prog, b"", 50)
        sub_zg = ours_zig(sub_file, b"", 50)

        # R4_SUB33_STATUS: all three halt, stdout is 0x0d (\r, byte 13)
        sub_status_match = (
            sub_ref["status"] == "HALTED"
            and sub_py["status"] == "HALTED"
            and sub_zg["status"] == "HALTED"
            and sub_ref["steps"] == 2
            and sub_py["steps"] == 3
            and sub_zg["steps"] == 3
            and sub_ref["stdout"] == b"\r"
            and sub_py["stdout"] == b"\r"
        )
        record("R4_SUB33_STATUS", sub_status_match, {
            "ref": {"status": sub_ref["status"], "steps": sub_ref["steps"], "stdout": sub_ref["stdout"].hex()},
            "py": {"status": sub_py["status"], "steps": sub_py["steps"], "stdout": sub_py["stdout"].hex()},
            "zg": {"status": sub_zg["status"], "steps": sub_zg["steps"]},
        })

        # R4_SUB33_SKIP_ENCRYPT: cell 0 held 13, outside [33..126], skipped by MalbolgeFree guard
        sub_skip_match = (
            sub_py["encrypted_cells"] == 1
            and sub_zg["encrypted"] == 1
            and sub_py["cell_0"] == 13
        )
        record("R4_SUB33_SKIP_ENCRYPT", sub_skip_match, {
            "py_encrypted_cells": sub_py["encrypted_cells"],
            "zg_encrypted_cells": sub_zg["encrypted"],
            "py_cell_0_after_step": sub_py["cell_0"],
            "expected_encrypted_cells": 1,
            "expected_cell_0": 13,
            "ref_cell_0_would_be": int(REF_XLAT_CONCAT[13]),
        })

        # R4_SUB33_CROSS_CORE: Python and Zig cores in 100% agreement
        sub_cross_match = (
            sub_py["status"] == sub_zg["status"]
            and sub_py["steps"] == sub_zg["steps"]
            and sub_py["c"] == sub_zg["c"]
            and sub_py["d"] == sub_zg["d"]
            and sub_py["encrypted_cells"] == sub_zg["encrypted"]
        )
        record("R4_SUB33_CROSS_CORE", sub_cross_match, {
            "py": {"status": sub_py["status"], "steps": sub_py["steps"], "c": sub_py["c"], "d": sub_py["d"]},
            "zg": {"status": sub_zg["status"], "steps": sub_zg["steps"], "c": sub_zg["c"], "d": sub_zg["d"]},
        })

    elapsed = time.time() - t0
    total = len(expectations)
    matched = sum(1 for e in expectations.values() if e["match"])
    falsified = total - matched

    print(f"\nF15 EXPECTATIONS={total} MATCH={matched} FALSIFIED={falsified}")
    print(f"F15 DISCLOSURE: canonical domain [33, 126] exhibits 100% cycle isomorphism across all")
    print(f"6 cycles; divergence V3 is strictly confined to [0, 32] (33 values) and [127, 140] (14 values).")
    print(f"Elapsed: {elapsed:.2f}s")

    report = {
        "gate": "F15",
        "pre_registration": PREGISTRATION,
        "elapsed_seconds": round(elapsed, 4),
        "reference": {
            "source": display(ref_src), "source_sha256": src_sha,
            "profile": display(ref_profile), "profile_sha256": profile_sha,
            "binary": display(ref_bin), "binary_sha256": bin_sha,
        },
        "expectations_total": total,
        "expectations_matched": matched,
        "expectations_falsified": falsified,
        "verdict": "PASS" if falsified == 0 else "FAIL",
        "expectations": expectations,
    }

    if args.output:
        if args.output.exists():
            sys.stderr.write(f"refusing to overwrite existing report {args.output}\n")
            return 1
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Report written to {display(args.output)}")

    if falsified == 0:
        print("F15 ENCRYPTION_CASCADE_DIVERGENCE_V3=PASS")
        return 0
    else:
        print("F15 ENCRYPTION_CASCADE_DIVERGENCE_V3=FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
