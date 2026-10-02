"""Product CLI smoke tests: run/inspect/trace with exit-code contract.

Runs malbolge_cli.py as a subprocess (the way a user would) on both OSes.
Exit codes are part of the product contract, see GUIA.md:
  0 = halted / inspection worked, 1 = usage/invalid source, 2 = MAX_STEPS.
"""
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLI = [sys.executable, str(ROOT / "malbolge_cli.py")]
HELLO = str(ROOT / "corpus" / "classic" / "hello.mal")


def cli(*argv):
    return subprocess.run(
        [*CLI, *argv], cwd=ROOT, capture_output=True, text=True, timeout=300,
    )


class CliProductTests(unittest.TestCase):
    def test_run_hello_halts_with_output(self):
        p = cli("run", "--file", HELLO)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("status=HALTED steps=40", p.stdout)
        self.assertIn("48656c6c6f20576f726c6421", p.stdout)

    def test_run_max_steps_is_exit_2(self):
        p = cli("run", "ubO", "--max-steps", "1")
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertIn("status=MAX_STEPS", p.stdout)

    def test_run_invalid_source_is_exit_1(self):
        p = cli("run", "a")
        self.assertEqual(p.returncode, 1, p.stderr)
        self.assertIn("INVALID SOURCE", p.stdout)

    def test_inspect_shows_state(self):
        p = cli("inspect", "ubO")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("program_len=3", p.stdout)
        self.assertIn("op=23", p.stdout)

    def test_trace_shows_steps(self):
        p = cli("trace", "ubO", "--limit", "2")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("status=HALTED steps=3", p.stdout)
        self.assertIn("a_before", p.stdout)

    def test_no_free_assisted_profile(self):
        # Deliberate product decision: the Python core has no auxiliary ISA,
        # so offering free_assisted would silently behave as free_pure.
        p = cli("run", "ubO", "--profile", "free_assisted")
        self.assertNotEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
