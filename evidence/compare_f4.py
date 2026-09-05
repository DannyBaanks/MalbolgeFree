"""F4 r1 complete: compare Python reference vs Zig core on the corpus."""
import sys, json, hashlib, subprocess, pathlib

ROOT = pathlib.Path(r"C:\Development\ISyCo Git\malbolge-free")
sys.path.insert(0, r"C:\Development\ISyCo Git\MALDOOM\vendor\malbolge")
import malbolge as pyref

CORPUS = ROOT / "corpus" / "classic"

# Reference: Python
py_rows = {}
for f in sorted(CORPUS.iterdir()):
    src = f.read_text(encoding="utf-8")
    text, steps, status = pyref.run(src, max_steps=2_000_000, stdin_data="")
    py_rows[f.name] = {
        "status": status, "steps": steps,
        "stdout_sha256": hashlib.sha256(text.encode("latin-1")).hexdigest(),
    }

# Zig: gen + run
zig_proc = subprocess.run(
    ["zig", "run", "evidence/run_f4.zig"],
    cwd=ROOT, capture_output=True, text=True, timeout=600,
)
zig_out = zig_proc.stderr if not zig_proc.stdout else zig_proc.stdout
zig_rows = {}
for line in zig_out.splitlines():
    line = line.strip()
    if not line.startswith("program="):
        continue
    parts = {}
    for tok in line.split(" "):
        if "=" in tok:
            k, v = tok.split("=", 1)
            parts[k] = v
    zig_rows[parts["program"]] = {
        "status": parts.get("status"),
        "steps": int(parts["steps"]),
        "stdout_sha256": parts.get("stdout_sha256") or parts.get("sha256"),
    }

# Compare
verdicts = []
all_match = True
for name in sorted(py_rows.keys()):
    p = py_rows[name]
    z = zig_rows.get(name)
    if z is None:
        verdicts.append({"program": name, "match": False, "note": "missing in zig run"})
        all_match = False
        continue
    # Classic run in pyref uses -1 EOF sentinel; ours uses 0xFF. Adjust stdout sentinel:
    # Step 1: the bytewise output where sentinel would show up.
    ref_stdout = pyref.run((CORPUS/name).read_text(encoding="utf-8"), max_steps=2_000_000)[0]
    ref_bytes = [(ord(ch) & 0xFF) for ch in ref_stdout]
    if ref_stdout:
        # -1 in pyref comes from EOF → repr is '\uFFFD' if we encoded? Let's reconstruct from the raw repr:
        if any(ord(ch) < 0 for ch in ref_stdout):
            pass
        # compare against zig's raw
    match = (p["status"] == z["status"] and
             p["steps"] == z["steps"] and
             p["stdout_sha256"] == z["stdout_sha256"])
    verdicts.append({"program": name, "match": match,
                     "python": p, "zig": z})
    if not match:
        all_match = False

report = {
    "phase": "F4",
    "claim": "CLASSIC_COMPATIBILITY",
    "all_match": all_match,
    "verdicts": verdicts,
    "zig_stderr_tail": zig_proc.stderr[-400:] if zig_proc.stderr else None,
}
out_path = ROOT / "evidence" / "f4_classic_parity.json"
out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2)[:3000])
print("\n=>", "PASS" if all_match else "MISMATCH")
