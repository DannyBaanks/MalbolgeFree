"""Motor de layout propio (M2/M3): Malbolge Classic crudo emitido por nosotros, sin LMAO.

    py -m unittest test_raw_malbolge -v        (desde malbolge-free/tools)
"""
from __future__ import annotations

import importlib.util
import random
import subprocess
import unittest
from pathlib import Path

import raw_malbolge as rm

GIT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("mal", GIT / "MALBOLGE" / "malbolge.py")
mal = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mal)
ZIG = GIT / "MALBOLGE" / "intermediate_vm_runner.exe"


def run_zig(src: str):
    p = subprocess.run([str(ZIG), "10", src.encode("latin-1").hex(), "", "300000", "0", "0", "0"],
                       capture_output=True, text=True, timeout=180)
    line = next((l for l in (p.stderr + p.stdout).splitlines() if l.startswith("RESULT")), None)
    if line is None:
        return None
    kv = dict(t.split("=", 1) for t in line.split()[1:])
    hx = kv.get("out_hex", "")
    return kv["status"], int(kv.get("steps", -1)), (b"" if hx == "-" else bytes.fromhex(hx))


class Emission(unittest.TestCase):
    def test_sample_bytes_on_oracle(self):
        rng = random.Random(20260916)
        for b in sorted(set(rng.sample(range(256), 24)) | {0, 10, 154, 165, 194, 255}):
            with self.subTest(byte=b):
                status, _, out = mal.run(rm.emit_byte(b, verify=False), b"", 300_000)
                self.assertEqual((status, out), ("HALTED", bytes([b])))

    def test_gap_bytes_use_accumulator_path(self):
        for b in (154, 164, 165, 193, 194, 208):
            with self.subTest(byte=b):
                status, _, out = mal.run(rm.emit_byte(b, verify=False), b"", 300_000)
                self.assertEqual((status, out), ("HALTED", bytes([b])))

    def test_target_never_stored_as_operand(self):
        """El byte objetivo se sintetiza: nunca aparece como operando almacenado."""
        dist, prev = rm._inline_bfs()
        for b in (10, 65, 128, 240):
            val = min((a for a in dist if a % 256 == b), key=lambda a: dist[a], default=None)
            if val is None:
                continue
            moves = rm._path(prev, val)
            self.assertNotIn(b, [v for _, v in moves], f"byte {b} almacenado")

    def test_programs_are_small(self):
        """Nuestro layout es mucho menor que el de LMAO (2069 celdas para un newline)."""
        for b in (10, 100, 200):
            self.assertLess(len(rm.emit_byte(b, verify=False)), 200)


@unittest.skipUnless(ZIG.exists(), "falta intermediate_vm_runner.exe")
class TwoEngineParity(unittest.TestCase):
    def test_sample_matches_zig(self):
        rng = random.Random(319)
        for b in sorted(set(rng.sample(range(256), 12)) | {0, 165, 255}):
            with self.subTest(byte=b):
                src = rm.emit_byte(b, verify=False)
                status, steps, out = mal.run(src, b"", 300_000)
                self.assertEqual(run_zig(src), (status, steps, out))


if __name__ == "__main__":
    unittest.main()
