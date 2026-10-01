"""F4: independent Zig oracle vs the canonical Malbolge Free runtime."""
import argparse
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "corpus" / "classic"

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=pathlib.Path, help="optional new report path")
args = parser.parse_args()

_oracle_path = pathlib.Path(__file__).resolve().parents[2] / "Malbolge-Translator" / "zig" / "parity_check.exe"
_oracle = str(_oracle_path)

# The oracle is a local build artifact of the sibling Malbolge-Translator repo and
# is NOT tracked in git (neither is its source zig/src/parity_check.zig). A fresh
# checkout therefore does not contain it. Report that as an explicit
# NOT_DEMONSTRATED condition with its own exit code instead of crashing with a
# traceback that looks like a parity failure. Checked BEFORE the zig run so a
# missing oracle does not first burn a full compile.
if not _oracle_path.exists():
    print(
        "F4_ORACLE_MISSING: {}\n"
        "  The independent Zig oracle is an untracked build artifact of the\n"
        "  Malbolge-Translator repo. CLASSIC_COMPATIBILITY = NOT_DEMONSTRATED in this\n"
        "  environment (NOT a parity mismatch). To run F4, build or place\n"
        "  parity_check.exe there; see ROADMAP M2/M3.".format(_oracle),
        file=sys.stderr,
    )
    raise SystemExit(3)

# The oracle lives outside this repository. The runtime under test is imported
# explicitly from src/ so no evidence copy can become authoritative by accident.
zig_proc = subprocess.run(
    [
        "zig", "run", "--dep", "malbolge_free=malbolge_free",
        "-Mroot=evidence/run_f4.zig",
        "-Mmalbolge_free=src/malbolge_free.zig",
    ],
    cwd=ROOT,
    capture_output=True,
    text=True,
    timeout=600,
)
if zig_proc.returncode != 0:
    raise RuntimeError(zig_proc.stderr or zig_proc.stdout)

try:
    oracle_proc = subprocess.run(
        [_oracle],
        capture_output=True,
        text=True,
        timeout=60,
    )
except OSError:
    # On Linux the oracle is a Windows PE; fall back to wine.
    try:
        oracle_proc = subprocess.run(
            ["wine", _oracle],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except OSError as wine_err:
        raise RuntimeError(
            "oracle exists but neither native nor wine execution works: {}".format(wine_err)
        )
if oracle_proc.returncode != 0:
    raise RuntimeError(oracle_proc.stderr or oracle_proc.stdout)

oracle_rows = json.loads(oracle_proc.stderr.strip())
oracle = {row["program"]: row for row in oracle_rows}

runtime_rows = {}
runtime_output = zig_proc.stdout or zig_proc.stderr
for line in runtime_output.splitlines():
    line = line.strip()
    if not line.startswith("program="):
        continue
    parts = dict(token.split("=", 1) for token in line.split() if "=" in token)
    runtime_rows[parts["program"]] = {
        "status": parts["status"],
        "steps": int(parts["steps"]),
        "stdout_sha256": parts.get("sha256") or parts.get("stdout_sha256"),
    }

verdicts = []
all_match = True
for name in sorted(oracle):
    expected = oracle[name]
    actual = runtime_rows.get(name)
    match = actual is not None and all(
        expected[key] == actual[key]
        for key in ("status", "steps", "stdout_sha256")
    )
    verdicts.append({
        "program": name,
        "match": match,
        "reference": expected,
        "runtime": actual,
    })
    all_match &= match

report = {
    "phase": "F4",
    "claim": "CLASSIC_COMPATIBILITY",
    "oracle": "Malbolge-Translator/zig/parity_check.exe",
    "runtime": "src/malbolge_free.zig",
    "all_match": all_match,
    "verdicts": verdicts,
}
if args.output:
    output = args.output if args.output.is_absolute() else ROOT / args.output
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing report: {output}")
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
print("\n=>", "PASS" if all_match else "MISMATCH")
