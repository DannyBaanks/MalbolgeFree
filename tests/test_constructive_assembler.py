import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
from classic_codec import disassemble
from constructive_assembler import build


class ConstructiveAssemblerTests(unittest.TestCase):
    def test_plan_is_deterministic_and_positionally_valid(self):
        source = build("in,out,rot,movd,opr,nop,end")
        self.assertEqual(source, build("in,out,rot,movd,opr,nop,end"))
        self.assertEqual([23, 5, 39, 40, 62, 68, 81], [item.opcode for item in disassemble(source)])


if __name__ == "__main__":
    unittest.main()
