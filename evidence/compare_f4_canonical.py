"""F4c: byte-a-byte Classic parity of BOTH cores against independent CANONICAL oracles.

Why this exists. The previous parity gate (compare_f4.py) used
Malbolge-Translator/zig/src/engine.zig as its oracle, and that engine assigns
`(1 << 16) - 1` on end of input — the same non-canonical family as the bug the
2026-10-17 audit found. Parity against a peer that shares your bug proves
nothing, so the claim is now measured against implementations that follow the
1998 interpreter (`malbolge.c`: `if ( x == EOF ) a = 59048;`), of which two are
available locally:

  ORACLE_C  reference_interpreter_classic  — Olmstead's C, compiled natively.
  ORACLE_PY ISyCo Git/MALBOLGE/malbolge.py — independent Python, EOF_VALUE=59048.

Both oracles are optional: if neither is present the gate reports
NOT_DEMONSTRATED with exit 3, exactly like compare_f4.py's missing-oracle path.

Comparisons are on stdout BYTES only (sha256 + hex). The C oracle exposes no
step count or status, so steps are recorded from our sides but never compared.
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
CORPUS = ROOT / "corpus" / "classic"
SIBLING = ROOT.parent  # `.../ISyCo Git`

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=pathlib.Path, help="new report path (never overwritten)")
args = parser.parse_args()

CANDIDATE_C = pathlib.Path(
    SIBLING.parent / "ISyCo" / "workspace" / "assembly" / "malbolge" / "reference_interpreter_classic"
)
CANDIDATE_PY = SIBLING / "MALBOLGE" / "malbolge.py"

oracle_c = pathlib.Path(os.environ.get("MALFREE_REFERENCE_CLASSIC", CANDIDATE_C))
oracle_py = pathlib.Path(os.environ.get("MALFREE_MALBOLGE_REFERENCE", CANDIDATE_PY))

have_c = oracle_c.is_file()
have_py = oracle_py.is_file()
if not (have_c or have_py):
    print(
        "F4c_ORACLES_MISSING: neither canonical oracle is present:\n"
        "  C : {}\n  PY: {}\n"
        "  CLASSIC_PARITY_CANONICAL = NOT_DEMONSTRATED here (NOT a parity mismatch).\n"
        "  Set MALFREE_REFERENCE_CLASSIC and/or MALFREE_MALBOLGE_REFERENCE.".format(oracle_c, oracle_py),
        file=sys.stderr,
    )
    raise SystemExit(3)


def load_module(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def provenance(p: pathlib.Path) -> dict:
    # The oracles are sibling checkouts this repo does not vendor: publish a
    # root-relative path plus their SHA-256, never a machine-specific layout.
    return {
        "path": os.path.relpath(p.resolve(), ROOT).replace(os.sep, "/"),
        "sha256": sha(p.read_bytes()),
    }


# Cases: the six canonical-corpus programs on empty stdin (the EOF witness: each
# `in` there immediately hits end of input), plus one fed-input control per echo
# program proving the non-EOF path is untouched by the fix. The last entry is an
# external program (the 88-byte `Hello, world.` from the language's public
# description) — it comes from outside this repo, so it is only run when present.
EXTERNAL_HELLO = SIBLING.parent / "ISyCo" / "workspace" / "assembly" / "malbolge" / "hello_world.malbolge"

CASES = [
    {"case": "echo.mal/eof", "program": "echo.mal", "path": CORPUS / "echo.mal", "stdin": ""},
    {"case": "echo1.mal/eof", "program": "echo1.mal", "path": CORPUS / "echo1.mal", "stdin": ""},
    {"case": "echo2.mal/eof", "program": "echo2.mal", "path": CORPUS / "echo2.mal", "stdin": ""},
    {"case": "echo3.mal/eof", "program": "echo3.mal", "path": CORPUS / "echo3.mal", "stdin": ""},
    {"case": "hello.mal/eof", "program": "hello.mal", "path": CORPUS / "hello.mal", "stdin": ""},
    {"case": "reproducer.mal/eof", "program": "reproducer.mal", "path": CORPUS / "reproducer.mal", "stdin": ""},
    {"case": "echo.mal/fed_A", "program": "echo.mal", "path": CORPUS / "echo.mal", "stdin": "A"},
    {"case": "echo1.mal/fed_A", "program": "echo1.mal", "path": CORPUS / "echo1.mal", "stdin": "A"},
    {"case": "echo2.mal/fed_AB", "program": "echo2.mal", "path": CORPUS / "echo2.mal", "stdin": "AB"},
    {"case": "echo3.mal/fed_ABC", "program": "echo3.mal", "path": CORPUS / "echo3.mal", "stdin": "ABC"},
]
if EXTERNAL_HELLO.is_file():
    CASES.append({"case": "external_hello_world/eof", "program": EXTERNAL_HELLO.name,
                  "path": EXTERNAL_HELLO, "stdin": ""})

# --- our Zig core, through evidence/run_f4c.zig --------------------------------
manifest = ROOT / "evidence" / "_f4c_cases.tsv"
lines = ["{}\t{}\t{}".format(c["case"], c["path"], c["stdin"]) for c in CASES]
manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
zig_proc = subprocess.run(
    ["zig", "run", "--dep", "malbolge_free=malbolge_free",
     "-Mroot=evidence/run_f4c.zig",
     "-Mmalbolge_free=src/malbolge_free.zig",
     "--", str(manifest)],
    cwd=ROOT, capture_output=True, text=True, timeout=600,
)
if zig_proc.returncode != 0:
    raise RuntimeError(zig_proc.stderr or zig_proc.stdout)
zig_rows = {}
for line in zig_proc.stderr.splitlines():
    if not line.startswith("case="):
        continue
    head, _, hexpart = line.partition("stdout_hex=[")
    fields = dict(tok.split("=", 1) for tok in head.split() if "=" in tok)
    body, _, _ = hexpart.partition("]")
    zig_rows[fields["case"]] = {
        "status": fields["status"], "steps": int(fields["steps"]),
        "stdout_sha256": fields["sha256"], "stdout_hex": body,
    }
manifest.unlink()

# --- our Python core ----------------------------------------------------------
core = load_module(ROOT / "src" / "malbolge_core.py", "mb_core")
py_rows = {}
for c in CASES:
    src = c["path"].read_text(encoding="utf-8")
    vm = core.MalbolgeCore(width=10, mem_limit=3 ** 10, growth_policy="fixed")
    vm.load(src)
    res = vm.run(2_000_000, stdin_data=c["stdin"].encode("latin-1"))
    out = res["stdout"].encode("latin-1")
    py_rows[c["case"]] = {
        "status": res["status"], "steps": res["steps"],
        "stdout_sha256": sha(out), "stdout_hex": out.hex(),
    }

# --- canonical oracles --------------------------------------------------------
ref_c_rows = {}
if have_c:
    for c in CASES:
        proc = subprocess.run(
            [str(oracle_c), str(c["path"])],
            input=c["stdin"].encode("latin-1"),
            capture_output=True, timeout=120,
        )
        if proc.returncode != 0:
            raise RuntimeError("oracle C failed on {}: {}".format(c["case"], proc.stderr))
        ref_c_rows[c["case"]] = {
            "status": "HALTED", "steps": None,
            "stdout_sha256": sha(proc.stdout), "stdout_hex": proc.stdout.hex(),
        }

ref_py_rows = {}
if have_py:
    refpy = load_module(oracle_py, "malbolge_canonical_reference")
    for c in CASES:
        src = c["path"].read_text(encoding="utf-8")
        status, steps, out = refpy.run(src, stdin_data=c["stdin"].encode("latin-1"), max_steps=2_000_000)
        ref_py_rows[c["case"]] = {
            "status": status, "steps": steps,
            "stdout_sha256": sha(out), "stdout_hex": out.hex(),
        }

# --- verdicts ----------------------------------------------------------------
references = ({"canonical_c_olmstead": ref_c_rows} if have_c else {}) | (
    {"canonical_python_malbolge_py": ref_py_rows} if have_py else {})

verdicts = []
all_match = True
for c in CASES:
    for side, rows in (("zig", zig_rows), ("python", py_rows)):
        per_ref = {}
        for ref_name, ref_rows in references.items():
            expected = ref_rows.get(c["case"])
            match = expected is not None and rows[c["case"]]["stdout_sha256"] == expected["stdout_sha256"]
            per_ref[ref_name] = {"expected": expected, "match": match}
            all_match &= match
        verdicts.append({
            "case": c["case"], "program": c["program"], "stdin": c["stdin"],
            "side": side, "runtime": rows[c["case"]], "references": per_ref,
        })

report = {
    "phase": "F4c",
    "claim": "CLASSIC_PARITY_CANONICAL",
    "runtime": {"zig": "src/malbolge_free.zig", "python": "src/malbolge_core.py"},
    "oracles": {
        "canonical_c_olmstead": provenance(oracle_c) if have_c else None,
        "canonical_python_malbolge_py": provenance(oracle_py) if have_py else None,
    },
    "eof_convention": "in on end of input assigns 3**w - 1 (59048 at w=10); out truncates to 0xa8",
    "cases": len(CASES),
    "comparisons": len(verdicts),
    "all_match": all_match,
    "verdicts": verdicts,
}
if args.output:
    output = args.output if args.output.is_absolute() else ROOT / args.output
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing report: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
print("\n=>", "PASS" if all_match else "MISMATCH", flush=True)
raise SystemExit(0 if all_match else 1)
