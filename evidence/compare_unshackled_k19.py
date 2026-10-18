#!/usr/bin/env python3
"""F13 — deterministic fixed-3^19 parity against a localized external reference.

`UNSHACKLED_PARITY` was carried as NOT_DEMONSTRABLE because the only reference in
this evidence chain, `MALDOOM/vendor/Unshackled.c`, calls `srand(time(NULL))`
(line 585): a nondeterministic peer falsifies nothing. That label conflated two
different claims. The unreachable one is parity with that original program. The
reachable one is parity with a *deterministic fixed-3^19 machine*, and such a
machine now exists as a third-party artifact we did not write:
`MalbolgeLispSlop/src/bolge19.zig`, whose own profile file
`MalbolgeLispSlop/profiles/fixed19.json` states the parameters our
`initUnshackledK19` constructor claims.

Expectations are pre-registered in `docs/F13_UNSHACKLED_K19_PREGISTRATION.md`,
written before the reference was executed on cases C2-C4. Read that file first;
this script only implements it. The scope is region 0 (`c < 3^18`) forward-walk
programs of at most four instructions, and the gate reports four divergences
(V1-V5 in that document) as findings — including one divergence, V2/`rot`, that
is asserted to *occur*. A predicted divergence that does not appear is a
falsification here, not a pass.

No byte of the reference is copied into this repository. Vendoring `bolge19.zig`
is a licensing decision (its own notices say "copy-and-revalidate, never
import"), so the gate reads the sibling checkout, records the hashes it saw, and
exits 3 when the reference is absent — which is what CI shows until a vendor
decision is made.

Exit codes: 0 every expectation holds · 1 an expectation was falsified ·
3 the reference is absent (NOT_DEMONSTRATED, an explicit skip) · 4 integrity or
driver failure (a pinned reference byte drifted, or a core could not run).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import random
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
PREGISTRATION = "docs/F13_UNSHACKLED_K19_PREGISTRATION.md"

# The two reference inputs whose bytes the expectations were read from. Drift in
# either is an integrity failure: every number below would be about a different
# machine. The built binary is NOT pinned — it is a build product of the pinned
# source, its hash is recorded in the report, and its behaviour is exactly what
# the runtime layer tests.
REF_SRC_SHA256 = "47758a3f667f4089f6029d86130b94f14f082d4c113a212b8ff571d84113e8a3"
REF_PROFILE_SHA256 = "6cc0afa10b050a36673e131b2efc69fa29e9589136f52b5f27a7dabe23b6ac1f"

BUDGET = 100
END = 1_162_261_467  # 3^19
THIRD = END // 3  # 3^18
EOF_VALUE = END - 1

# Region offsets transcribed from bolge19.zig:371-376 (offs = [0, 117, 140]).
REF_REGION_OFFS = (0, 117, 140)

# Cases: image bytes, stdin bytes, and the pre-registered prediction per machine.
# Opcode alignment is (cell + position) % 94 == op, so each image below decodes
# as the walk named in `walk`. Predicted stdout bytes are decimal.
CASES = [
    {
        "name": "C1", "image": bytes((117, 98, 79)), "stdin": b"", "walk": "in out halt",
        "ours_out": [218], "ref_out": [218], "ours_steps": 3, "ref_steps": 2, "halt": (2, 2),
    },
    {
        "name": "C2", "image": bytes((117, 61, 97, 78)), "stdin": b"", "walk": "in crz out halt",
        "ours_out": [32], "ref_out": [32], "ours_steps": 4, "ref_steps": 3, "halt": (3, 3),
    },
    {
        # V2/rot: ours rotate(38,19) = 774840990 -> 0x9e; bolge19 mrot(38) =
        # 258280338 -> 0x92. The divergence is the prediction.
        "name": "C3", "image": bytes((68, 38, 97, 78)), "stdin": b"", "walk": "nop rot out halt",
        "ours_out": [158], "ref_out": [146], "ours_steps": 4, "ref_steps": 3, "halt": (3, 3),
    },
    {
        "name": "C4", "image": bytes((117, 98, 79)), "stdin": b"A", "walk": "in out halt",
        "ours_out": [65], "ref_out": [65], "ours_steps": 3, "ref_steps": 2, "halt": (2, 2),
    },
]


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def display(path: pathlib.Path) -> str:
    """Evidence must not carry workstation paths (the repo rule for every public
    Malbolge remote, and the reason repo-engine blocks LOCAL_PATH_001 findings).
    The sibling checkout is addressed relative to this repository; identity is
    carried by the hash, not by the absolute path."""
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


# ── the reference's own primitives, transcribed from the pinned source ───────
# These two tables are copied from bolge19.zig:31-71 so that the *rule* can be
# checked over a sample without running anything. They are documentation-grade:
# a transcription of the peer is not an independent falsifier (the F4 lesson,
# HONESTY_LEDGER entry 24). The falsifier for P1/P2 is the binary itself: if this
# transcription were wrong, C2 could not reproduce its predicted stdout byte.
XLAT_CONCAT = (
    "SOMEBODY MAKE ME FEEL ALIVE"
    "[hj9>,5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<."
    "TVac`uY*MK'X~xDl}REokN:#?G\"i@"
    "AND SHATTER ME"
)
CRAZY_TBL = ((1, 0, 0), (1, 0, 2), (2, 2, 1))
CRZ2 = (
    4, 3, 3, 1, 0, 0, 1, 0, 0, 9, 9, 9, 9, 9, 9, 9,
    4, 3, 5, 1, 0, 2, 1, 0, 2, 9, 9, 9, 9, 9, 9, 9,
    5, 5, 4, 2, 2, 1, 2, 2, 1, 9, 9, 9, 9, 9, 9, 9,
    4, 3, 3, 1, 0, 0, 7, 6, 6, 9, 9, 9, 9, 9, 9, 9,
    4, 3, 5, 1, 0, 2, 7, 6, 8, 9, 9, 9, 9, 9, 9, 9,
    5, 5, 4, 2, 2, 1, 8, 8, 7, 9, 9, 9, 9, 9, 9, 9,
    7, 6, 6, 7, 6, 6, 4, 3, 3, 9, 9, 9, 9, 9, 9, 9,
    7, 6, 8, 7, 6, 8, 4, 3, 5, 9, 9, 9, 9, 9, 9, 9,
    8, 8, 7, 8, 8, 7, 5, 5, 4, 9, 9, 9, 9, 9, 9, 9,
)


def ref_mcrz(a: int, d: int) -> int:
    """bolge19.zig:49-63. Nine base-9 digit pairs (18 trits) plus one final
    trit = 19 trits. u32 wrapping is kept explicit; 3^19-1 fits, so no pass
    overflows."""
    r = 0
    k = 1
    mask = (1 << 32) - 1
    for _ in range(9):
        r = (r + k * CRZ2[(a % 9) + 16 * (d % 9)]) & mask
        a //= 9
        d //= 9
        k = (k * 9) & mask
    r = (r + k * CRAZY_TBL[d % 3][a % 3]) & mask
    return r


def ref_mrot(x: int) -> int:
    """bolge19.zig:65-71. Rotates the low 18 trits and leaves the 19th in place."""
    b = x % THIRD
    m = b % 3
    q = b // 3
    return (q + m * (THIRD // 3) + (x - b)) & ((1 << 32) - 1)


def ref_run(binary: pathlib.Path, image_path: pathlib.Path, stdin: bytes) -> dict:
    proc = subprocess.run(
        [str(binary), str(image_path), "--loader", "raw", "--max-steps", str(BUDGET)],
        input=stdin, capture_output=True, timeout=300,
    )
    if proc.returncode != 0:
        raise SystemExit(
            f"F13_REFERENCE_FAILURE rc={proc.returncode}\n"
            + (proc.stderr or proc.stdout).decode("utf-8", "replace")[-2000:]
        )
    obs = {"stdout": proc.stdout, "image_cells": None, "status": None,
           "steps": None, "c": None, "d": None, "a": None}
    for line in proc.stderr.decode("utf-8", "replace").splitlines():
        if line.startswith("bolge19: imagen="):
            obs["image_cells"] = int(line.split("imagen=")[1].split()[0])
        elif line.startswith("bolge19: HALT"):
            fields = dict(tok.split("=", 1) for tok in line[len("bolge19: HALT"):].split() if "=" in tok)
            obs.update(status="HALTED", steps=int(fields["steps"]), c=int(fields["c"]),
                       d=int(fields["d"]), a=int(fields["a"]))
        elif line.startswith("bolge19: MAX_STEPS"):
            obs.update(status="MAX_STEPS", steps=int(line.split()[-1]))
    if obs["status"] is None:
        raise SystemExit("F13_DRIVER_INCOMPLETE: reference printed no halt/max-steps line")
    return obs


def ours_python(core, image: bytes, stdin: bytes) -> dict:
    vm = core.MalbolgeCore(width=19, mem_limit=END, growth_policy="fixed")
    vm.load(image.decode("latin-1"))
    res = vm.run(BUDGET, stdin)
    return {
        "status": res["status"], "steps": res["steps"],
        "stdout": res["stdout"].encode("latin-1"),
        "c": vm.stats["final_c"], "d": vm.stats["final_d"],
        "program_len": vm.program_len,
        "width": vm.width, "padwidth": vm.padwidth, "mem_limit": vm.mem_limit,
    }


def ours_zig(image_path: pathlib.Path, stdin: bytes) -> dict:
    proc = subprocess.run(
        ["zig", "run", "--dep", "malbolge_free=malbolge_free",
         "-Mroot=evidence/run_f13_k19.zig", "-Mmalbolge_free=src/malbolge_free.zig",
         "--", str(image_path), stdin.hex() or "-", str(BUDGET)],
        cwd=ROOT, capture_output=True, text=True, timeout=600,
    )
    if proc.returncode != 0:
        sys.stderr.write(f"F13_ZIG_DRIVER_FAILURE rc={proc.returncode}\n")
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
        raise SystemExit("F13_DRIVER_INCOMPLETE: zig core printed no PARAM/RUN line")
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

    sib = ROOT.parent / "MalbolgeLispSlop"
    ref_src = pathlib.Path(os.environ.get("MALFREE_BOLGE19_SRC", sib / "src" / "bolge19.zig"))
    ref_profile = pathlib.Path(os.environ.get("MALFREE_BOLGE19_PROFILE",
                                              sib / "profiles" / "fixed19.json"))
    ref_bin = pathlib.Path(os.environ.get("MALFREE_BOLGE19_BIN", sib / "build" / "bolge19"))

    missing = [display(path) for path in (ref_src, ref_profile, ref_bin) if not path.is_file()]
    if missing:
        sys.stderr.write(
            "F13_REFERENCE_ABSENT: no localized deterministic fixed-3^19 reference here.\n"
            "  " + "\n  ".join(missing) + "\n"
            "  UNSHACKLED_K19_PARITY = NOT_DEMONSTRATED in this environment (NOT a mismatch).\n"
            f"  Set MALFREE_BOLGE19_SRC / _PROFILE / _BIN, or see {PREGISTRATION}.\n"
        )
        return 3

    src_sha, profile_sha = sha(ref_src.read_bytes()), sha(ref_profile.read_bytes())
    bin_sha = sha(ref_bin.read_bytes())
    for label, seen, pin in (("src", src_sha, REF_SRC_SHA256),
                             ("profile", profile_sha, REF_PROFILE_SHA256)):
        if seen != pin:
            sys.stderr.write(
                f"F13_REFERENCE_DRIFT: the {label} the expectations were read from has changed.\n"
                f"  pinned: {pin}\n  found:  {seen}\n"
                "  Every number below would be about a different machine.\n"
            )
            return 4

    json_profile = json.loads(ref_profile.read_text(encoding="utf-8"))
    core = module_from(ROOT / "src" / "malbolge_core.py", "mb_core")
    oracle = module_from(ROOT / "vendor" / "canonical_malbolge_py" / "malbolge.py", "mb_oracle")

    print(f"F13 reference src={display(ref_src)} sha={src_sha[:16]}")
    print(f"F13 reference profile={display(ref_profile)} sha={profile_sha[:16]}")
    print(f"F13 reference bin={display(ref_bin)} sha={bin_sha[:16]} (build product, recorded not pinned)")
    print(f"F13 ours python=src/malbolge_core.py zig=src/malbolge_free.zig budget={BUDGET}")
    print(f"F13 scope=region 0 (c < {THIRD}) forward-walk images of <=4 cells; "
          f"region offsets of the reference = {REF_REGION_OFFS}")

    # ── definitional layer ───────────────────────────────────────────────────
    zg_probe = None
    workdir = pathlib.Path(tempfile.mkdtemp(prefix="f13_"))
    try:
        image_paths = {}
        for case in CASES:
            path = workdir / f"{case['name']}.mb"
            path.write_bytes(case["image"])  # bytes, never write_text: no line endings
            image_paths[case["name"]] = path

        # First Zig run doubles as the PARAM source for D3/D5.
        zg_probe = ours_zig(image_paths["C1"], b"")
        param = zg_probe["param"]

        for case in CASES:
            case["ref"] = ref_run(ref_bin, image_paths[case["name"]], case["stdin"])
            case["py"] = ours_python(core, case["image"], case["stdin"])
            case["zg"] = ours_zig(image_paths[case["name"]], case["stdin"])
            print(
                f"  {case['name']:2s} {case['walk']:18s} "
                f"ref status={case['ref']['status']} steps={case['ref']['steps']} "
                f"c={case['ref']['c']} d={case['ref']['d']} a={case['ref']['a']} "
                f"out={case['ref']['stdout'].hex() or '-'} | "
                f"py status={case['py']['status']} steps={case['py']['steps']} "
                f"out={case['py']['stdout'].hex() or '-'} | "
                f"zg status={case['zg']['status']} steps={case['zg']['steps']} "
                f"out_len={case['zg']['stdout_len']} "
                f"first={'-' if case['zg']['first'] is None else format(case['zg']['first'], '02x')}"
            )

        expectations: list[tuple[str, bool, str]] = []

        def check(name: str, ok: bool, measured: str) -> None:
            expectations.append((name, ok, measured))

        check("D1_end_equals_pow3_19",
              json_profile["end"] == END == 3 ** 19 == int(param["pow3_19"]),
              f"json.end={json_profile['end']} 3**19={3 ** 19} zig pow3(19)={param['pow3_19']}")
        # The reference's EOF value is not read from its source here, it is the
        # `a` it reports at the halt of C1, where the only input was end of input.
        check("D2_eof_rule_value",
              json_profile["eof_value"] == EOF_VALUE == 3 ** 19 - 1
              and CASES[0]["ref"]["a"] == EOF_VALUE,
              f"json.eof_value={json_profile['eof_value']} 3^19-1={3 ** 19 - 1} "
              f"reference a at C1 halt={CASES[0]['ref']['a']} "
              "(both cores: pow3(padwidth)-1, malbolge_core.py:210 / malbolge_free.zig:517)")
        check("D3_wrap_modulus",
              int(param["mem_limit"]) == END == json_profile["end"] and param["growth"] == "fixed",
              f"zg mem_limit={param['mem_limit']} growth={param['growth']}; "
              "both advance c,d modulo it (malbolge_core.py:263 / bolge19.zig:420-421)")
        check("D4_dispatch_opcode_set",
              set(json_profile["dispatch"].values()) == set(oracle._VALID_OPS),
              f"json={sorted(set(json_profile['dispatch'].values()))} "
              f"vendored oracle _VALID_OPS={sorted(oracle._VALID_OPS)}")
        check("D5_trit_width",
              json_profile["trits"] == 19 == CASES[0]["py"]["width"] == CASES[0]["py"]["padwidth"]
              == int(param["width"]) == int(param["padwidth"]),
              f"json.trits={json_profile['trits']} py width={CASES[0]['py']['width']} "
              f"padwidth={CASES[0]['py']['padwidth']} zg width={param['width']} padwidth={param['padwidth']}")

        rng = random.Random(20261018)
        crazy_pairs = [(rng.randrange(0, END), rng.randrange(0, END)) for _ in range(200_000)]
        crazy_bad = [k for k in crazy_pairs if ref_mcrz(*k) != core.crazy(k[0], k[1], 19)]
        check("P1_mcrz_equals_crazy19", not crazy_bad,
              f"{len(crazy_pairs)} seeded pairs (random.Random(20261018)), mismatches={len(crazy_bad)}"
              + (f" first={crazy_bad[0]}" if crazy_bad else ""))

        rng2 = random.Random(20261019)
        rot_values = [rng2.randrange(0, THIRD) for _ in range(200_000)]
        rot_bad = [v for v in rot_values if ref_mrot(v) != core.rotate(v, 19)]
        rot_predicate = [v for v in rot_values if v % 3 != 0]
        check("P2_mrot_diverges_iff_v_mod_3", set(rot_bad) == set(rot_predicate),
              f"{len(rot_values)} values under 3^18; divergent={len(rot_bad)} "
              f"predicate(v%3!=0)={len(rot_predicate)} "
              f"set_equality={set(rot_bad) == set(rot_predicate)}")

        for case in CASES:
            tag = case["name"]
            ref, py, zg = case["ref"], case["py"], case["zg"]
            check(f"R{tag[1:]}_status_and_halt_address",
                  ref["status"] == py["status"] == zg["status"] == "HALTED"
                  and (py["c"], py["d"]) == (zg["c"], zg["d"]) == (ref["c"], ref["d"])
                  and tuple(case["halt"]) == (ref["c"], ref["d"]),
                  f"ref={ref['status']}@({ref['c']},{ref['d']}) py=({py['c']},{py['d']}) "
                  f"zg=({zg['c']},{zg['d']})")
            if case["ours_out"] == case["ref_out"]:
                ok_out = (list(py["stdout"]) == list(ref["stdout"]) == case["ours_out"]
                          and zg["stdout_len"] == len(case["ours_out"])
                          and zg["first"] == case["ours_out"][0])
                check(f"R{tag[1:]}_stdout_equal", ok_out,
                      f"ref={ref['stdout'].hex()} py={py['stdout'].hex()} "
                      f"zg_first={zg['first']} predicted equal {bytes(case['ours_out']).hex()}")
            else:
                ok_out = (list(py["stdout"]) == case["ours_out"]
                          and list(ref["stdout"]) == case["ref_out"]
                          and zg["first"] == case["ours_out"][0]
                          and py["stdout"] != ref["stdout"])
                check(f"R{tag[1:]}_stdout_diverges_as_predicted", ok_out,
                      f"py={py['stdout'].hex()} zg_first={zg['first']} ref={ref['stdout'].hex()} "
                      f"predicted ours={bytes(case['ours_out']).hex()} "
                      f"ref={bytes(case['ref_out']).hex()} (V2/rot)")
            check(f"R{tag[1:]}_step_convention",
                  py["steps"] == zg["steps"] == case["ours_steps"]
                  and ref["steps"] == case["ref_steps"]
                  and py["steps"] == ref["steps"] + 1,
                  f"py={py['steps']} zg={zg['steps']} ref={ref['steps']} (V4: halt not counted)")

        check("L1_raw_loader_image_length",
              all(c["ref"]["image_cells"] == len(c["image"]) == c["py"]["program_len"]
                  for c in CASES),
              f"ref image_cells={[c['ref']['image_cells'] for c in CASES]} "
              f"file_bytes={[len(c['image']) for c in CASES]} "
              f"py program_len={[c['py']['program_len'] for c in CASES]}")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    for name, ok, measured in expectations:
        print(f"F13 EXP {name}: {'MATCH' if ok else 'FALSIFIED'} ({measured})")
    falsified = [name for name, ok, _ in expectations if not ok]
    print(f"F13 EXPECTATIONS={len(expectations)} MATCH={len(expectations) - len(falsified)} "
          f"FALSIFIED={len(falsified)}")

    verdict = "PASS" if not falsified else "FAIL"
    print(
        "F13 UNSHACKLED_K19_PARITY=" + verdict
        + " (scoped: deterministic fixed-3^19, region 0, <=4 instructions, 3 machines)"
    )
    print(
        "F13 DISCLOSURE what_is_NOT_claimed: not Lutter Unshackled parity (V1 region offsets "
        "+117/+140, V2 rot width 18 vs 19, V3 encryption alphabet 27 vs 33 and guard <135 vs "
        "33..126, V5 tail representation), not Turing completeness, not Unicode I/O, not the "
        "canonical loader, not any address >= 3^18, not the encryption cascade. V2 is MEASURED "
        "(C3 and P2); V1, V3 and V5 are identified by reading only."
    )

    if args.output:
        out = args.output if args.output.is_absolute() else ROOT / args.output
        if out.exists():
            raise SystemExit(f"refusing to overwrite existing report: {out}")
        report = {
            "gate": "F13",
            "preregistration": PREGISTRATION,
            "reference": {
                "source": display(ref_src), "source_sha256": src_sha,
                "profile": display(ref_profile), "profile_sha256": profile_sha,
                "binary": display(ref_bin), "binary_sha256": bin_sha,
            },
            "budget": BUDGET,
            "scope": {"region": 0, "region_limit": THIRD, "region_offsets": list(REF_REGION_OFFS),
                      "max_instructions": 4},
            "cases": [
                {
                    "name": c["name"], "walk": c["walk"],
                    "image": list(c["image"]), "image_sha256": sha(c["image"]),
                    "stdin_hex": c["stdin"].hex(),
                    "reference": {"status": c["ref"]["status"], "steps": c["ref"]["steps"],
                                  "c": c["ref"]["c"], "d": c["ref"]["d"], "a": c["ref"]["a"],
                                  "image_cells": c["ref"]["image_cells"],
                                  "stdout_hex": c["ref"]["stdout"].hex()},
                    "python": {"status": c["py"]["status"], "steps": c["py"]["steps"],
                               "c": c["py"]["c"], "d": c["py"]["d"],
                               "stdout_hex": c["py"]["stdout"].hex()},
                    "zig": {k: v for k, v in c["zg"].items() if k != "param"},
                    "predicted": {"ours_out": c["ours_out"], "ref_out": c["ref_out"],
                                  "ours_steps": c["ours_steps"], "ref_steps": c["ref_steps"],
                                  "halt": list(c["halt"])},
                }
                for c in CASES
            ],
            "primitive_sample": {
                "seed_crazy": 20261018, "seed_rot": 20261019, "draws": 200_000,
                "crazy_mismatches": len(crazy_bad),
                "rot_mismatches": len(rot_bad),
                "rot_predicate_mismatches": len(rot_predicate),
            },
            "expectations": [{"name": n, "ok": ok, "measured": m} for n, ok, m in expectations],
            "divergences": {
                "V1_region_offsets": {"measured": False, "value": list(REF_REGION_OFFS)},
                "V2_rot_width": {"measured": True, "evidence": ["C3", "P2"]},
                "V3_encryption_alphabet": {"measured": False,
                                           "ours": "94-entry xlat indexed m-33, guard 33..126",
                                           "reference": "135-entry concatenation indexed m, guard <135"},
                "V4_halt_step_convention": {"measured": True, "evidence": "all four cases"},
                "V5_tail_representation": {"measured": False},
            },
            "verdict": verdict,
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
