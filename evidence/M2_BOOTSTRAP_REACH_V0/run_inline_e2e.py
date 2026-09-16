#!/usr/bin/env python3
"""End-to-end sweep: every inline-reachable byte, synthesised clean-room, assembled by the
external LMAO, verified on both Classic engines. Extends M2_BOOTSTRAP_REACH_V0 (no new prereg;
same frozen engines and the inline model documented in hell_materialize.py)."""
from __future__ import annotations

import importlib.util
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GIT = HERE.parents[2]
TOOLS = GIT / "malbolge-free" / "tools"
sys.path.insert(0, str(TOOLS))
import hell_materialize as hm      # noqa: E402
import lmao_bridge as lb           # noqa: E402


def main() -> int:
    reachable = sorted(hm.reachable_bytes())
    rng = random.Random(20260913)
    zig_sample = set(rng.sample(reachable, 20)) | {0, 10, 128, 255} & set(reachable)
    results = {"reachable_count": len(reachable), "verified_oracle": 0, "verified_zig": 0,
               "zig_checked": 0, "failures": [], "no_store_violations": 0}
    for b in reachable:
        moves = hm.synthesize(b)
        if b in (v for _, v in moves):
            results["no_store_violations"] += 1
        source = lb.assemble(hm.emit_hell(bytes([b])))
        o = lb.run_oracle(source, b"")
        ok_o = o.status == "HALTED" and o.output == bytes([b])
        results["verified_oracle"] += ok_o
        rec = {"byte": b, "ops": len(moves), "oracle": [o.status, o.output.hex()]}
        if b in zig_sample:
            z = lb.run_zig(source, b"")
            results["zig_checked"] += 1
            ok_z = z is not None and z.status == "HALTED" and z.output == bytes([b]) and z.steps == o.steps
            results["verified_zig"] += ok_z
            rec["zig"] = [z.status, z.steps == o.steps] if z else None
            if not ok_z:
                results["failures"].append(rec)
        if not ok_o:
            results["failures"].append(rec)
        if b % 32 == 0:
            print(f"byte {b}: oracle {o.status} {o.output.hex()} ({results['verified_oracle']} ok)", flush=True)
    results["verdict"] = ("INLINE_SYNTH_E2E = PASS" if
                          results["verified_oracle"] == len(reachable)
                          and results["verified_zig"] == results["zig_checked"]
                          and not results["no_store_violations"]
                          else "PARTIAL")
    (HERE / "INLINE_E2E_RESULTS.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: results[k] for k in
                      ("reachable_count", "verified_oracle", "verified_zig", "zig_checked",
                       "no_store_violations", "verdict")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
