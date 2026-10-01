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

TRANSLATOR = pathlib.Path(__file__).resolve().parents[2] / "Malbolge-Translator"
ORACLE_SRC = TRANSLATOR / "zig" / "src" / "parity_check.zig"
ORACLE_ENGINE = TRANSLATOR / "zig" / "src" / "engine.zig"

# The oracle is an independent Zig engine in the sibling repo (it imports
# engine.zig, never malbolge_free.zig). Both its source and its corpus are
# tracked there since 0c8a56b, so it builds from a fresh checkout and no
# .exe/wine is involved. If the sibling repo is absent, F4 cannot run at all:
# report that as NOT_DEMONSTRATED with its own exit code rather than crashing
# with a traceback that reads like a parity failure.
if not ORACLE_SRC.is_file():
    print(
        "F4_ORACLE_MISSING: {}\n"
        "  The independent oracle lives in the sibling Malbolge-Translator repo.\n"
        "  CLASSIC_COMPATIBILITY = NOT_DEMONSTRATED here (NOT a parity mismatch).\n"
        "  Clone it next to this repository, e.g.\n"
        "    git clone https://github.com/DannyBaanks/Malbolge-Translator.git".format(ORACLE_SRC),
        file=sys.stderr,
    )
    raise SystemExit(3)

# Guard against a silent false OK: the oracle embeds its own copy of the corpus
# while the runtime under test embeds ours. If the two copies ever diverge, this
# would compare different programs and could report a meaningless parity.
_translator_corpus = TRANSLATOR / "zig" / "corpus"
_diverge = []
for _mal in sorted(CORPUS.glob("*.mal")):
    _other = _translator_corpus / _mal.name
    if not _other.is_file():
        _diverge.append((_mal.name, "missing_in_translator"))
    elif _other.read_bytes() != _mal.read_bytes():
        _diverge.append((_mal.name, "bytes_differ"))
if _diverge:
    print(
        "F4_CORPUS_DIVERGENCE:\n"
        "  The runtime under test and the oracle embed different copies of the\n"
        "  corpus, so a parity verdict would be meaningless: " + repr(_diverge),
        file=sys.stderr,
    )
    raise SystemExit(4)

# The oracle under test's runtime, imported explicitly from src/ so no evidence
# copy can become authoritative by accident.
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

# Run the oracle natively. cwd must be the translator's zig/ directory because
# @embedFile resolves the corpus relative to that module root.
oracle_proc = subprocess.run(
    [
        "zig", "run", "--dep", "engine=engine",
        "-Mroot=src/parity_check.zig",
        "-Mengine=src/engine.zig",
    ],
    cwd=TRANSLATOR / "zig",
    capture_output=True,
    text=True,
    timeout=600,
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
    "oracle": "Malbolge-Translator/zig/src/parity_check.zig (native zig run)",
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
