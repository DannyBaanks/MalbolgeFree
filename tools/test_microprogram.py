"""M4 — microprogramas propios sobre Malbolge Classic (sin LMAO, sin HeLL, sin gen_init).

    py -m unittest test_microprogram -v        (desde malbolge-free/tools)
"""
from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import unittest
from pathlib import Path

import microprogram as mp
import raw_malbolge as rm

GIT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("mal", GIT / "MALBOLGE" / "malbolge.py")
mal = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mal)
ZIG = GIT / "MALBOLGE" / "intermediate_vm_runner.exe"

ECHO = [("in",), ("out_acc",), ("halt",)]
COMPOSED = [("out", 0x3e), ("in",), ("out_acc",), ("jmp", "done"), ("out", 0x58),
            ("label", "done"), ("out", 0x0a), ("halt",)]


def run(src, stdin=b""):
    return mal.run(src, stdin, 500_000)


def run_zig(src, stdin=b""):
    p = subprocess.run([str(ZIG), "10", src.encode("latin-1").hex(), stdin.hex(),
                        "500000", "0", "0", "0"], capture_output=True, text=True, timeout=300)
    line = next((l for l in (p.stderr + p.stdout).splitlines() if l.startswith("RESULT")), None)
    kv = dict(t.split("=", 1) for t in line.split()[1:])
    hx = kv.get("out_hex", "")
    return kv["status"], int(kv.get("steps", -1)), (b"" if hx == "-" else bytes.fromhex(hx))


class Regression(unittest.TestCase):
    def test_m3_byte_synthesis_still_works(self):
        """M4 no puede romper M3."""
        for b in (0, 10, 65, 154, 165, 194, 255):
            with self.subTest(byte=b):
                status, _, out = run(rm.emit_byte(b, verify=False))
                self.assertEqual((status, out), ("HALTED", bytes([b])))


class Sequence(unittest.TestCase):
    def test_arbitrary_sequences(self):
        for data in [b"A", b"AB", b"HI\n", bytes([0, 255, 127]), b">A\n", b"nada"]:
            with self.subTest(data=data):
                src = mp.emit_program([("out", b) for b in data] + [("halt",)])
                status, _, out = run(src)
                self.assertEqual((status, out), ("HALTED", data))

    def test_growth_is_linear_not_explosive(self):
        sizes = []
        for n in (1, 4, 8):
            src = mp.emit_program([("out", 65)] * n + [("halt",)])
            sizes.append(len(src))
        self.assertLess(sizes[2] - sizes[1], 40)     # ~3 celdas por byte, no miles


class Input(unittest.TestCase):
    def test_roundtrip(self):
        src = mp.emit_program(ECHO)
        for byte in (0x00, 0x41, 0x7f, 0xff):
            with self.subTest(byte=byte):
                status, _, out = run(src, bytes([byte]))
                self.assertEqual((status, out), ("HALTED", bytes([byte])))

    def test_eof_is_c2_mod_256(self):
        status, _, out = run(mp.emit_program(ECHO), b"")
        self.assertEqual((status, out), ("HALTED", bytes([mp.EOF_BYTE])))


class State(unittest.TestCase):
    def test_input_survives_and_transforms(self):
        """Un byte leído sobrevive como estado y se transforma antes de salir."""
        p = mp.MicroProgram()
        p.read()
        v = mp.valid_values(p.d)[0]
        p.opr_op(v)
        p.out()
        p.halt()
        src = p.source()
        for byte in (0x00, 0x41, 0xff, 0x7a):
            with self.subTest(byte=byte):
                status, _, out = run(src, bytes([byte]))
                self.assertEqual((status, out), ("HALTED", bytes([mal.crazy(byte, v) % 256])))


class Jump(unittest.TestCase):
    def test_unreachable_trap_never_runs(self):
        src = mp.emit_program([("out", 0x41), ("jmp", "done"), ("out", 0x58),
                               ("label", "done"), ("out", 0x42), ("halt",)])
        status, _, out = run(src)
        self.assertEqual((status, out), ("HALTED", b"AB"))
        self.assertNotIn(b"X", out)

    def test_jump_breaks_the_linear_offset(self):
        """El invariante d = c + 40 es local: tras saltar el desplazamiento cambia."""
        p = mp.MicroProgram()
        p.out_const(0x41)
        before = p.d - p.c
        p.jmp(max(t for t in p.jump_targets() if t > max(p.cells)))
        self.assertEqual(before, mp.D0)
        self.assertNotEqual(p.d - p.c, mp.D0)


class Composed(unittest.TestCase):
    def test_microprogram(self):
        src = mp.emit_program(COMPOSED)
        for inp in (b"A", b"\x00", b"z", b"\xff"):
            with self.subTest(inp=inp):
                status, _, out = run(src, inp)
                self.assertEqual((status, out), ("HALTED", b">" + inp + b"\n"))

    def test_deterministic_source(self):
        first = mp.emit_program(COMPOSED)
        for _ in range(4):
            self.assertEqual(mp.emit_program(COMPOSED), first)


@unittest.skipUnless(ZIG.exists(), "falta intermediate_vm_runner.exe")
class CrossEngine(unittest.TestCase):
    def test_parity_on_every_milestone(self):
        cases = [(mp.emit_program([("out", b) for b in b"HI\n"] + [("halt",)]), b""),
                 (mp.emit_program(ECHO), b"A"),
                 (mp.emit_program(COMPOSED), b"z")]
        for src, stdin in cases:
            with self.subTest(stdin=stdin):
                self.assertEqual(run_zig(src, stdin), run(src, stdin))


if __name__ == "__main__":
    unittest.main()
