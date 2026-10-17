"""F4c: byte-a-byte Classic parity of BOTH cores against independent CANONICAL oracles.

Why this exists. The previous parity gate (compare_f4.py) used
Malbolge-Translator/zig/src/engine.zig as its oracle, and that engine assigns
`(1 << 16) - 1` on end of input — the same non-canonical family as the bug the
2026-10-17 audit found. Parity against a peer that shares your bug proves
nothing, so the claim is now measured against implementations that follow the
1998 interpreter (`malbolge.c`: `if ( x == EOF ) a = 59048;`), of which two are
available locally:

  ORACLE_C    reference_interpreter_classic — Olmstead's C, compiled natively.
              External, so it is used when reachable or when MALFREE_REFERENCE_CLASSIC
              points at it; without it the claim rests on the Python oracle alone.
  ORACLE_PY   vendor/canonical_malbolge_py/malbolge.py — canonical Python
              (EOF_VALUE=59048), vendored verbatim so a fresh clone can MEASURE this
              parity instead of skipping it. Its SHA-256 is pinned below: a drift is
              exit 4, never a PASS, because a silently edited oracle is exactly what
              kept the EOF bug green for a month.

With no usable oracle at all the gate reports NOT_DEMONSTRATED with exit 3, like
compare_f4.py's missing-oracle path.

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

VENDORED_PY = ROOT / "vendor" / "canonical_malbolge_py" / "malbolge.py"
VENDORED_PY_SHA256 = "e64af4f0d51712e99fdf205e1a102587e4e52c863302384b5d2599f6edf3222b"
VENDORED_PY_SOURCE = "github.com/DannyBaanks/MALBOLGE@bf4d6fa (malbolge.py, MIT)"

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=pathlib.Path, help="new report path (never overwritten)")
args = parser.parse_args()


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def use_vendored_py() -> bool:
    if not VENDORED_PY.is_file():
        return False
    digest = sha(VENDORED_PY.read_bytes())
    if digest != VENDORED_PY_SHA256:
        print(
            "F4C_VENDORED_ORACLE_DRIFT: {}\n"
            "  pinned: {}\n  found:  {}\n"
            "  The vendored canonical oracle no longer matches the copy described in\n"
            "  vendor/canonical_malbolge_py/PROVENANCE.md. Parity measured against it\n"
            "  would be meaningless, so this is a hard failure — not a skip, not a PASS.\n"
            "  Restore the verbatim copy, or re-vendor deliberately and update the pin\n"
            "  plus PROVENANCE.md (source commit and hash).".format(VENDORED_PY, VENDORED_PY_SHA256, digest),
            file=sys.stderr,
        )
        raise SystemExit(4)
    return True


CANDIDATE_C = pathlib.Path(
    SIBLING.parent / "ISyCo" / "workspace" / "assembly" / "malbolge" / "reference_interpreter_classic"
)

oracle_c = pathlib.Path(os.environ.get("MALFREE_REFERENCE_CLASSIC", CANDIDATE_C))
have_c = oracle_c.is_file() and os.access(oracle_c, os.X_OK)
vendored_py_used = use_vendored_py()
# An externally supplied interpreter is an ADDITIONAL oracle, never a replacement:
# the pinned vendored copy is what CI and a fresh clone actually measure against.
oracle_py_env = pathlib.Path(os.environ["MALFREE_MALBOLGE_REFERENCE"]) if "MALFREE_MALBOLGE_REFERENCE" in os.environ else None
have_py_env = bool(oracle_py_env and oracle_py_env.is_file())

if not (have_c or vendored_py_used or have_py_env):
    print(
        "F4c_ORACLES_MISSING: no canonical oracle is usable:\n"
        "  C        : {} ({})\n  vendored PY: {}{}\n  MALFREE_MALBOLGE_REFERENCE: {}\n"
        "  CLASSIC_PARITY_CANONICAL = NOT_DEMONSTRATED here (NOT a parity mismatch).\n"
        "  Restore vendor/canonical_malbolge_py/malbolge.py or set MALFREE_REFERENCE_CLASSIC.".format(
            oracle_c,
            "present" if oracle_c.is_file() else "absent",
            VENDORED_PY,
            "" if VENDORED_PY.is_file() else " (absent)",
            oracle_py_env if oracle_py_env else "unset",
        ),
        file=sys.stderr,
    )
    raise SystemExit(3)


def load_module(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def provenance(p: pathlib.Path, **extra) -> dict:
    # Publish a root-relative path plus the oracle's SHA-256, never a
    # machine-specific layout: the identity that matters is the hash.
    info = {
        "path": os.path.relpath(p.resolve(), ROOT).replace(os.sep, "/"),
        "sha256": sha(p.read_bytes()),
    }
    info.update(extra)
    return info


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

def run_python_oracle(path: pathlib.Path, module_name: str) -> dict:
    mod = load_module(path, module_name)
    rows = {}
    for c in CASES:
        src = c["path"].read_text(encoding="utf-8")
        status, steps, out = mod.run(src, stdin_data=c["stdin"].encode("latin-1"), max_steps=2_000_000)
        rows[c["case"]] = {
            "status": status, "steps": steps,
            "stdout_sha256": sha(out), "stdout_hex": out.hex(),
        }
    return rows


python_oracles = {}
if vendored_py_used:
    python_oracles["canonical_python_vendored"] = (
        run_python_oracle(VENDORED_PY, "malbolge_canonical_vendored"),
        provenance(VENDORED_PY, pinned_sha256=VENDORED_PY_SHA256, source=VENDORED_PY_SOURCE),
    )
if have_py_env:
    python_oracles["canonical_python_external"] = (
        run_python_oracle(oracle_py_env, "malbolge_canonical_external"),
        provenance(oracle_py_env, pinned_sha256=None),
    )

# --- verdicts ----------------------------------------------------------------
references = ({"canonical_c_olmstead": ref_c_rows} if have_c else {}) | {
    name: rows for name, (rows, _meta) in python_oracles.items()}

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
    "format": "f4c-canonical-parity/2",
    "claim": "CLASSIC_PARITY_CANONICAL",
    "runtime": {"zig": "src/malbolge_free.zig", "python": "src/malbolge_core.py"},
    "oracles": (
        {"canonical_c_olmstead": provenance(oracle_c, pinned_sha256=None)} if have_c else {}
    ) | {name: meta for name, (_rows, meta) in python_oracles.items()},
    "eof_convention": "in on end of input assigns 3**w - 1 (59048 at w=10); out truncates to 0xa8",
    # Counted explicitly so a verdict can never be vacuous: `verdicts` is
    # cases x cores, `hash_comparisons` is that times the oracles actually used.
    "cases": len(CASES),
    "cores": 2,
    "oracles_used": len(references),
    "verdicts": len(verdicts),
    "hash_comparisons": len(verdicts) * len(references),
    "all_match": all_match and len(references) > 0,
    "verdicts_detail": verdicts,
}
if args.output:
    output = args.output if args.output.is_absolute() else ROOT / args.output
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing report: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
verdict = "PASS" if report["all_match"] else "MISMATCH"
print("\n=>", verdict, "({} cases x 2 cores x {} oracle(s) = {} stdout-hash comparisons)".format(
    report["cases"], report["oracles_used"], report["hash_comparisons"]), flush=True)
raise SystemExit(0 if report["all_match"] else 1)
