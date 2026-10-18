#!/usr/bin/env python3
"""Quine-under-epochal differential (F10).

Asks the question that the synthetic F9 witnesses cannot answer: does the
`epochal` profile agree with Classic on a *real* self-reproducing program, one
that survives far longer than the Classic frontier `3^10 = 59049`?

Three profiles of OUR OWN runtime are compared against each other, plus the
Python core as a cross-check:

  classic      width 10, mem_limit = 3**10, fixed   -> must be Malbolge
  pure_fixed   width 10, mem_limit = None,  fixed   -> isolates "no wrap"
  epochal      width 10, mem_limit = None,  epochal -> adds frontier growth

Expectations were written down AFTER a 1 000 000-step pilot on this machine and
before the confirmatory run sealed here, so this artifact tests generalization
(budget, trace pass, cross-core agreement), not discovery. The pilot is recorded
in `pilot` for that reason.

Exit codes follow verdicts, house convention:
  0 all expectations met, 1 an expectation was falsified,
  3 the program input is not reachable (NOT_DEMONSTRATED, an explicit skip),
  4 hard failure (pinned program drifted, driver error, cores disagree).
"""
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
SIBLING = ROOT.parent  # `.../ISyCo Git`
DEFAULT_PROGRAM = SIBLING / "MALDOOM" / "vendor" / "quines" / "quine_lutter.malbolge"

# The program is third-party (Matthias Lutter) and is NOT vendored here. It is
# pinned by hash so a silently edited input cannot manufacture a verdict.
PROGRAM_SHA256 = "dca8476f8b70c8462c32f661f63c5f8b1ad6c33946b3c7a9a35186c824117d98"
PROGRAM_CITATION = "DannyBaanks/MalDOOM:vendor/quines/quine_lutter.malbolge"

# Budgets default to a full Classic halt. They are env-overridable so a cheaper
# trial run is possible without editing the gate; the sealed artifact records
# whichever values were actually used.
TRACE_BUDGET = int(os.environ.get("MALFREE_F10_TRACE_BUDGET", 60_000))     # Zig pass 1 traces
STDOUT_BUDGET = int(os.environ.get("MALFREE_F10_STDOUT_BUDGET", 200_000_000))  # Zig pass 2
CORE_BUDGET = int(os.environ.get("MALFREE_F10_CORE_BUDGET", 20_000))       # both cores here

program = pathlib.Path(os.environ.get("MALFREE_QUINE_LUTTER", DEFAULT_PROGRAM))
if not program.is_file():
    print(
        "F10_PROGRAM_MISSING: no Lutter quine is reachable:\n"
        "  tried: {}\n  override: MALFREE_QUINE_LUTTER=<path>\n"
        "  QUINE_EPOCHAL_DIFFERENTIAL = NOT_DEMONSTRATED here (NOT a runtime failure).\n"
        "  The program is deliberately not vendored in this repository.".format(program),
        file=sys.stderr,
    )
    raise SystemExit(3)

prog_bytes = program.read_bytes()
digest = hashlib.sha256(prog_bytes).hexdigest()
if digest != PROGRAM_SHA256:
    print(
        "F10_PROGRAM_DRIFT: the quine no longer matches its pin.\n"
        "  pinned: {}\n  found:  {}\n"
        "  A different input would make every number below meaningless.".format(
            PROGRAM_SHA256, digest),
        file=sys.stderr,
    )
    raise SystemExit(4)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def val(tok: dict, key: str):
    """Zig prints `{?d}`: either a number or the literal `null`. Normalise both
    so a comparison against None/0 is a comparison against a real value."""
    raw = tok.get(key)
    if raw is None or raw == "null":
        return None
    return int(raw)


def run_driver(trace_budget: int, stdout_budget: int) -> dict:
    proc = subprocess.run(
        ["zig", "run", "--dep", "malbolge_free=malbolge_free",
         "-Mroot=evidence/run_quine_epochal.zig",
         "-Mmalbolge_free=src/malbolge_free.zig",
         "--", str(program), str(trace_budget), str(stdout_budget)],
        cwd=ROOT, capture_output=True, text=True, timeout=7200,
    )
    if proc.returncode != 0:
        print("F10_DRIVER_FAILURE:\n" + (proc.stderr or proc.stdout), file=sys.stderr)
        raise SystemExit(4)
    rows, diffs, images = {}, {}, {}
    for line in proc.stderr.splitlines():
        tok = dict(p.split("=", 1) for p in line.split() if "=" in p)
        if line.startswith("RUN "):
            rows[tok["prof"]] = {
                "status": tok["status"], "steps": int(tok["steps"]),
                "padwidth": int(tok["padwidth"]), "growth_events": int(tok["growth_events"]),
                "final_c": int(tok["final_c"]), "final_d": int(tok["final_d"]),
                "max_addr_touched": int(tok["max_addr"]), "cells_materialized": int(tok["cells"]),
                "stdout_len": int(tok["stdout_len"]), "stdout_sha256": tok["stdout_sha"],
                "stdout_equals_program": tok["source_eq_stdout"] == "true",
            }
        elif line.startswith("IMAGE stored_sha"):
            images["stored_sha256"] = {k: tok[k] for k in ("classic", "pure_fixed", "epochal")}
        elif line.startswith("IMAGE addressed_sha"):
            images["addressed_sha256"] = {k: tok[k] for k in ("classic", "pure_fixed", "epochal")}
            images["program_len"] = int(tok["program_len"])
        elif line.startswith("IMAGE addressed_first_diff"):
            images["addressed_first_diff"] = {
                "classic_vs_pure_fixed": val(tok, "classic_vs_pure_fixed"),
                "classic_vs_epochal": val(tok, "classic_vs_epochal"),
                "pure_fixed_vs_epochal": val(tok, "pure_fixed_vs_epochal"),
            }
        elif line.startswith("DIFF_STDOUT"):
            diffs["stdout_first_byte"] = {
                "classic_vs_epochal": val(tok, "classic_vs_epochal"),
                "classic_vs_pure_fixed": val(tok, "classic_vs_pure_fixed"),
                "pure_fixed_vs_epochal": val(tok, "pure_fixed_vs_epochal"),
            }
        elif line.startswith("DIFF_TRACE"):
            pair = {
                "classic_vs_epochal": val(tok, "classic_vs_epochal"),
                "classic_vs_pure_fixed": val(tok, "classic_vs_pure_fixed"),
                "pure_fixed_vs_epochal": val(tok, "pure_fixed_vs_epochal"),
            }
            diffs.setdefault("trace_" + tok["field"], pair)
        elif line.startswith("WIDEN "):
            rows["epochal_widen"] = {
                "growth_events": int(tok["epochal_events_at_stdout_budget"]),
                "final_padwidth": int(tok["final_padwidth"]),
            }
    missing = {"classic", "pure_fixed", "epochal"} - set(rows)
    if missing:
        print("F10_DRIVER_FAILURE: no RUN line for {}".format(sorted(missing)), file=sys.stderr)
        raise SystemExit(4)
    return rows, diffs, images


def load_module(path, name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- Zig core, full measurement ----------------------------------------------
t0 = time.time()
zig_rows, zig_diffs, zig_images = run_driver(TRACE_BUDGET, STDOUT_BUDGET)
zig_seconds = round(time.time() - t0, 2)

# --- Zig core at the bounded budget, so the Python core can be compared ------
t0 = time.time()
zig_small, _, _ = run_driver(CORE_BUDGET, CORE_BUDGET)
zig_small_seconds = round(time.time() - t0, 2)

# --- Python core at the same bounded budget ----------------------------------
core = load_module(ROOT / "src" / "malbolge_core.py", "mb_core")
src_text = prog_bytes.decode("latin-1")
py_rows = {}
t0 = time.time()
for prof, kwargs in (
    ("classic", {"width": 10, "mem_limit": 3 ** 10, "growth_policy": "fixed"}),
    ("pure_fixed", {"width": 10, "mem_limit": None, "growth_policy": "fixed"}),
    ("epochal", {"width": 10, "mem_limit": None, "growth_policy": "epochal"}),
):
    vm = core.MalbolgeCore(**kwargs)
    vm.load(src_text)
    res = vm.run(CORE_BUDGET, stdin_data=b"")
    out = res["stdout"].encode("latin-1")
    py_rows[prof] = {
        "status": res["status"], "steps": res["steps"],
        "padwidth": vm.padwidth, "growth_events": res["growth_events"],
        "growth_event_list": list(vm.stats["width_growth_events"]),
        "max_addr_touched": res["max_addr_touched"],
        "stdout_len": len(out), "stdout_sha256": sha(out),
    }
py_seconds = round(time.time() - t0, 2)

# --- verdicts ----------------------------------------------------------------
# `frontier_step` is where the epochal run widens, read from the Python core's
# event log (the Zig core counts events but does not timestamp them); the
# cross-core agreement verdict is what licenses using it for the Zig trace.
events = py_rows["epochal"]["growth_event_list"]
frontier_step = events[0]["step"] if events else None


def earliest(diffs: dict, key: str):
    """Smallest divergence step over the five compared trace fields, ignoring
    fields that never diverge. `stdout_prefix_len` is excluded: it is a stdout
    comparison, not a per-step trace field."""
    vals = [v[key] for k, v in diffs.items()
            if k.startswith("trace_") and k != "trace_stdout_prefix_len" and v[key] is not None]
    return min(vals) if vals else None


div_classic = earliest(zig_diffs, "classic_vs_pure_fixed")
div_prefix = earliest(zig_diffs, "pure_fixed_vs_epochal")
div_classic_dfield = zig_diffs["trace_d_after"]["classic_vs_pure_fixed"]

expect = {
    "classic_reproduces_the_quine": (
        zig_rows["classic"]["status"] == "HALTED"
        and zig_rows["classic"]["stdout_equals_program"]),
    "pre_execution_images_are_profile_independent": (
        len(set(zig_images["stored_sha256"].values())) == 1
        and len(set(zig_images["addressed_sha256"].values())) == 1
        and all(v is None for v in zig_images["addressed_first_diff"].values())),
    "epochal_stdout_is_not_classic_stdout": (
        zig_rows["epochal"]["stdout_sha256"] != zig_rows["classic"]["stdout_sha256"]),
    "epochal_diverges_from_classic_from_the_first_byte": (
        zig_diffs["stdout_first_byte"]["classic_vs_epochal"] == 0),
    "unbounded_alone_diverges_from_classic": (
        zig_diffs["stdout_first_byte"]["classic_vs_pure_fixed"] == 0),
    "a_real_program_triggers_at_least_one_widening": (
        zig_rows["epochal"]["growth_events"] >= 1 and frontier_step is not None),
    "the_frontier_crossing_explains_the_divergence": (
        frontier_step is not None and div_classic is not None
        and abs(int(div_classic) - frontier_step) <= 1),
    "prefix_preservation_holds_before_the_frontier": (
        frontier_step is not None and div_prefix is not None
        and int(div_prefix) >= frontier_step),
    "free_profiles_halt_before_classic": (
        zig_rows["epochal"]["status"] == "HALTED"
        and zig_rows["pure_fixed"]["status"] == "HALTED"
        and zig_rows["classic"]["status"] == "HALTED"
        and zig_rows["epochal"]["steps"] < zig_rows["classic"]["steps"]
        and zig_rows["pure_fixed"]["steps"] < zig_rows["classic"]["steps"]),
    "cores_agree_on_the_bounded_budget": all(
        zig_small[p]["status"] == py_rows[p]["status"]
        and zig_small[p]["steps"] == py_rows[p]["steps"]
        and zig_small[p]["stdout_sha256"] == py_rows[p]["stdout_sha256"]
        for p in ("classic", "pure_fixed", "epochal")),
}

verdicts = [{"claim": k, "expected": True, "measured": v,
             "verdict": "MATCH" if v else "FALSIFIED"} for k, v in expect.items()]
all_match = all(v["measured"] for v in verdicts)

report = {
    "phase": "F10",
    "format": "quine-epochal-differential/1",
    "claim": "EPOCHAL_ON_REAL_QUINE",
    "question": ("does the epochal profile agree with Classic on a program that "
                 "outlives the Classic frontier 3^10 = 59049?"),
    "program": {
        "citation": PROGRAM_CITATION, "sha256": digest, "bytes": len(prog_bytes),
        "vendored_here": False,
        "note": ("third-party source (Matthias Lutter), pinned by hash, read from a "
                 "sibling repository; the path recorded here is a public remote "
                 "citation, never a local absolute path"),
    },
    "runtime": {"zig": "src/malbolge_free.zig", "python": "src/malbolge_core.py"},
    "profiles": {
        "classic": "width 10, mem_limit 3^10 (wrap), growth fixed",
        "pure_fixed": "width 10, mem_limit None, growth fixed",
        "epochal": "width 10, mem_limit None, growth epochal (widen at the frontier)",
    },
    "budgets": {"zig_trace": TRACE_BUDGET, "zig_stdout": STDOUT_BUDGET, "cross_core": CORE_BUDGET},
    "pilot": {
        "note": ("measured on this machine before the expectations above were written; "
                 "stdout budget 1 000 000, traces 600 steps"),
        "classic": {"status": "MAX_STEPS", "steps": 1_000_000, "stdout_len": 837,
                    "stdout_sha256": "515b00731d4b4eb78f3ee8d766d1b4048d413d25da7002aa9bdd1bf1355bc0d1"},
        "pure_fixed": {"status": "HALTED", "steps": 6_521, "stdout_len": 1},
        "epochal": {"status": "HALTED", "steps": 8_761, "growth_events": 1, "padwidth": 11,
                    "stdout_len": 0},
    },
    "pre_execution_images": zig_images,
    "zig_full": zig_rows,
    "zig_bounded": zig_small,
    "python_bounded": py_rows,
    "frontier": {
        "boundary_3_pow_10": 3 ** 10,
        "widening_step_from_python_event_log": frontier_step,
        "event_log": events,
        "earliest_trace_divergence_classic_vs_pure_fixed": div_classic,
        "earliest_trace_divergence_pure_fixed_vs_epochal": div_prefix,
        "d_after_divergence_classic_vs_pure_fixed": div_classic_dfield,
        "mechanism": ("the first pointer to reach the frontier is D, not C: at the "
                      "divergence step D becomes 3^10, Classic wraps it to address 0 "
                      "while the unbounded profiles read the cell at 3^10, and the "
                      "epochal preflight widens at the next step. That is why the "
                      "synthetic witnesses' "
                      "step-59050 crossing does not generalise: a real program jumps "
                      "to the frontier far earlier by assigning pointers"),
        "step_provenance": ("the widening step is the Python core's event-log value; the Zig "
                            "core counts WIDEN events without timestamping them, and "
                            "cores_agree_on_the_bounded_budget is what makes the number "
                            "usable against the Zig trace"),
    },
    "trial": {
        "note": ("two bounded trials (stdout budgets 15 000 and 1 000 000) ran first. The "
                 "15 000 one falsified the strict reading of prefix preservation: on the "
                 "`d_after` field alone the earliest pure_fixed-vs-epochal divergence is "
                 "1274, and over all five compared fields it is 1246 — in both readings "
                 "AFTER the widening at 1230, not at it. The invariant P1 says 'equal "
                 "until the first WIDEN', so the correct expectation is >= the widening "
                 "step, and the expectation was changed to that BEFORE the sealed run. "
                 "Parsing was also corrected (`{?d}` prints the literal `null`, which had "
                 "been compared as a string). Nothing about the runtime was altered to fit."),
        "widening_step": 1230,
        "d_after_only_pure_fixed_vs_epochal_divergence": 1274,
        "earliest_pure_fixed_vs_epochal_divergence_all_fields": 1246,
        "classic_reproduction_not_possible_below_its_own_halt": True,
    },
    "divergence": zig_diffs,
    "timing_seconds": {"zig_full": zig_seconds, "cross_core_bounded": zig_small_seconds,
                       "python_bounded": py_seconds},
    "verdicts": verdicts,
    "all_match": all_match,
    "counts_are_explicit": {
        "profiles": 3, "cores": 2, "programs": 1, "verdicts": len(verdicts),
        "cross_core_profile_comparisons": 6, "trace_fields_compared": 5,
    },
    "scope": ("one program (Lutter's quine: 59 852 bytes on disk, "
              "{} loaded cells), width 10 boot, empty stdin, this machine; each profile "
              "is bounded by its own HALT or by the budget recorded in `budgets`".format(
                  zig_images["program_len"])),
    "not_claimed": [
        "that epochal is Turing-complete or not: the claim is about compatibility with Classic",
        "that the quine would print correctly under any other growth policy",
        "CI reproducibility: the pinned program is not vendored, so a fresh clone exits 3",
        "any statement about Unshackled or the assisted BF backend",
        "a general bound for when a real program reaches the frontier: one witness only",
    ],
}

out_path = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--output" else None
if out_path is None:
    print("usage: compare_quine_epochal.py --output <path.json>", file=sys.stderr)
    raise SystemExit(4)
if out_path.exists():
    print("F10_OUTPUT_EXISTS: {} — evidence paths are never reused.".format(out_path),
          file=sys.stderr)
    raise SystemExit(4)
out_path.write_bytes(json.dumps(report, indent=2, sort_keys=False).encode("utf-8"))

print("== F10 quine-under-epochal differential ==")
for v in verdicts:
    print("  {}: {} (expected {})".format(v["verdict"], v["claim"], v["expected"]))
print("  all_match={}  verdicts={}  report={}".format(all_match, len(verdicts), out_path.name))
for p in ("classic", "pure_fixed", "epochal"):
    r = zig_rows[p]
    print("  {:11s} status={:9s} steps={:>10d} w={:>2d} growth={:<2d} stdout_len={:>6d}".format(
        p, r["status"], r["steps"], r["padwidth"], r["growth_events"], r["stdout_len"]))
raise SystemExit(0 if all_match else 1)
