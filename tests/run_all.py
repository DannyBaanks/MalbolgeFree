"""M2 reproducible test harness for Malbolge Free."""
from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def safe_print(text: str) -> None:
    """Print arbitrary subprocess output on any console encoding.

    Zig test names may contain non-ASCII characters (e.g. arrows). The
    Windows console (cp1252) cannot encode them, so escape them instead
    of crashing the whole harness run.
    """
    enc = sys.stdout.encoding or "utf-8"
    sys.stdout.write(text.encode(enc, errors="backslashreplace").decode(enc) + "\n")


def zig_test(path: str) -> list[str]:
    return [
        "zig",
        "test",
        "--dep",
        "malbolge_free=malbolge_free",
        f"-Mroot={ROOT / path}",
        f"-Mmalbolge_free={ROOT / 'src' / 'malbolge_free.zig'}",
    ]


def zig_test_hell(path: str) -> list[str]:
    return [
        "zig",
        "test",
        "--dep",
        "hell=hell",
        "--dep",
        "malbolge_free=malbolge_free",
        f"-Mroot={ROOT / path}",
        f"-Mhell={ROOT / 'src' / 'hell.zig'}",
        f"-Mmalbolge_free={ROOT / 'src' / 'malbolge_free.zig'}",
    ]


def zig_run(path: str) -> list[str]:
    return [
        "zig",
        "run",
        "--dep",
        "malbolge_free=malbolge_free",
        f"-Mroot={ROOT / path}",
        f"-Mmalbolge_free={ROOT / 'src' / 'malbolge_free.zig'}",
    ]


GATES = [
    ("Classic codec unit tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_classic_codec.py", "-v"]),
    ("constructive assembler unit tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_constructive_assembler.py", "-v"]),
    ("product CLI verify", [sys.executable, str(ROOT / "malbolge_cli.py"), "verify"]),
    ("F4 Classic parity", [sys.executable, str(ROOT / "evidence" / "compare_f4.py")]),
    ("M2 Classic trace differential", [sys.executable, str(ROOT / "evidence" / "compare_m2.py")]),
    ("M1 numeric and EOF", zig_test("tests/t_m1_contract.zig")),
    ("negative contracts", zig_test("tests/t_negative.zig")),
    ("execution profiles", zig_test("tests/t_profiles.zig")),
    ("explicit unshackled k19 profile", zig_test("tests/t_unshackled_k19.zig")),
    ("conservative epochal extension", zig_test("tests/t_m4_conservative.zig")),
    ("repeated frontier 10 to 12", zig_test("tests/t_m5_repeated.zig")),
    ("repeated frontier 10 to 12 (full VM)", zig_test("tests/t_m5_full_vm.zig")),
    ("E10 to E19 toy epoch ladder unit tests", [sys.executable, "-m", "unittest", "discover", "-s", "epoch_ladder", "-p", "test_*epoch_ladder.py", "-v"]),
    ("E11 to E18 preregistered offset gates", [sys.executable, str(ROOT / "epoch_ladder" / "offset_epoch_ladder.py"), "run"]),
    ("M6 BF reference semantics", zig_test("tests/t_m6_bf_reference.zig")),
    ("M6 BF to IR translator", zig_test("tests/t_m6_bf_to_ir.zig")),
    ("M6 IR differential VM", zig_test("tests/t_m6_bf_ir_vm.zig")),
    ("M6 IR image payload", zig_test("tests/t_m6_bf_ir_image.zig")),
    ("M6 BFIR1 VM", zig_test("tests/t_m6_bf_image_vm.zig")),
    ("M6 Hello World compiler oracle", zig_test("tests/t_m6_bf_hello_oracle.zig")),
    ("M7 Uroboros seed determinism", zig_test("tests/t_m7_uroboros_seed.zig")),
    ("M6.2 Malbolge I/O primitive control", zig_test("tests/t_m6_malbolge_primitives.zig")),
    ("M6.2a Malbolge payload relay", zig_test("tests/t_m6_2a_payload_relay.zig")),
    ("A1 HeLL parser (lmao-lite)", [
        "zig", "test", "--dep", "hell=hell",
        f"-Mroot={ROOT / 'tests' / 't_a1_hell_parser.zig'}",
        f"-Mhell={ROOT / 'src' / 'hell.zig'}",
    ]),
    ("A2 opcode table (lmao-lite)", [
        "zig", "test", "--dep", "hell=hell",
        f"-Mroot={ROOT / 'tests' / 't_a2_opcode_table.zig'}",
        f"-Mhell={ROOT / 'src' / 'hell.zig'}",
    ]),
    ("A3 labels/layout (lmao-lite)", [
        "zig", "test", "--dep", "hell=hell",
        f"-Mroot={ROOT / 'tests' / 't_a3_layout.zig'}",
        f"-Mhell={ROOT / 'src' / 'hell.zig'}",
    ]),
    ("A4 emission (lmao-lite)", [
        "zig", "test", "--dep", "hell=hell", "--dep", "malbolge_free=malbolge_free",
        f"-Mroot={ROOT / 'tests' / 't_a4_emit.zig'}",
        f"-Mhell={ROOT / 'src' / 'hell.zig'}",
        f"-Mmalbolge_free={ROOT / 'src' / 'malbolge_free.zig'}",
    ]),
    ("A6 multi-byte cat (lmao-lite)", [
        "zig", "test", "--dep", "hell=hell",
        f"-Mroot={ROOT / 'tests' / 't_a6_cat.zig'}",
        f"-Mhell={ROOT / 'src' / 'hell.zig'}",
    ]),
    ("A7 BFIR1 backend", [
        "zig", "test", "--dep", "backend=backend", "--dep", "hell=hell", "--dep", "malbolge_free=malbolge_free",
        f"-Mroot={ROOT / 'tests' / 't_a7_bfir1_backend.zig'}",
        f"-Mbackend={ROOT / 'src' / 'bfir1_backend.zig'}",
        f"-Mhell={ROOT / 'src' / 'hell.zig'}",
        f"-Mmalbolge_free={ROOT / 'src' / 'malbolge_free.zig'}",
    ]),
    ("A7 conditional scaffold", [
        "zig", "test", "--dep", "backend=backend", "--dep", "hell=hell", "--dep", "malbolge_free=malbolge_free",
        f"-Mroot={ROOT / 'tests' / 't_a7_conditional.zig'}",
        f"-Mbackend={ROOT / 'src' / 'bfir1_backend.zig'}",
        f"-Mhell={ROOT / 'src' / 'hell.zig'}",
        f"-Mmalbolge_free={ROOT / 'src' / 'malbolge_free.zig'}",
    ]),
    ("READ_D_0 + JMP_A opcodes", zig_test_hell("tests/t_read_d_0.zig")),
    ("TAPE-V0 runtime zero", zig_test_hell("tests/t_tape_v0.zig")),
    ("TAPE-V1 addressed re-reads", zig_test_hell("tests/t_tape_v1.zig")),
    ("CHASE branch gadget (real VM)", zig_test_hell("tests/t_branch_gadget_zig.zig")),
    ("M6.2 vertical slice", [
        "zig", "test", "--dep", "backend=backend", "--dep", "hell=hell", "--dep", "malbolge_free=malbolge_free",
        f"-Mroot={ROOT / 'tests' / 't_m62_vertical_slice.zig'}",
        f"-Mbackend={ROOT / 'src' / 'bfir1_backend.zig'}",
        f"-Mhell={ROOT / 'src' / 'hell.zig'}",
        f"-Mmalbolge_free={ROOT / 'src' / 'malbolge_free.zig'}",
    ]),
    ("M6.2 differential (3 images)", [
        "zig", "test", "--dep", "backend=backend", "--dep", "hell=hell", "--dep", "malbolge_free=malbolge_free",
        f"-Mroot={ROOT / 'tests' / 't_m62_differential.zig'}",
        f"-Mbackend={ROOT / 'src' / 'bfir1_backend.zig'}",
        f"-Mhell={ROOT / 'src' / 'hell.zig'}",
        f"-Mmalbolge_free={ROOT / 'src' / 'malbolge_free.zig'}",
    ]),
    ("M6.3 input echo + EOF", [
        "zig", "test", "--dep", "backend=backend", "--dep", "hell=hell", "--dep", "malbolge_free=malbolge_free",
        f"-Mroot={ROOT / 'tests' / 't_m63_input.zig'}",
        f"-Mbackend={ROOT / 'src' / 'bfir1_backend.zig'}",
        f"-Mhell={ROOT / 'src' / 'hell.zig'}",
        f"-Mmalbolge_free={ROOT / 'src' / 'malbolge_free.zig'}",
    ]),
    ("M6.4 branches (loop differential)", [
        "zig", "test", "--dep", "backend=backend", "--dep", "hell=hell", "--dep", "malbolge_free=malbolge_free",
        f"-Mroot={ROOT / 'tests' / 't_m64_branch.zig'}",
        f"-Mbackend={ROOT / 'src' / 'bfir1_backend.zig'}",
        f"-Mhell={ROOT / 'src' / 'hell.zig'}",
        f"-Mmalbolge_free={ROOT / 'src' / 'malbolge_free.zig'}",
    ]),
    ("M6.5 full differential (5 programs)", [
        "zig", "test", "--dep", "backend=backend", "--dep", "hell=hell", "--dep", "malbolge_free=malbolge_free",
        f"-Mroot={ROOT / 'tests' / 't_m65_differential.zig'}",
        f"-Mbackend={ROOT / 'src' / 'bfir1_backend.zig'}",
        f"-Mhell={ROOT / 'src' / 'hell.zig'}",
        f"-Mmalbolge_free={ROOT / 'src' / 'malbolge_free.zig'}",
    ]),
    ("epochal invariants", zig_test("tests/t_epochal.zig")),
    ("frontier 10 to 12", zig_run("tests/t_frontier_moment.zig")),
]


def main() -> int:
    failures = 0
    for name, command in GATES:
        print(f"\n== {name} ==")
        print("$ " + " ".join(str(part) for part in command))
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        output = completed.stdout + completed.stderr
        safe_print(output.rstrip())
        if completed.returncode != 0:
            failures += 1
            print(f"FAIL: {name} (exit {completed.returncode})")
        else:
            print(f"PASS: {name}")

    print(f"\nM2/M4/M5/M6-infra verdict: {'PASS' if failures == 0 else 'FAIL'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
