"""Run the M5 epochal ladder on the real VM up to a chosen width.

Usage:
    py run_ladder_scale.py 13 14 15 16        # run these rungs
    py run_ladder_scale.py --estimate 17 18 19 # print memory estimate only
    py run_ladder_scale.py --label xeon-32gb 17 18 19

Each rung runs a fresh VM from w=10, so rung N proves the whole climb
10 -> ... -> N. Results are appended to results.json next to this file.

Memory estimate: the core stores every executed cell in a hash map of
u128 -> u128 (16 + 16 bytes + 1 metadata byte). The table is reserved up
front with a power-of-two capacity, so the estimate is
next_pow2(cells / 0.8) * 33 bytes, plus the witness source (1 byte/cell).
"""
from __future__ import annotations

import argparse
import json
import platform
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RESULTS = HERE / "results.json"
ENTRY_BYTES = 2 * 16 + 1


def estimate_bytes(target: int) -> int:
    cells = 3 ** (target - 1) + 1 + 1000 + 16
    capacity = 1
    while capacity * 80 // 100 < cells:
        capacity *= 2
    return capacity * ENTRY_BYTES + cells


def total_ram_gib() -> float | None:
    try:
        if sys.platform == "win32":
            import ctypes

            class Status(ctypes.Structure):
                _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
                            ("total", ctypes.c_ulonglong)] + [
                    (name, ctypes.c_ulonglong) for name in ("a", "b", "c", "d", "e", "f")]

            status = Status()
            status.length = ctypes.sizeof(Status)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
            return round(status.total / 2 ** 30, 1)
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                return round(int(line.split()[1]) / 2 ** 20, 1)
    except Exception:
        pass
    return None


def run_rung(target: int, label: str, dense: bool) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        cfg = Path(tmp) / "ladder_cfg.zig"
        cfg.write_text(
            f"pub const target_w: u8 = {target};\npub const dense: bool = {'true' if dense else 'false'};\n",
            encoding="ascii")
        cmd = [
            "zig", "run", "-O", "ReleaseFast",
            "--dep", "malbolge_free", "--dep", "ladder_cfg",
            f"-Mroot={HERE / 'ladder_scale.zig'}",
            f"-Mmalbolge_free={ROOT / 'src' / 'malbolge_free.zig'}",
            f"-Mladder_cfg={cfg}",
        ]
        start = time.perf_counter()
        proc = subprocess.run(cmd, capture_output=True, text=True)
        seconds = time.perf_counter() - start
    text = proc.stdout + proc.stderr
    match = re.search(r"RESULT (.*)", text)
    fields = dict(kv.split("=", 1) for kv in match.group(1).split()) if match else {}
    passed = proc.returncode == 0 and fields.get("padwidth") == str(target)
    return {
        "target_w": target,
        "verdict": "PASS" if passed else "FAIL",
        "exit_code": proc.returncode,
        "seconds_including_compile": round(seconds, 1),
        "estimated_bytes": estimate_bytes(target),
        "label": label,
        "os": platform.system(),
        "processor": platform.processor() or platform.machine(),
        "ram_total_gib": total_ram_gib(),
        "fields": fields,
        "tail": text.strip().splitlines()[-3:],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("targets", nargs="+", type=int)
    parser.add_argument("--estimate", action="store_true")
    parser.add_argument("--label", default="", help="free-text machine label (no hostnames)")
    parser.add_argument("--dense", action="store_true",
                        help="use the dense u32 representation (~8x less RAM per rung)")
    args = parser.parse_args()

    for target in args.targets:
        gib = estimate_bytes(target) / 2 ** 30
        print(f"w={target}: c must reach 3^{target - 1} = {3 ** (target - 1):,}; "
              f"estimated table ~{gib:.1f} GiB")
    if args.estimate:
        return 0

    results = json.loads(RESULTS.read_text(encoding="utf-8")) if RESULTS.exists() else []
    failed = False
    for target in args.targets:
        row = run_rung(target, args.label, args.dense)
        print(json.dumps(row))
        results.append(row)
        RESULTS.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        if row["verdict"] != "PASS":
            failed = True
            break  # later rungs need more memory than a failed one
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
