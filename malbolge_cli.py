"""Small product CLI for codec and deterministic witness operations."""
from __future__ import annotations

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "src"))
from classic_codec import assemble, disassemble, parity, parse_plan  # noqa: E402
import malbolge_core as core  # noqa: E402

# NOTE: there is deliberately no free_assisted profile here. The auxiliary ISA
# (opcodes 69-79, TAPE_BASE, lock_noencrypt) exists only in the Zig engine;
# this CLI drives the Python core, which implements exactly the eight Classic
# opcodes. Offering free_assisted would silently behave as free_pure, which is
# the kind of silent lie this repository exists to prevent.
PROFILES = ("classic", "free_pure")

# Exit codes are part of the product contract (documented in GUIA.md):
#   0 = the program halted normally (status HALTED)
#   1 = usage error, invalid source, or an internal failure
#   2 = the program did not halt within the step budget (status MAX_STEPS)
EXIT_OK, EXIT_ERROR, EXIT_MAX_STEPS = 0, 1, 2


def _load_source(source: str, from_file: bool) -> str:
    if from_file:
        return pathlib.Path(source).read_text(encoding="latin-1")
    return source


def _make_vm(profile: str, width: int, growth: str) -> "core.MalbolgeCore":
    if profile == "classic":
        if growth != "fixed" or width != 10:
            raise SystemExit("classic is width=10, fixed growth, 3^10 cells")
        return core.MalbolgeCore(width=10, mem_limit=3 ** 10, growth_policy="fixed")
    if profile == "free_pure":
        if growth not in ("fixed", "epochal"):
            raise SystemExit("free_pure growth is fixed or epochal")
        return core.MalbolgeCore(width=width, mem_limit=None, growth_policy=growth)
    raise SystemExit(f"unknown profile: {profile} (choose from {', '.join(PROFILES)})")


def _load_vm(vm: "core.MalbolgeCore", source: str) -> int:
    try:
        vm.load(source)
    except ValueError as err:
        print(f"INVALID SOURCE: {err}")
        return EXIT_ERROR
    except AssertionError as err:
        print(f"INVALID SOURCE: {err}")
        return EXIT_ERROR
    return -1


def cmd_run(args: argparse.Namespace) -> int:
    source = _load_source(args.source, args.file)
    stdin_data = (args.stdin or "").encode("latin-1")
    try:
        vm = _make_vm(args.profile, args.width, getattr(args, "growth", "fixed"))
    except SystemExit as err:
        print(err)
        return EXIT_ERROR
    rc = _load_vm(vm, source)
    if rc != -1:
        return rc
    res = vm.run(args.max_steps, stdin_data)
    out = res["stdout"].encode("latin-1")
    print(f"status={res['status']} steps={res['steps']} padwidth={res['padwidth']}")
    print(f"stdout[{len(out)} bytes]={out.hex()}")
    try:
        print(f"stdout_text={out.decode('utf-8')!r}")
    except UnicodeDecodeError:
        print("stdout_text=<not utf-8>")
    print(f"final a/c/d: see trace for registers (run --trace)")
    print(f"max_addr_touched={res['max_addr_touched']} max_value={res['max_value']} "
          f"growth_events={res['growth_events']}")
    return EXIT_OK if res["status"] == "HALTED" else EXIT_MAX_STEPS


def cmd_inspect(args: argparse.Namespace) -> int:
    source = _load_source(args.source, args.file)
    try:
        vm = _make_vm(args.profile, args.width, getattr(args, "growth", "fixed"))
    except SystemExit as err:
        print(err)
        return EXIT_ERROR
    rc = _load_vm(vm, source)
    if rc != -1:
        return rc
    print(f"profile={args.profile} width={vm.width} mem_limit={vm.mem_limit} "
          f"growth={vm.growth_policy} padwidth={vm.padwidth}")
    print(f"program_len={vm.program_len} initial_registers: a=0 c=0 d=0 steps=0 stdout=empty")
    shown = min(vm.program_len, args.cells)
    print(f"first {shown} cells (char -> decoded op):")
    for pos in range(shown):
        cell = vm._cell(pos)
        op = (cell + pos) % 94
        ch = chr(cell) if 33 <= cell <= 126 else "."
        print(f"  [{pos:6d}] {ch!r:4} op={op:2d}")
    if vm.program_len > shown:
        print(f"  ... ({vm.program_len - shown} more program cells)")
    print(f"frozen tail (lazy-fill period, 12 cells from program_len):")
    tail = [vm._cell(vm.program_len + k) for k in range(12)]
    print("  " + " ".join(str(v) for v in tail))
    print(f"tail repeats with period 12 from cell {vm.program_len + 12} onward")
    return EXIT_OK


OP_NAMES = {4: "jmp", 5: "out", 23: "in", 39: "rot", 40: "movd",
            62: "crazy", 68: "nop", 81: "halt"}


def cmd_trace(args: argparse.Namespace) -> int:
    source = _load_source(args.source, args.file)
    stdin_data = (args.stdin or "").encode("latin-1")
    try:
        vm = _make_vm(args.profile, args.width, getattr(args, "growth", "fixed"))
    except SystemExit as err:
        print(err)
        return EXIT_ERROR
    rc = _load_vm(vm, source)
    if rc != -1:
        return rc
    res, events = vm.trace_run(args.max_steps, stdin_data, limit=args.limit)
    print(f"status={res['status']} steps={res['steps']} padwidth={res['padwidth']}")
    shown = events if args.limit is None else events[:args.limit]
    print(f"showing {len(shown)} events of a {res['steps']}-step run "
          f"(a/c/d are accumulator/code/data registers):")
    print("  step      c      d  op  a_before  a_after  enc@")
    for ev in shown:
        name = OP_NAMES.get(ev["op"], f"nop({ev['op']})")
        enc = "-" if ev["encrypted_addr"] is None else str(ev["encrypted_addr"])
        print(f"  {ev['step']:4d} {ev['c_before']:6d} {ev['d_before']:6d} "
              f"{name:>5} {ev['a_before']:8d} {ev['a_after']:8d}  {enc}")
    if args.limit is not None and res["steps"] > len(shown):
        print(f"  ... truncated at --limit {args.limit} (run has {res['steps']} steps)")
    return EXIT_OK if res["status"] == "HALTED" else EXIT_MAX_STEPS


def main() -> int:
    parser = argparse.ArgumentParser(prog="malbolge-free")
    commands = parser.add_subparsers(dest="command", required=True)
    asm = commands.add_parser("assemble")
    asm.add_argument("plan")
    dis = commands.add_parser("disassemble")
    dis.add_argument("source")
    dis.add_argument("--file", action="store_true")
    commands.add_parser("verify")

    run_p = commands.add_parser("run", help="execute a program and report status")
    run_p.add_argument("source", help="Malbolge source text (or path with --file)")
    run_p.add_argument("--file", action="store_true")
    run_p.add_argument("--stdin", default="", help="input bytes (latin-1 text)")
    run_p.add_argument("--max-steps", type=int, default=2_000_000)
    run_p.add_argument("--profile", default="classic", choices=PROFILES)
    run_p.add_argument("--width", type=int, default=10,
                       help="starting width (free_pure only)")
    run_p.add_argument("--growth", default="fixed", choices=("fixed", "epochal"),
                       help="growth policy (free_pure only)")
    run_p.add_argument("--trace", action="store_true",
                       help="same as the trace command after running")

    ins_p = commands.add_parser("inspect", help="show machine state without running")
    ins_p.add_argument("source", help="Malbolge source text (or path with --file)")
    ins_p.add_argument("--file", action="store_true")
    ins_p.add_argument("--profile", default="classic", choices=PROFILES)
    ins_p.add_argument("--width", type=int, default=10)
    ins_p.add_argument("--cells", type=int, default=12,
                       help="how many program cells to decode")

    tr_p = commands.add_parser("trace", help="step-by-step execution trace")
    tr_p.add_argument("source", help="Malbolge source text (or path with --file)")
    tr_p.add_argument("--file", action="store_true")
    tr_p.add_argument("--stdin", default="")
    tr_p.add_argument("--max-steps", type=int, default=2_000_000)
    tr_p.add_argument("--profile", default="classic", choices=PROFILES)
    tr_p.add_argument("--width", type=int, default=10)
    tr_p.add_argument("--growth", default="fixed", choices=("fixed", "epochal"))
    tr_p.add_argument("--limit", type=int, default=40,
                      help="how many step events to print (default 40)")

    args = parser.parse_args()
    if args.command == "assemble":
        print(assemble(parse_plan(args.plan)))
        return 0
    if args.command == "disassemble":
        source = _load_source(args.source, args.file)
        items = disassemble(source)
        for item in items:
            print(f"{item.position:5d} {item.character!r:4} op={item.opcode:2d} {item.name}")
        return 0 if all(item.valid for item in items) else 1
    if args.command == "run":
        rc = cmd_run(args)
        if rc == EXIT_OK and args.trace:
            args.limit = None
            return cmd_trace(args)
        return rc
    if args.command == "inspect":
        return cmd_inspect(args)
    if args.command == "trace":
        return cmd_trace(args)
    checked, problems = parity()
    if problems:
        print(f"VERIFY FAIL {len(problems)}/{checked}")
        return 1
    print(f"VERIFY PASS {checked} positional instruction pairs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
