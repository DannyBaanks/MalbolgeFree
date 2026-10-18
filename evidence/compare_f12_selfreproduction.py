#!/usr/bin/env python3
"""F12 — the vendored quine reproduces itself byte for byte, to completion, on both cores.

F11 runs the frontier differential under a bounded budget and therefore does NOT
test whether `classic` finishes. This gate does: it lets the program halt on its
own, at a budget far above the halt point, and compares what it prints against a
known answer that this repository did not produce.

The known answer is external and public
--------------------------------------
`DannyBaanks/Malbolge-MB-Database:quine/evidence/quine_53562_verification.json`
(2026-10-17) records three engines reproducing this program byte-for-byte: the
database's own native runner, BolgeForge's `mb_ref`, and
`quine/evidence/mb_classic_indep.c` — a Classic interpreter written clean-room
from the published specification and shipped with the evidence. All three report
`HALTED` after 62 239 852 steps with stdout equal to the program itself. The same
bytes are published as `DannyBaanks/BolgeForge@5a55b9b:artifacts/candidate_m281_53562b.mal`.

So the expectations below are not "our two cores agree with each other" — that
would be self-referential — they are "our two cores agree with an answer
measured by engines that share no code with this repository". The parity gates
(F4c) already say that on 10 small cases; this says it on a 53 562-byte,
62-million-step self-reproducing program.

Pre-registered expectations (2026-10-18, from a full-budget pilot on this machine
against both cores; they test portability of the measurement, not its discovery):

   K1  program sha256 == the sha published by MB-Database           (integrity, rc 4)
   K2  zig  classic: HALTED, 62 239 852 steps, stdout == program bytes
   K3  python classic: HALTED, 62 239 852 steps, stdout == program bytes
   K4  the two cores agree with each other on status, steps, padwidth, growth and stdout hash
   K5  the step count equals the externally published count (agreement with engines outside this repo)
   K6  the wrap-free profiles still do not reproduce it: pure_fixed 0 bytes, epochal 3 bytes
   K7  `source_eq_stdout` is true for classic and false for the other two, in the same run

Cost, stated up front: the Classic halt is ~63 s on the Zig core and ~51 s on the
Python core as measured on Linux on 2026-10-18, so this is the slow gate in the
suite and `tests/run_all.py` gives it its own timeout instead of the default 180 s.

Read-only: prints a verdict, writes nothing unless --output names a NEW path.
Exit codes follow verdicts: 0 all met, 1 falsified, 4 integrity or driver
failure. No exit 3: the input is in the repository.
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
# Pinned to the bytes as published, not to a local path.
PROGRAM_SHA256 = "96b670b825372a0f41fa3b574d47457f92654b76411e5d5be4c438003087610e"
PROGRAM_CITATIONS = (
    "DannyBaanks/Malbolge-MB-Database:quine/quine_53562_m281.mb",
    "DannyBaanks/BolgeForge@5a55b9b:artifacts/candidate_m281_53562b.mal",
)
EXTERNAL_STEPS = 62_239_852     # MB-Database verification JSON: all three engines
EXTERNAL_STDOUT_LEN = 53_562    # the program's own size: self-reproduction
TRACE_BUDGET = int(os.environ.get("MALFREE_F12_TRACE_BUDGET", 2_000))
STDOUT_BUDGET = int(os.environ.get("MALFREE_F12_STDOUT_BUDGET", 200_000_000))
CORE_BUDGET = int(os.environ.get("MALFREE_F12_CORE_BUDGET", 200_000_000))


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_core():
    spec = importlib.util.spec_from_file_location("mb_core", ROOT / "src" / "malbolge_core.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def zig_full_run(program_path: pathlib.Path) -> dict:
    """Pass 1 keeps only TRACE_BUDGET steps of traces (a 62 M-step trace would be
    gigabytes); pass 2 runs every profile to completion without tracing."""
    proc = subprocess.run(
        ["zig", "run", "--dep", "malbolge_free=malbolge_free",
         "-Mroot=evidence/run_quine_epochal.zig", "-Mmalbolge_free=src/malbolge_free.zig",
         "--", str(program_path), str(TRACE_BUDGET), str(STDOUT_BUDGET)],
        cwd=ROOT, capture_output=True, text=True, timeout=7200,
    )
    if proc.returncode != 0:
        sys.stderr.write(f"F12_DRIVER_FAILURE rc={proc.returncode}\n")
        sys.stderr.write((proc.stderr or proc.stdout)[-4000:])
        raise SystemExit(4)
    rows = {}
    # Pass 2 rows are the last ones printed per profile, and they are the rows
    # that ran to completion, so overwriting pass-1 rows is the point.
    for line in proc.stderr.splitlines():
        if not line.startswith("RUN prof="):
            continue
        parts = dict(tok.split("=", 1) for tok in line.split() if "=" in tok)
        rows[parts["prof"]] = {
            "status": parts["status"],
            "steps": int(parts["steps"]),
            "padwidth": int(parts["padwidth"]),
            "growth": int(parts["growth_events"]),
            "stdout_len": int(parts["stdout_len"]),
            "stdout_sha256": parts["stdout_sha"],
            "source_eq_stdout": parts["source_eq_stdout"] == "true",
        }
    missing = [p for p in ("classic", "pure_fixed", "epochal") if p not in rows]
    if missing:
        sys.stderr.write(f"F12_DRIVER_INCOMPLETE missing profiles {missing}\n")
        raise SystemExit(4)
    return rows


def python_full_run(core, program_text: str) -> dict:
    rows = {}
    for profile, kwargs in (
        ("classic", dict(width=10, mem_limit=3 ** 10, growth_policy="fixed")),
        ("pure_fixed", dict(width=10, mem_limit=None, growth_policy="fixed")),
        ("epochal", dict(width=10, mem_limit=None, growth_policy="epochal")),
    ):
        vm = core.MalbolgeCore(**kwargs)
        vm.load(program_text)
        res = vm.run(max_steps=CORE_BUDGET, stdin_data=b"")
        out = res["stdout"].encode("latin-1")
        rows[profile] = {
            "status": res["status"],
            "steps": res["steps"],
            "padwidth": res["padwidth"],
            "growth": res["growth_events"],
            "stdout_len": len(out),
            "stdout_sha256": sha(out),
            "source_eq_stdout": out == program_text.encode("latin-1"),
        }
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=pathlib.Path,
                        help="write the measurement JSON to this NEW path")
    args = parser.parse_args()

    if not PROGRAM.is_file():
        sys.stderr.write(f"F12_PROGRAM_ABSENT {PROGRAM}\n")
        return 4
    prog_bytes = PROGRAM.read_bytes()
    digest = sha(prog_bytes)
    if digest != PROGRAM_SHA256:
        sys.stderr.write(
            "F12_PROGRAM_DRIFT: the vendored quine no longer matches its pin.\n"
            f"  pinned: {PROGRAM_SHA256}\n  found:  {digest}\n"
            "  The published record this gate compares against is a different file.\n"
        )
        return 4

    import time
    core = load_core()
    program_text = prog_bytes.decode("latin-1")

    t0 = time.monotonic()
    zg = zig_full_run(PROGRAM)
    zig_secs = round(time.monotonic() - t0, 1)
    t0 = time.monotonic()
    py = python_full_run(core, program_text)
    py_secs = round(time.monotonic() - t0, 1)

    print(f"F12 program={PROGRAM.relative_to(ROOT)} bytes={len(prog_bytes)} sha={digest}")
    print(f"F12 cited_as_published_to={' and '.join(PROGRAM_CITATIONS)}")
    print(f"F12 budgets zig_trace={TRACE_BUDGET} zig_stdout={STDOUT_BUDGET} python={CORE_BUDGET}")
    print(f"F12 measured_wall_seconds zig={zig_secs} python={py_secs}")
    for profile in ("classic", "pure_fixed", "epochal"):
        z, p = zg[profile], py[profile]
        print(
            f"  {profile:10s} zg status={z['status']} steps={z['steps']} pw={z['padwidth']} "
            f"g={z['growth']} out={z['stdout_len']}B sha={z['stdout_sha256'][:16]} eq={z['source_eq_stdout']}"
        )
        print(
            f"  {'':10s} py status={p['status']} steps={p['steps']} pw={p['padwidth']} "
            f"g={p['growth']} out={p['stdout_len']}B sha={p['stdout_sha256'][:16]} eq={p['source_eq_stdout']}"
        )

    expectations: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, measured: str) -> None:
        expectations.append((name, ok, measured))

    check("K1_program_pin_is_the_published_record", True, digest[:16])
    check("K2_zig_classic_halts_reproducing_the_program",
          zg["classic"]["status"] == "HALTED" and zg["classic"]["source_eq_stdout"]
          and zg["classic"]["stdout_len"] == EXTERNAL_STDOUT_LEN,
          f"status={zg['classic']['status']} steps={zg['classic']['steps']} "
          f"out={zg['classic']['stdout_len']}B eq={zg['classic']['source_eq_stdout']}")
    check("K3_python_classic_halts_reproducing_the_program",
          py["classic"]["status"] == "HALTED" and py["classic"]["source_eq_stdout"]
          and py["classic"]["stdout_len"] == EXTERNAL_STDOUT_LEN,
          f"status={py['classic']['status']} steps={py['classic']['steps']} "
          f"out={py['classic']['stdout_len']}B eq={py['classic']['source_eq_stdout']}")
    compared = ("status", "steps", "padwidth", "growth", "stdout_len", "stdout_sha256",
                "source_eq_stdout")
    disagreements = [
        f"{profile}.{field}: zg={zg[profile][field]!r} py={py[profile][field]!r}"
        for profile in ("classic", "pure_fixed", "epochal")
        for field in compared if zg[profile][field] != py[profile][field]
    ]
    check("K4_cross_core_agreement", not disagreements,
          f"{len(compared)} fields x 3 profiles; disagreements={disagreements or 'none'}")
    check("K5_step_count_matches_the_external_engines",
          zg["classic"]["steps"] == EXTERNAL_STEPS and py["classic"]["steps"] == EXTERNAL_STEPS,
          f"zg={zg['classic']['steps']} py={py['classic']['steps']} external={EXTERNAL_STEPS} "
          "(MB-Database 2026-10-17: native runner, mb_ref, mb_classic_indep.c)")
    check("K6_wrap_free_profiles_do_not_reproduce",
          zg["pure_fixed"]["stdout_len"] == 0 and zg["epochal"]["stdout_len"] == 3
          and not zg["pure_fixed"]["source_eq_stdout"] and not zg["epochal"]["source_eq_stdout"],
          f"zg pure_fixed={zg['pure_fixed']['stdout_len']}B epochal={zg['epochal']['stdout_len']}B")
    check("K7_source_eq_stdout_selects_only_classic",
          zg["classic"]["source_eq_stdout"] and not zg["pure_fixed"]["source_eq_stdout"]
          and not zg["epochal"]["source_eq_stdout"],
          f"classic={zg['classic']['source_eq_stdout']} pure_fixed={zg['pure_fixed']['source_eq_stdout']} "
          f"epochal={zg['epochal']['source_eq_stdout']}")

    for name, ok, measured in expectations:
        print(f"F12 EXP {name}: {'MATCH' if ok else 'FALSIFIED'} ({measured})")
    falsified = [name for name, ok, _ in expectations if not ok]
    print(f"F12 EXPECTATIONS={len(expectations)} MATCH={len(expectations) - len(falsified)} "
          f"FALSIFIED={len(falsified)}")

    scope_lines = [
        "proves: this repository's two cores reach a known answer published by three engines "
        "outside it, on a 53 562-byte self-reproducing Classic program",
        "does NOT prove: that epochal can reproduce a quine (F11 shows it emits 3 bytes here, "
        "and F10 shows the same on a third-party quine)",
        "does NOT prove: smallest-quine or any ranking claim; those live in MB-Database with "
        "its enumerated-universe sweep",
        "byte-exact self-reproduction is asserted about stdout bytes only; max_addr_touched is "
        "not compared (the two cores measure it by different rules, see F11's disclosure)",
    ]
    for line in scope_lines:
        print(f"F12 SCOPE {line}")

    verdict = "PASS" if not falsified else "FAIL"
    print(f"F12 SELF_REPRODUCTION_KNOWN_ANSWER={verdict}")

    if args.output:
        out = args.output if args.output.is_absolute() else ROOT / args.output
        if out.exists():
            raise SystemExit(f"refusing to overwrite existing report: {out}")
        report = {
            "gate": "F12",
            "program": str(PROGRAM.relative_to(ROOT)),
            "program_sha256": digest,
            "cited_as_published_to": list(PROGRAM_CITATIONS),
            "budgets": {"zig_trace": TRACE_BUDGET, "zig_stdout": STDOUT_BUDGET, "python": CORE_BUDGET},
            "measured_wall_seconds": {"zig": zig_secs, "python": py_secs},
            "zig": zg,
            "python": py,
            "external_known_answer": {"steps": EXTERNAL_STEPS, "stdout_len": EXTERNAL_STDOUT_LEN},
            "compared_fields": list(compared),
            "expectations": [{"name": n, "ok": ok, "measured": m} for n, ok, m in expectations],
            "scope": scope_lines,
            "verdict": verdict,
        }
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
