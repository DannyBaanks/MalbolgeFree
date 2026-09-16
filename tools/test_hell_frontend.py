"""Hybrid lmao-lite slice 1: our HeLL frontends -> external LMAO -> Classic, on our two engines.

    py -m unittest test_hell_frontend -v        (from malbolge-free/tools)
"""
from __future__ import annotations

import random
import unittest

import hell_frontend as hf
import lmao_bridge as lb

try:
    lb.lmao_exe()
    HAVE_LMAO = True
except lb.BridgeError:
    HAVE_LMAO = False


@unittest.skipUnless(HAVE_LMAO, "LMAO not built (see _external/README.md)")
class TextFrontend(unittest.TestCase):
    def check(self, hell: str, stdin: bytes, expected: bytes):
        ok, lines = lb.verify(lb.assemble(hell), stdin, expected)
        self.assertTrue(ok, "\n".join(lines))

    def test_hello_world(self):
        self.check(hf.text_program(b"Hello, World!\n"), b"", b"Hello, World!\n")

    def test_every_byte_value(self):
        for start in range(0, 256, 64):
            chunk = bytes(range(start, start + 64))
            with self.subTest(start=start):
                self.check(hf.text_program(chunk), b"", chunk)

    def test_random_strings(self):
        rng = random.Random(20260913)
        for i in range(3):
            data = bytes(rng.randrange(256) for _ in range(rng.randint(1, 48)))
            with self.subTest(i=i):
                self.check(hf.text_program(data), b"", data)

    def test_empty_string_halts(self):
        self.check(hf.text_program(b""), b"", b"")


@unittest.skipUnless(HAVE_LMAO, "LMAO not built (see _external/README.md)")
class EchoFrontend(unittest.TestCase):
    def test_random_input(self):
        data = bytes(random.Random(319).randrange(256) for _ in range(32))
        ok, lines = lb.verify(lb.assemble(hf.echo_program(32)), data, data)
        self.assertTrue(ok, "\n".join(lines))

    def test_eof_gives_c2_mod_256(self):
        ok, lines = lb.verify(lb.assemble(hf.echo_program(3)), b"A", b"A\xa8\xa8")
        self.assertTrue(ok, "\n".join(lines))


@unittest.skipUnless(HAVE_LMAO, "LMAO not built (see _external/README.md)")
class Controls(unittest.TestCase):
    """The frontend's semantics must matter: broken HeLL must produce broken output."""

    def test_wrong_value_changes_output(self):
        hell = hf.text_program(b"AB").replace(f"ROT {hf.rotl(ord('B'))} ", f"ROT {hf.rotl(ord('C'))} ")
        run = lb.run_oracle(lb.assemble(hell), b"")
        self.assertEqual(run.output, b"AC")

    def test_without_r_restore_gadget_stops_working(self):
        # R_ROT re-enters at address(ROT): it encrypts the Rot/Nop cell back to Rot and runs the
        # gadget's Jmp.  Pointing at ROT (address-1) instead re-runs the gadget cell, which then
        # consumes the next stream cell (the OUT pointer) as its argument and desynchronises the
        # data stream.  Measured 2026-09-13: HALTED after 2543 steps with empty output (normal: 'AB').
        hell = hf.text_program(b"AB").replace("R_ROT", "ROT", 1)
        run = lb.run_oracle(lb.assemble(hell), b"", fuel=2_000_000)
        self.assertNotEqual((run.status, run.output), ("HALTED", b"AB"))


if __name__ == "__main__":
    unittest.main()
