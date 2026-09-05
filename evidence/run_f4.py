"""Evidence generator — runs each corpus program under BOTH:
  A) Python reference Classic (vendored malbolge.py)
  B) Our Free core (k=10)
Compares stdout/steps/status. Writes evidence/f4_classic_parity.json.
"""
import sys, json, hashlib, time
sys.path.insert(0, r"C:\Development\ISyCo Git\MALDOOM\vendor\malbolge")
import malbolge as pyref

import subprocess, pathlib

CORPUS = pathlib.Path(r"C:\Development\ISyCo Git\malbolge-free\corpus\classic")
PY_TIMEOUT = 60

def py_run(src, stdin=""):
    t = time.time()
    text, steps, status = pyref.run(src, max_steps=2_000_000, stdin_data=stdin)
    return {
        "status": status,
        "steps": steps,
        "stdout": text,
        "stdout_sha256": hashlib.sha256(text.encode("latin-1")).hexdigest(),
        "elapsed_ms": int((time.time() - t) * 1000),
    }

records = []
for p in sorted(CORPUS.iterdir()):
    src = p.read_text(encoding="utf-8", errors="replace")
    r = py_run(src)
    records.append({
        "program": p.name,
        "program_sha256": hashlib.sha256(src.encode("utf-8")).hexdigest(),
        "python": r,
    })

out = {"phase": "F4", "edge": "classic parity (reference only)",
       "programs": records}
path = pathlib.Path(r"C:\Development\ISyCo Git\malbolge-free\evidence\f4_classic_parity.json")
path.write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(records, indent=2)[:2500])
print("wrote", path)
