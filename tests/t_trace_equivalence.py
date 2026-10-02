"""trace_run() must be observationally identical to run().

The sink parameter added to MalbolgeCore.run only appends to a list, so in
theory it cannot change machine state. This file proves it in practice instead
of trusting the theory: same programs, same inputs, same summaries, plus
structural checks on the events themselves.
"""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_core():
    spec = importlib.util.spec_from_file_location(
        "mb_core_trace", ROOT / "src" / "malbolge_core.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def build_witness(length: int) -> str:
    out = []
    for pos in range(length):
        for cv in range(33, 127):
            if (cv + pos) % 94 in (5, 23, 62, 68):
                out.append(chr(cv))
                break
    return "".join(out)


CASES = [
    # (name, source, stdin, max_steps, width, mem_limit, policy)
    ("tiny_echo", "ubO", b"", 500, 10, 3 ** 10, "fixed"),
    ("echo_input", "ubO", b"Hi", 500, 10, 3 ** 10, "fixed"),
    ("hello", "(=<`#9]~6ZY32Vx/4Rs+0No-&Jk)\"Fh}|Bcy?`=*z]Kw%oG4UUS0/@-ejc(:'8dc",
     b"", 2000, 10, 3 ** 10, "fixed"),
    ("epochal_crossing", build_witness(300), b"", 300, 3, None, "epochal"),
    ("epochal_w10", build_witness(60000), b"", 60000, 10, None, "epochal"),
]


def check_case(mb, name, src, stdin, steps, width, limit, policy):
    vm_a = mb.MalbolgeCore(width=width, mem_limit=limit, growth_policy=policy)
    vm_a.load(src)
    expected = vm_a.run(steps, stdin)

    vm_b = mb.MalbolgeCore(width=width, mem_limit=limit, growth_policy=policy)
    vm_b.load(src)
    got, events = vm_b.trace_run(steps, stdin)

    assert got == expected, (name, got, expected)
    assert len(events) == expected["steps"], (name, len(events), expected["steps"])
    # events are well-formed and monotone in step
    for i, ev in enumerate(events, start=1):
        assert ev["step"] == i, (name, i, ev)
        for key in ("c_before", "d_before", "op", "a_before", "a_after",
                    "c_after", "d_after", "encrypted_addr"):
            assert key in ev, (name, i, key)
    # last event agrees with the summary on the final registers
    if events:
        last = events[-1]
        assert last["c_after"] == vm_b.stats["final_c"], name
        assert last["d_after"] == vm_b.stats["final_d"], name
    return expected["steps"]


def main() -> int:
    mb = load_core()
    total = 0
    for name, src, stdin, steps, width, limit, policy in CASES:
        n = check_case(mb, name, src, stdin, steps, width, limit, policy)
        total += n
        print(f"  {name}: summary identical, {n} events well-formed")
    print(f"TRACE_EQUIVALENCE: PASS ({len(CASES)} cases, {total} steps incl. epochal)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
