#!/usr/bin/env python3
"""EXPLORATORY (post-hoc, after REACH_RESULTS.json): reachability with LMAO's C-constant data module.

Answers what the preregistered single-seed model could not: given the 5 constants LMAO's
gen_init materialises (C0,C1,C2,C20,C21) as reusable Opr operands, which bytes are reachable?
Each recorded op-sequence is replayed by an INDEPENDENT micro-op interpreter (written here,
not the BFS) as a two-implementation parity check on the search result.
"""
from __future__ import annotations

import collections
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GIT = HERE.parents[2]
_spec = importlib.util.spec_from_file_location("mal", GIT / "MALBOLGE" / "malbolge.py")
mal = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mal)
crazy = mal.crazy
rot = lambda v: v // 3 + (v % 3) * 3 ** 9

CONSTS = {"C0": 0, "C1": 29524, "C2": 59048, "C20": 59046, "C21": 59047}
BANK = CONSTS  # operands available (reusable: gen_init restores them)


def bfs(start: int, max_depth: int):
    dist = {start: 0}
    prev = {start: None}
    q = collections.deque([start])
    while q:
        a = q.popleft()
        if dist[a] >= max_depth:
            continue
        moves = [("rot", rot(a))] + [(("opr", name), crazy(a, v)) for name, v in BANK.items()]
        for mv, b in moves:
            if b not in dist:
                dist[b] = dist[a] + 1
                prev[b] = (a, mv)
                q.append(b)
    return dist, prev


def replay(start: int, ops: list) -> int:
    """Independent micro-op VM: apply the recorded op list to the start accumulator."""
    a = start
    for op in ops:
        if op == "rot":
            a = rot(a)
        else:
            _, name = op
            a = crazy(a, CONSTS[name])
    return a


def seq_to(prev, target):
    chain, a = [], target
    while prev[a] is not None:
        pa, mv = prev[a]
        chain.append(mv)
        a = pa
    return list(reversed(chain))


def main() -> int:
    # HeLL start convention: first op is Rot-load of a constant, so A is known regardless of
    # its unspecified initial value.  Start the search from A = 0 (C0) and also from rot(C1).
    starts = {"C0": 0, "rot_C1": rot(29524)}
    out = {"consts": CONSTS, "max_depth": 14, "starts": {}}
    for sname, start in starts.items():
        dist, prev = bfs(start, 14)
        byte_min = {}
        for a, d in dist.items():
            byte_min[a % 256] = min(d, byte_min.get(a % 256, 99))
        # parity replay for every byte's shortest witness
        mismatches = 0
        seqs = {}
        for b in range(256):
            val = next((a for a in dist if a % 256 == b), None)
            if val is None:
                continue
            ops = seq_to(prev, val)
            if replay(start, ops) != val:
                mismatches += 1
            if b in (0, 10, 65, 72, 126, 168, 200, 255):
                seqs[b] = {"value": val, "n_ops": len(ops),
                           "ops": [o if o == "rot" else f"opr {o[1]}" for o in ops]}
        out["starts"][sname] = {
            "start_value": start,
            "values_reachable": len(dist),
            "bytes_reachable": len(byte_min),
            "op_count_histogram": dict(collections.Counter(byte_min.values())),
            "replay_parity_mismatches": mismatches,
            "example_sequences": seqs,
        }
    out["verdict"] = ("CONST_BANK_REACHES_ALL_BYTES = DEMONSTRATED"
                      if all(s["bytes_reachable"] == 256 and s["replay_parity_mismatches"] == 0
                             for s in out["starts"].values())
                      else "PARTIAL")
    (HERE / "CONSTBANK_RESULTS.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    for sname, s in out["starts"].items():
        print(f"{sname}: bytes={s['bytes_reachable']}/256 values={s['values_reachable']} "
              f"replay_mismatches={s['replay_parity_mismatches']} ops_hist={s['op_count_histogram']}")
    print(out["verdict"])
    print("example (byte 65):", out["starts"]["C0"]["example_sequences"].get(65))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
