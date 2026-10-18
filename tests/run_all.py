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
    # Parity is measured against CANONICAL oracles (Olmstead's C interpreter and
    # MALBOLGE/malbolge.py, both `a = 3**10-1` at EOF). The former F4 gate used
    # Malbolge-Translator/zig/src/engine.zig, which assigns 0xFFFF at EOF: a peer
    # that shares a convention cannot falsify it. compare_f4.py is kept as the
    # measurement of that divergence and is no longer a gate; see
    # evidence/f4_engine_zig_divergence_20261017.json and HONESTY_LEDGER entry 24.
    ("F4c canonical Classic parity", [sys.executable, str(ROOT / "evidence" / "compare_f4_canonical.py")]),
    ("M2 Classic trace differential", [sys.executable, str(ROOT / "evidence" / "compare_m2.py")]),
    ("EPOCHAL Python parity differential", [sys.executable, str(ROOT / "evidence" / "compare_epochal.py")]),
    # F11/F12 read the vendored corpus/classic/quine_m281.mal, so unlike F10 they
    # need no sibling checkout: their exit-3 (NOT_DEMONSTRATED) branch is
    # unreachable from a fresh clone, which is what lets the frontier/EOF and
    # self-reproduction claims be affirmed by CI rather than by one machine.
    # F12 halts the real 62 239 852-step program on both cores (~115 s measured on
    # Linux), so it carries an explicit timeout instead of the 180 s default.
    ("F11 epochal frontier and width-relative EOF differential", [sys.executable, str(ROOT / "evidence" / "compare_f11_frontier_eof.py")], 600),
    ("F12 Classic self-reproduction known answer (both cores)", [sys.executable, str(ROOT / "evidence" / "compare_f12_selfreproduction.py")], 900),
    # F13 compares the fixed-3^19 profile against a localized *deterministic*
    # third-party reference (MalbolgeLispSlop's bolge19 + profiles/fixed19.json),
    # which is deliberately not vendored here: its own notices say
    # "copy-and-revalidate, never import", so vendoring is a licensing decision.
    # Absent that sibling checkout the gate exits 3 and the harness prints the
    # explicit NOT_DEMONSTRATED skip -- which is what CI shows until the decision
    # is made. Locally it is measured, not skipped. See
    # docs/F13_UNSHACKLED_K19_PREGISTRATION.md and HONESTY_LEDGER entry 39.
    ("F13 deterministic fixed-3^19 parity differential", [sys.executable, str(ROOT / "evidence" / "compare_unshackled_k19.py")], 300),
    # F14 measures the regional dispatch divergence V1 (+117 in Region 1, +140 in
    # Region 2) against the same reference: formula sampling across 150 000 pairs
    # and execution jumps reaching Region 1. Exits 3 if the reference is absent.
    # See docs/F14_REGION_OFFSETS_V1_PREGISTRATION.md and HONESTY_LEDGER entry 40.
    ("F14 region 1 and 2 dispatch divergence (V1)", [sys.executable, str(ROOT / "evidence" / "compare_f14_region_offsets.py")], 300),
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
    ("M7 compiler image guard (no crash on malformed)", zig_test("tests/t_m7_compiler_image_guard.zig")),
    ("M7 tape width (capacity, not semantics)", [
        "zig", "test", "--dep", "hell=hell", "--dep", "malbolge_free=malbolge_free",
        f"-Mroot={ROOT / 'tests' / 't_m7_tape_width.zig'}",
        f"-Mhell={ROOT / 'src' / 'hell.zig'}",
        f"-Mmalbolge_free={ROOT / 'src' / 'malbolge_free.zig'}",
    ]),
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
    ("M6 eight-opcode boundary (bounded negative + control)", [
        "zig", "test", "--dep", "hell=hell", "--dep", "malbolge_free=malbolge_free",
        f"-Mroot={ROOT / 'tests' / 't_m6_eight_opcode_boundary.zig'}",
        f"-Mhell={ROOT / 'src' / 'hell.zig'}",
        f"-Mmalbolge_free={ROOT / 'src' / 'malbolge_free.zig'}",
    ]),
    ("product CLI run/inspect/trace", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_cli_product.py", "-v"]),
    ("M0 EOF and numeric precision", zig_test("tests/t_m0_eof_precision.zig")),
    ("M0 free-pure vertical slice (8 opcodes only)", [
        "zig", "test", "--dep", "hell=hell", "--dep", "malbolge_free=malbolge_free",
        f"-Mroot={ROOT / 'tests' / 't_free_pure_vertical_slice.zig'}",
        f"-Mhell={ROOT / 'src' / 'hell.zig'}",
        f"-Mmalbolge_free={ROOT / 'src' / 'malbolge_free.zig'}",
    ]),
    ("dense representation differential", zig_test("tests/t_dense_differential.zig")),
    ("epochal invariants", zig_test("tests/t_epochal.zig")),
    ("frontier 10 to 12", zig_run("tests/t_frontier_moment.zig")),
    # S1 seal gate: SHA256SUMS.txt is a claim about the published bytes, and
    # until now only the sealing machine ever checked it. This makes the seal a
    # per-run measurement on every runner, in Python because Windows runners
    # have no `sha256sum`. Integrity failure -> exit 4, which the loop below
    # counts as FAIL; exit 3 is unreachable (there is no external input to miss).
    ("S1 seal manifest (SHA256SUMS.txt)", [sys.executable, str(ROOT / "evidence" / "verify_seal_manifest.py")]),
]


def main() -> int:
    failures = 0
    skipped: list[str] = []
    for entry in GATES:
        name, command = entry[:2]
        # A gate may carry a third element: its own timeout in seconds. The 180 s
        # default fits everything that does not halt a real Classic program.
        timeout = entry[2] if len(entry) > 2 else 180
        print(f"\n== {name} ==")
        print("$ " + " ".join(str(part) for part in command))
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        output = completed.stdout + completed.stderr
        safe_print(output.rstrip())
        # Exit code 3 from a checker means "required external input is absent",
        # not "the machine is wrong". Report it as an explicit NOT_DEMONSTRATED
        # skip: counted, printed, and visible in the summary line.
        if completed.returncode == 3:
            skipped.append(name)
            print(f"SKIP (NOT_DEMONSTRATED, missing external input): {name}")
        elif completed.returncode == 4:
            # Exit 4 is reserved for integrity failures: corpus divergence
            # between runtime and oracle (F4c) or a seal that does not match the
            # bytes on disk (S1). A verdict resting on either would be
            # meaningless, so this is a hard failure, never a skip.
            failures += 1
            print(f"FAIL: {name} (integrity failure, exit 4)")
        elif completed.returncode != 0:
            failures += 1
            print(f"FAIL: {name} (exit {completed.returncode})")
        else:
            print(f"PASS: {name}")

    verdict = "PASS" if failures == 0 else "FAIL"
    print(f"\nM2/M4/M5/M6-infra verdict: {verdict}")
    if skipped:
        print(
            "NOT_DEMONSTRATED in this environment ({} gate(s)): {}".format(
                len(skipped), "; ".join(skipped)
            )
        )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
