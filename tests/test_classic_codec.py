import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from classic_codec import MEMORY_SIZE, OPCODES, assemble, decode, disassemble, encode, parity


class ClassicCodecTests(unittest.TestCase):
    def test_exhaustive_positional_parity(self):
        checked, problems = parity()
        self.assertEqual(8 * MEMORY_SIZE, checked)
        self.assertEqual([], problems)

    def test_toy_program(self):
        source = assemble([23, 5, 39, 40, 62, 68, 81])
        items = disassemble(source)
        self.assertEqual([23, 5, 39, 40, 62, 68, 81], [item.opcode for item in items])

    def test_invalid_opcode_is_visible(self):
        item = disassemble(encode(0, 0))[0]
        self.assertFalse(item.valid)


if __name__ == "__main__":
    unittest.main()
