"""lmao-lite M2 slice: clean-room byte synthesis -> external LMAO -> Classic, on both engines.

    py -m unittest test_hell_materialize -v        (from malbolge-free/tools)
"""
from __future__ import annotations

import random
import unittest

import hell_materialize as hm
import lmao_bridge as lb

try:
    lb.lmao_exe()
    HAVE_LMAO = True
except lb.BridgeError:
    HAVE_LMAO = False


class Synthesis(unittest.TestCase):
    def test_reachable_replays_exact(self):
        bad = [b for b in hm.reachable_bytes() if hm.replay(hm.synthesize(b)) % 256 != b]
        self.assertEqual(bad, [])

    def test_target_never_stored(self):
        viol = [b for b in hm.reachable_bytes() if b in (v for _, v in hm.synthesize(b))]
        self.assertEqual(viol, [])

    def test_coverage_is_the_measured_201(self):
        self.assertEqual(len(hm.reachable_bytes()), 201)

    def test_gap_is_154_to_208(self):
        gap = sorted(set(range(256)) - hm.reachable_bytes())
        self.assertEqual(gap, list(range(154, 209)))


@unittest.skipUnless(HAVE_LMAO, "LMAO not built (see _external/README.md)")
class EndToEnd(unittest.TestCase):
    def check(self, data: bytes):
        ok, lines = lb.verify(lb.assemble(hm.emit_hell(data)), b"", data)
        self.assertTrue(ok, "\n".join(lines))

    def test_printable_string(self):
        self.check(b"ISyCo")

    def test_control_bytes(self):
        self.check(b"\n\t\x07")

    def test_high_byte(self):
        self.check(b"\x80")

    def test_random_reachable_string(self):
        reachable = sorted(hm.reachable_bytes())
        rng = random.Random(319)
        self.check(bytes(rng.choice(reachable) for _ in range(12)))

    def test_gap_byte_raises(self):
        with self.assertRaises(ValueError):
            hm.synthesize(180)


if __name__ == "__main__":
    unittest.main()
