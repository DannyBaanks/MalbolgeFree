#!/usr/bin/env python3
"""M2 bootstrap reachability: which A values / output bytes are reachable from the seed via Rot/Opr."""
from __future__ import annotations

import collections
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GIT = HERE.parents[2]
PRE = json.loads((HERE / "PREREGISTRATION.json").read_text(encoding="utf-8"))

_spec = importlib.util.spec_from_file_location("mal", GIT / "MALBOLGE" / "malbolge.py")
mal = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mal)
crazy, rot = mal.crazy, lambda v: v // 3 + (v % 3) * 3 ** 9
OPS = {4, 5, 23, 39, 40, 62, 68, 81}
SEED = 29524


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_valid(value: int) -> bool:
    """Can `value` sit in a data cell at some position and pass the Classic loader?"""
    if not 33 <= value <= 126:
        return False
    return any((value + pos) % 94 in OPS for pos in range(94))


def bfs(bank: frozenset[int], max_depth: int):
    """Shortest op-sequence (rot / opr_k) from SEED to each reachable A, bounded by depth."""
    dist = {SEED: 0}
    prev = {SEED: None}
    q = collections.deque([SEED])
    while q:
        a = q.popleft()
        if dist[a] >= max_depth:
            continue
        nxt = [("rot", rot(a))] + [(("opr", k), crazy(a, k)) for k in bank]
        for move, b in nxt:
            if b not in dist:
                dist[b] = dist[a] + 1
                prev[b] = (a, move)
                q.append(b)
    return dist, prev


def main() -> int:
    max_depth = 14
    # bootstrap fixpoint of the operand bank
    bank = frozenset({SEED})
    for _ in range(8):
        dist, _ = bfs(bank, max_depth)
        grown = frozenset(bank | {v for v in dist if load_valid(v)})
        if grown == bank:
            break
        bank = grown
    dist, prev = bfs(bank, max_depth)

    residues = {}
    for a, d in dist.items():
        r = a % 256
        if r not in residues or d < residues[r]:
            residues[r] = d
    reachable_bytes = sorted(residues)
    missing = [b for b in range(256) if b not in residues]

    def seq_for(target_value: int):
        chain, a = [], target_value
        while prev[a] is not None:
            pa, move = prev[a]
            chain.append(move)
            a = pa
        return list(reversed(chain))

    report = {
        "preregistration_sha256": sha256(HERE / "PREREGISTRATION.json"),
        "seed": SEED, "max_depth": max_depth,
        "operand_bank_size": len(bank),
        "operand_bank_sample": sorted(bank)[:20],
        "values_reachable": len(dist),
        "bytes_reachable": len(reachable_bytes),
        "bytes_missing": missing,
        "byte_min_ops_histogram": dict(collections.Counter(residues.values())),
        "example_sequences": {},
    }
    for t in PRE["targets"]:
        val = next((a for a in dist if a % 256 == t), None)
        report["example_sequences"][t] = {
            "reachable": val is not None,
            "value": val,
            "ops": seq_for(val) if val is not None else None,
        }
    report["verdicts"] = {
        "BOOTSTRAP_ALL_BYTES_REACHABLE": "DEMONSTRATED" if not missing
        else f"PARTIAL {len(reachable_bytes)}/256 (missing {len(missing)})"
    }
    (HERE / "REACH_RESULTS.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in
                      ("operand_bank_size", "values_reachable", "bytes_reachable",
                       "byte_min_ops_histogram", "verdicts")}, indent=1))
    print("missing bytes:", missing)
    return 0


if __name__ == "__main__":
    sys.exit(main())
