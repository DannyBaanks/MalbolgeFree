#!/usr/bin/env python3
"""F11 — the vendored quine under the frontier, and what widening does to `in`.

F10 (`compare_quine_epochal.py`) asks the same frontier question, but its input is
a third-party program that is deliberately NOT vendored, so on a clean clone it
exits 3 and CI can only report the absence. F11 runs on bytes that live in this
repository (`corpus/classic/quine_m281.mal`), so CI re-executes it and
`NOT_DEMONSTRATED` is unreachable by construction.

What is new here, and what the gate is really for
-------------------------------------------------
Both cores assign `in` at end of input as `3^padwidth - 1` (HONESTY_LEDGER entry
24). Under `classic` and `pure_fixed` `padwidth` never moves, so end of input is
the constant 59 048 that every published Classic program hard-codes. Under
`epochal` it is a variable: once the machine widens, end of input stops being
59 048. That consequence of entry 24 had never been measured, and entry 24's note
(c) assumed it could not matter ("they read no stdin") — this program reads
stdin, so the assumption is tested here instead of trusted.

Pre-registered expectations
---------------------------
Written down on 2026-10-18 from a bounded pilot on THIS machine against the
published Python core (`src/malbolge_core.py`) at budget 60 000, before this
gate's confirmatory run. They therefore test generalization — to the Zig core, to
a Windows runner, to a clean checkout — not discovery:

   E1  program sha256 == PROGRAM_SHA256                        (integrity, rc 4)
   E2  classic at this budget: MAX_STEPS at 60 000 steps       (completion is F12)
   E3  classic reaches no address >= 3**10, because it wraps
   E4  classic executes no `in` within the budget
   E5  pure_fixed HALTED at 9 718 steps, 0 bytes of stdout
   E6  pure_fixed widens never: padwidth 10, growth 0
   E7  pure_fixed `in` at end of input returns 59 048  == 3**10 - 1
   E8  epochal  HALTED at 25 729 steps, 3 bytes of stdout (not the program)
   E9  epochal  widens exactly once: padwidth 11, growth 1
   E10 epochal  first trace address >= 3**10 is step 1 229
   E11 epochal  `in` at end of input returns 177 146 == 3**11 - 1   <- the new claim
   E12 both wrap-free profiles differ from classic stdout at byte 0
   E13 P1: no step-valued trace field differs at a step strictly below 1 229
   E14 every compared observable agrees between the Python core and the Zig core
   E15 the two no-crossing controls (`reproducer.mal`, `hello.mal`) are identical
       across all three profiles and in both cores

**Disclosure about the first run of this gate (2026-10-18).** E13 came back
FALSIFIED and the cause was this checker, not the machine: it folded
`field=stdout_prefix_len` — which is a BYTE index into stdout — into a predicate
over STEP indices, so "byte 0 differs" was read as "differs before step 1229".
E13 now runs over step-valued fields only and prints the excluded field with the
verdict. No other expectation was altered after seeing the numbers, and the
measured values quoted in E5-E11 are the pilot's, unchanged.

Read-only: prints a verdict, writes nothing unless --output names a NEW path.
Exit codes follow verdicts: 0 all met, 1 an expectation falsified, 4 integrity or
driver failure. There is no exit 3: the input is in the repository.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "corpus" / "classic" / "quine_m281.mal"
PROGRAM_SHA256 = "96b670b825372a0f41fa3b574d47457f92654b76411e5d5be4c438003087610e"
CONTROLS = ("corpus/classic/reproducer.mal", "corpus/classic/hello.mal")
PROFILES = ("classic", "pure_fixed", "epochal")
BUDGET = int(os.environ.get("MALFREE_F11_BUDGET", 60_000))
TRACE_FIELDS = ("op", "a_after", "c_after", "d_after")
# `run_quine_epochal.zig` also prints field=stdout_prefix_len, which is a BYTE
# index into stdout, not a step. It is informative (classic vs epochal differ at
# byte 0) but it must never enter a "no difference before step N" predicate: the
# first version of this gate folded it into E13 and reported a falsified P1 that
# was a checker defect, not a machine one.
STEP_VALUED_FIELDS = TRACE_FIELDS + ("cell_before",)
# The two cores count `max_addr_touched` by different rules (see the disclosure
# printed at the end), so it is reported but deliberately not compared.
COMPARED_FIELDS = ("status", "steps", "padwidth", "growth", "stdout_len",
                   "stdout_sha256", "in_events", "first_addr_ge_3pow10_step")


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_core():
    spec = importlib.util.spec_from_file_location("mb_core", ROOT / "src" / "malbolge_core.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def py_profile_kwargs(core):
    return {
        "classic": dict(width=10, mem_limit=3 ** 10, growth_policy="fixed"),
        "pure_fixed": dict(width=10, mem_limit=None, growth_policy="fixed"),
        "epochal": dict(width=10, mem_limit=None, growth_policy="epochal"),
    }


def first_diff_step(a: list, b: list, field: str):
    n = min(len(a), len(b))
    for i in range(n):
        if a[i][field] != b[i][field]:
            return a[i]["step"]
    if len(a) != len(b):
        return n + 1
    return None


def first_byte_diff(a: bytes, b: bytes):
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    if len(a) != len(b):
        return n
    return None


def python_observations(core, program_text: str, budget: int) -> dict:
    """Run every profile with a per-step trace, reduced to the observables this
    gate compares. Raw stdout bytes are kept so the byte-index claim E12 is about
    bytes rather than about hashes; they are dropped from the JSON report."""
    rows = {}
    for profile, kwargs in py_profile_kwargs(core).items():
        vm = core.MalbolgeCore(**kwargs)
        vm.load(program_text)
        res, events = vm.trace_run(max_steps=budget, stdin_data=b"")
        out = res["stdout"].encode("latin-1")
        rows[profile] = {
            "status": res["status"],
            "steps": res["steps"],
            "padwidth": res["padwidth"],
            "growth": res["growth_events"],
            "max_addr_touched": res["max_addr_touched"],
            "stdout_len": len(out),
            "stdout_sha256": sha(out),
            "stdout_bytes": out,
            "in_events": [[e["step"], e["a_after"]] for e in events if e["op"] == 23],
            "first_addr_ge_3pow10_step": next(
                (e["step"] for e in events
                 if e["c_after"] >= 3 ** 10 or e["d_after"] >= 3 ** 10),
                None,
            ),
            "trace": [{**{k: e[k] for k in TRACE_FIELDS}, "step": e["step"]} for e in events],
            # The Python core stamps each WIDEN with its own step counter, which
            # runs one ahead of the trace event counter for the same crossing.
            "widen_events": list(vm.stats["width_growth_events"]),
        }
    return rows


def zig_run(driver: str, argv: list[str]) -> str:
    proc = subprocess.run(
        ["zig", "run", "--dep", "malbolge_free=malbolge_free",
         f"-Mroot=evidence/{driver}", "-Mmalbolge_free=src/malbolge_free.zig", "--", *argv],
        cwd=ROOT, capture_output=True, text=True, timeout=7200,
    )
    if proc.returncode != 0:
        sys.stderr.write(f"F11_DRIVER_FAILURE {driver} rc={proc.returncode}\n")
        sys.stderr.write((proc.stderr or proc.stdout)[-4000:])
        raise SystemExit(4)
    return proc.stderr


def zig_observations(program_path: pathlib.Path, budget: int) -> dict:
    raw = zig_run("run_f11_observations.zig", [str(program_path), str(budget)])
    rows = {}
    for line in raw.splitlines():
        parts = dict(tok.split("=", 1) for tok in line.split() if "=" in tok)
        if line.startswith("RUN prof="):
            rows[parts["prof"]] = {
                "status": parts["status"],
                "steps": int(parts["steps"]),
                "padwidth": int(parts["padwidth"]),
                "growth": int(parts["growth"]),
                "max_addr_touched": int(parts["max_addr"]),
                "stdout_len": int(parts["stdout_len"]),
                "stdout_sha256": parts["stdout_sha"],
                "in_events": [],
                "first_addr_ge_3pow10_step": None,
            }
        elif line.startswith("IN prof="):
            rows[parts["prof"]]["in_events"].append([int(parts["step"]), int(parts["a_after"])])
        elif line.startswith("OBS prof="):
            value = parts["first_addr_ge_3pow10_step"]
            rows[parts["prof"]]["first_addr_ge_3pow10_step"] = (
                None if value == "null" else int(value)
            )
    missing = [p for p in PROFILES if p not in rows]
    if missing:
        sys.stderr.write(f"F11_DRIVER_INCOMPLETE missing profiles {missing}\n")
        raise SystemExit(4)
    return rows


def zig_trace_diffs(program_path: pathlib.Path, budget: int) -> dict:
    """Reuse the F10 driver for the per-field first-difference numbers: it already
    compares the three traces pairwise and prints the step of the first difference
    per field. Equal budgets make it skip its second (unbounded stdout) pass."""
    raw = zig_run("run_quine_epochal.zig", [str(program_path), str(budget), str(budget)])
    diffs = {}
    for line in raw.splitlines():
        if not line.startswith("DIFF_TRACE field="):
            continue
        parts = dict(tok.split("=", 1) for tok in line.split() if "=" in tok)

        def num(key: str):
            return None if parts[key] == "null" else int(parts[key])

        diffs[parts["field"]] = {
            "classic_vs_epochal": num("classic_vs_epochal"),
            "classic_vs_pure_fixed": num("classic_vs_pure_fixed"),
        }
    return diffs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=pathlib.Path,
                        help="write the measurement JSON to this NEW path")
    args = parser.parse_args()

    if not PROGRAM.is_file():
        sys.stderr.write(f"F11_PROGRAM_ABSENT {PROGRAM}\n")
        return 4
    prog_bytes = PROGRAM.read_bytes()
    digest = sha(prog_bytes)
    if digest != PROGRAM_SHA256:
        sys.stderr.write(
            "F11_PROGRAM_DRIFT: the vendored quine no longer matches its pin.\n"
            f"  pinned: {PROGRAM_SHA256}\n  found:  {digest}\n"
            "  Every number below would be about a different program.\n"
        )
        return 4

    core = load_core()
    py = python_observations(core, prog_bytes.decode("latin-1"), BUDGET)
    zg = zig_observations(PROGRAM, BUDGET)
    zig_diffs = zig_trace_diffs(PROGRAM, BUDGET)
    py_diffs = {
        field: {
            "classic_vs_epochal": first_diff_step(py["classic"]["trace"], py["epochal"]["trace"], field),
            "classic_vs_pure_fixed": first_diff_step(py["classic"]["trace"], py["pure_fixed"]["trace"], field),
        }
        for field in TRACE_FIELDS
    }

    print(f"F11 program={PROGRAM.relative_to(ROOT)} bytes={len(prog_bytes)} sha={digest}")
    print(f"F11 budget={BUDGET} cores: python=src/malbolge_core.py zig=src/malbolge_free.zig")
    for profile in PROFILES:
        p, z = py[profile], zg[profile]
        print(
            f"  {profile:10s} py status={p['status']} steps={p['steps']} padwidth={p['padwidth']} "
            f"growth={p['growth']} out={p['stdout_len']}B sha={p['stdout_sha256'][:16]} "
            f"in={p['in_events']} frontier={p['first_addr_ge_3pow10_step']} max_addr={p['max_addr_touched']}"
        )
        print(
            f"  {'':10s} zg status={z['status']} steps={z['steps']} padwidth={z['padwidth']} "
            f"growth={z['growth']} out={z['stdout_len']}B sha={z['stdout_sha256'][:16]} "
            f"in={z['in_events']} frontier={z['first_addr_ge_3pow10_step']} max_addr={z['max_addr_touched']}"
        )

    expectations: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, measured: str) -> None:
        expectations.append((name, ok, measured))

    both = (py, zg)
    check("E1_program_pin", True, digest[:16])
    check("E2_classic_is_bounded_here",
          all(r["classic"]["status"] == "MAX_STEPS" and r["classic"]["steps"] == BUDGET for r in both),
          f"py={py['classic']['status']}@{py['classic']['steps']} zg={zg['classic']['status']}@{zg['classic']['steps']}")
    check("E3_classic_never_reaches_the_frontier_by_address",
          all(r["classic"]["first_addr_ge_3pow10_step"] is None for r in both),
          f"py={py['classic']['first_addr_ge_3pow10_step']} zg={zg['classic']['first_addr_ge_3pow10_step']}")
    check("E4_classic_reads_no_input_within_budget",
          all(not r["classic"]["in_events"] for r in both),
          f"py={len(py['classic']['in_events'])} zg={len(zg['classic']['in_events'])} `in` events")
    check("E5_pure_fixed_halts_at_9718_with_no_output",
          all(r["pure_fixed"]["status"] == "HALTED" and r["pure_fixed"]["steps"] == 9_718
              and r["pure_fixed"]["stdout_len"] == 0 for r in both),
          f"py={py['pure_fixed']['steps']} steps @ {py['pure_fixed']['stdout_len']}B "
          f"zg={zg['pure_fixed']['steps']} steps @ {zg['pure_fixed']['stdout_len']}B")
    check("E6_pure_fixed_never_widens",
          all(r["pure_fixed"]["padwidth"] == 10 and r["pure_fixed"]["growth"] == 0 for r in both),
          f"py pw={py['pure_fixed']['padwidth']} g={py['pure_fixed']['growth']} | "
          f"zg pw={zg['pure_fixed']['padwidth']} g={zg['pure_fixed']['growth']}")
    check("E7_pure_fixed_eof_is_3pow10_minus_1",
          [v for _, v in py["pure_fixed"]["in_events"]] == [59_048]
          and [v for _, v in zg["pure_fixed"]["in_events"]] == [59_048],
          f"py={py['pure_fixed']['in_events']} zg={zg['pure_fixed']['in_events']} (3**10-1 = 59048)")
    check("E8_epochal_halts_at_25729_with_3_bytes",
          all(r["epochal"]["status"] == "HALTED" and r["epochal"]["steps"] == 25_729
              and r["epochal"]["stdout_len"] == 3 for r in both),
          f"py={py['epochal']['steps']}@{py['epochal']['stdout_len']}B "
          f"zg={zg['epochal']['steps']}@{zg['epochal']['stdout_len']}B")
    check("E9_epochal_widens_once_to_padwidth_11",
          all(r["epochal"]["padwidth"] == 11 and r["epochal"]["growth"] == 1 for r in both),
          f"py pw={py['epochal']['padwidth']} g={py['epochal']['growth']} | "
          f"zg pw={zg['epochal']['padwidth']} g={zg['epochal']['growth']} | "
          f"py widen_events={py['epochal']['widen_events']}")
    check("E10_frontier_crossing_step_is_1229",
          py["epochal"]["first_addr_ge_3pow10_step"] == 1_229
          and zg["epochal"]["first_addr_ge_3pow10_step"] == 1_229,
          f"py={py['epochal']['first_addr_ge_3pow10_step']} zg={zg['epochal']['first_addr_ge_3pow10_step']}")
    check("E11_epochal_eof_is_3pow11_minus_1",
          all(r["epochal"]["in_events"] and
              all(v == 177_146 for _, v in r["epochal"]["in_events"]) for r in both),
          f"py={py['epochal']['in_events']} zg={zg['epochal']['in_events']} (3**11-1 = 177146)")
    e12 = {
        profile: first_byte_diff(py["classic"]["stdout_bytes"], py[profile]["stdout_bytes"])
        for profile in ("pure_fixed", "epochal")
    }
    check("E12_wrap_free_stdout_differs_from_byte_0",
          e12 == {"pure_fixed": 0, "epochal": 0},
          f"first differing byte index classic_vs={e12}")
    zig_step_diffs = {f: d for f, d in zig_diffs.items() if f in STEP_VALUED_FIELDS}
    zig_excluded = sorted(set(zig_diffs) - set(zig_step_diffs))
    check("E13_p1_no_difference_before_the_crossing",
          all(d["classic_vs_epochal"] is None or d["classic_vs_epochal"] >= 1_229 for d in py_diffs.values())
          and all(d["classic_vs_epochal"] is None or d["classic_vs_epochal"] >= 1_229 for d in zig_step_diffs.values()),
          f"py={ {f: d['classic_vs_epochal'] for f, d in py_diffs.items()} } "
          f"zg={ {f: d['classic_vs_epochal'] for f, d in zig_step_diffs.items()} } "
          f"excluded_non_step_fields={zig_excluded}")
    disagreements = [
        f"{profile}.{field}: py={py[profile][field]!r} zg={zg[profile][field]!r}"
        for profile in PROFILES for field in COMPARED_FIELDS if py[profile][field] != zg[profile][field]
    ]
    check("E14_cross_core_agreement_on_compared_observables",
          not disagreements,
          f"{len(COMPARED_FIELDS)} fields x 3 profiles; disagreements={disagreements or 'none'}")

    control_lines, control_ok = [], True
    for rel in CONTROLS:
        path = ROOT / rel
        if not path.is_file():
            control_ok = False
            control_lines.append(f"{rel}: ABSENT")
            continue
        cpy = python_observations(core, path.read_bytes().decode("latin-1"), BUDGET)
        czg = zig_observations(path, BUDGET)
        identical = all(
            cpy[p]["status"] == cpy["classic"]["status"]
            and cpy[p]["steps"] == cpy["classic"]["steps"]
            and cpy[p]["stdout_sha256"] == cpy["classic"]["stdout_sha256"]
            and cpy[p]["growth"] == 0
            for p in PROFILES
        )
        agrees = all(
            cpy[p]["steps"] == czg[p]["steps"] and cpy[p]["stdout_sha256"] == czg[p]["stdout_sha256"]
            for p in PROFILES
        )
        control_ok = control_ok and identical and agrees
        control_lines.append(
            f"{rel}: {cpy['classic']['steps']} steps, {cpy['classic']['stdout_len']}B, "
            f"sha {cpy['classic']['stdout_sha256'][:16]}, three profiles "
            f"{'identical' if identical else 'DIFFERENT'}, cross-core "
            f"{'agrees' if agrees else 'DISAGREES'}"
        )
    check("E15_no_crossing_controls_are_profile_independent", control_ok, "; ".join(control_lines))

    for name, ok, measured in expectations:
        print(f"F11 EXP {name}: {'MATCH' if ok else 'FALSIFIED'} ({measured})")
    falsified = [name for name, ok, _ in expectations if not ok]
    print(f"F11 EXPECTATIONS={len(expectations)} MATCH={len(expectations) - len(falsified)} "
          f"FALSIFIED={len(falsified)}")

    deltas = {p: zg[p]["max_addr_touched"] - py[p]["max_addr_touched"] for p in PROFILES}
    print(
        "F11 DISCLOSURE max_addr_touched_is_not_a_compared_observable: "
        f"zg-py delta={deltas}. The Python core updates it only inside _cell_write() "
        "(src/malbolge_core.py:156-161: highest address WRITTEN) while the Zig core "
        "updates it inside touch() (src/malbolge_free.zig:337-338: highest address "
        "READ OR WRITTEN). Same field name, different measurement rule. No gate "
        "before or after this one asserts equality on it, so nothing in this "
        "repository may cite max_addr_touched without naming the core that measured "
        "it."
    )

    verdict = "PASS" if not falsified else "FAIL"
    print(f"F11 FRONTIER_EOF_DIFFERENTIAL={verdict}")

    if args.output:
        out = args.output if args.output.is_absolute() else ROOT / args.output
        if out.exists():
            raise SystemExit(f"refusing to overwrite existing report: {out}")
        drop = ("stdout_bytes", "trace")
        report = {
            "gate": "F11",
            "program": str(PROGRAM.relative_to(ROOT)),
            "program_sha256": digest,
            "budget": BUDGET,
            "cores": {"python": "src/malbolge_core.py", "zig": "src/malbolge_free.zig"},
            "python": {p: {k: v for k, v in py[p].items() if k not in drop} for p in PROFILES},
            "zig": {p: {k: v for k, v in zg[p].items() if k not in drop} for p in PROFILES},
            "python_trace_first_diff": py_diffs,
            "zig_trace_first_diff": zig_diffs,
            "compared_fields": list(COMPARED_FIELDS),
            "expectations": [{"name": n, "ok": ok, "measured": m} for n, ok, m in expectations],
            "max_addr_delta_zg_minus_py": deltas,
            "verdict": verdict,
        }
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
