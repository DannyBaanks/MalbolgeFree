"""MalbolgeCore — parametric Malbolge runtime.

No special-casing for k=10 or k=19 anywhere in the semantics.
Classic parity is achieved by *parameters*, not by `if k == 10` branches.
"""
from __future__ import annotations

# ── constants (width-independent) ────────────────────────────────────────────
_CRAZY = ((1, 0, 0), (1, 0, 2), (2, 2, 1))
_ENC = {ord(o): ord(t) for o, t in zip(
    r"""!"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~""",
    r"""5z]&gqtyfr$(we4{WP)H-Zn,[%\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G"i@""",
)}


def crazy(a: int, b: int, width: int) -> int:
    """Tritwise crazy over exactly `width` positions. Width is in, not global."""
    res = 0
    p = 1
    for _ in range(width):
        res += _CRAZY[b % 3][a % 3] * p
        a //= 3
        b //= 3
        p *= 3
    return res


def rotate(v: int, width: int) -> int:
    """Rotate right one trit within `width` trits. Width is in, not global."""
    return v // 3 + (v % 3) * (3 ** (width - 1))


def tritlen(v: int) -> int:
    """min w s.t. v < 3**w.  v=0 -> 1 (fits in a single trit)."""
    if v < 0:
        raise ValueError("negative")
    n = 1
    p = 3
    while p <= v:
        p *= 3
        n += 1
    return n


class MalbolgeCore:
    """Parametric Malbolge.

    Parameters
    ----------
    width :
        Trit width for crazy/rotate **if** growth_policy == 'fixed'.
        With growth_policy='pad_to_padwidth', val-ops pad to `padwidth`,
        which can grow; width is then just the starting padwidth.
    mem_limit : int | None
        Address space size; addresses wrap modulo mem_limit. None = unbounded,
        no wrap (lazy memory). Classic uses 3**10.
    growth_policy : 'fixed' | 'pad_to_padwidth' | 'epochal'
        'fixed': crazy/rotate always use exactly `width` trits.
        'pad_to_padwidth': before rotate, pad operand to current padwidth
        (det_growth_policy can raise padwidth).
        'epochal': width follows the address frontier. Before each step, if `c`
        or `d` has reached 3**padwidth, padwidth grows by one and crazy/rotate
        use the new padwidth. Requires mem_limit=None (no wrap), otherwise the
        frontier could never be reached. History is never rewritten.
    """

    def __init__(self, width: int = 10, mem_limit: int | None = 3 ** 10,
                 growth_policy: str = "fixed"):
        assert width >= 1
        assert mem_limit is None or mem_limit >= 3
        assert growth_policy in ("fixed", "pad_to_padwidth", "epochal"), growth_policy
        if growth_policy == "epochal":
            # A wrapping address space can never reach the frontier, so the
            # policy would be dead code. Refuse instead of pretending.
            if mem_limit is not None:
                raise ValueError("epochal requires mem_limit=None (no wrap)")
        self.width = width
        self.mem_limit = mem_limit
        self.growth_policy = growth_policy
        self.padwidth = width          # grows under pad_to_padwidth and epochal
        self.mem: dict[int, int] = {}  # lazy; cell i absent => lazy-fill on read
        self.program_len = 0
        self.initial_tail: list[int] = []
        # instrumentation
        self.stats = {
            "steps": 0, "max_addr_touched": 0, "max_value": 0,
            "width_growth_events": [],
            "encrypted_cells": 0, "assisted_opcodes": 0,
            "final_c": None, "final_d": None,
        }

    # -- loader --------------------------------------------------------------
    def load(self, source: str):
        """Load program, stripping whitespace; reject non-printable bytes."""
        chars = [c for c in source if not c.isspace()]
        for i, ch in enumerate(chars):
            v = ord(ch)
            if not (33 <= v <= 126):
                raise ValueError(f"invalid source char {v!r} at {i}")
            self.mem[i] = v
        assert len(chars) >= 2, "need at least 2 cells for crazy-fill seed"
        self.program_len = len(chars)
        # Freeze one full 12-cell period of the crazy-fill tail, computed with the
        # *initial* width before execution can encrypt source cells. Reads past
        # the range repeat this immutable period, which is what makes the eager
        # Classic fill reproducible without materialising every cell.
        self.initial_tail = []
        for k in range(12):
            t = self.program_len + k
            v = crazy(self.mem[t - 1], self.mem[t - 2], self.width)
            self.mem[t] = v
            self.initial_tail.append(v)

    def _cell(self, i: int) -> int:
        """Lazy materialization. Equivalent to eager Classic crazy-fill:
        cell[i] = crazy(cell[i-1], cell[i-2]) for i >= program_len.
        Past the frozen 12-cell period the tail repeats, so a read at an
        arbitrary address is O(1) instead of an O(i) walk."""
        if self.mem_limit is not None:
            i %= self.mem_limit
        if i in self.mem:
            return self.mem[i]
        if i < self.program_len:
            raise AssertionError(f"program cell {i} missing")
        if i >= self.program_len + 12:
            return self.initial_tail[(i - self.program_len) % 12]
        # inside the frozen window but not materialised yet: build the short chain
        chain = []
        j = i
        while j >= self.program_len and j not in self.mem:
            chain.append(j)
            j -= 1
        while chain:
            t = chain.pop()
            v = crazy(self.mem[t - 1], self.mem[t - 2], self.width)
            self.mem[t] = v
        return self.mem[i]

    def _frontier_trigger(self, c: int, d: int):
        """Epochal: grow by one when a pointer reaches the current frontier.

        Fires at most one step per widening, before the step touches memory at
        the boundary address. Already-written cells always win over the frozen
        tail, so widening never rewrites history.
        """
        if self.growth_policy != "epochal":
            return
        boundary = 3 ** self.padwidth
        if c >= boundary or d >= boundary:
            ev = {"from": self.padwidth, "to": self.padwidth + 1,
                  "step": self.stats["steps"], "c": c, "d": d}
            self.stats["width_growth_events"].append(ev)
            self.padwidth += 1

    def _cell_write(self, i: int, v: int):
        if self.mem_limit is not None:
            i %= self.mem_limit
        self.mem[i] = v
        mad = max(self.stats["max_addr_touched"], i)
        self.stats["max_addr_touched"] = mad
        self.stats["max_value"] = max(self.stats["max_value"], v)

    def _maybe_grow(self, v: int):
        """det growth policy (Unshackled): if a value's width exceeds, grow."""
        if self.growth_policy != "pad_to_padwidth":
            return
        need = tritlen(v)
        if need > self.padwidth:
            ev = {"from": self.padwidth, "to": need, "step": self.stats["steps"]}
            self.stats["width_growth_events"].append(ev)
            self.padwidth = need

    # -- stepper -------------------------------------------------------------
    def run(self, max_steps: int = 2_000_000, stdin_data: bytes = b"",
              _sink: list | None = None) -> dict:
        import sys
        sys.setrecursionlimit(max(10000, self.program_len + 1000))
        a, c, d = 0, 0, 0
        out = bytearray()
        stdin_iter = iter(stdin_data)
        limit = self.mem_limit  # None => unbounded
        status = "MAX_STEPS"

        # NOTE (M7 CLI): _sink is an internal event collector used only by
        # trace_run(). When None (every existing caller, all 43 gates) the loop
        # below is semantically identical to before: appending to a list cannot
        # change machine state. Equivalence is asserted, not assumed, by
        # tests/t_trace_equivalence.py.
        while self.stats["steps"] < max_steps:
            self.stats["steps"] += 1
            # Epochal widening happens BEFORE the step touches memory, so the
            # boundary address is read at the new width.
            self._frontier_trigger(c, d)
            cc = (c % limit) if limit is not None else c
            cell = self._cell(cc)
            op = (cell + cc) % 94
            a_before, c_before, d_before, enc_addr = a, c, d, None

            if op == 4:                 # jmp
                c = self._cell(d % limit if limit is not None else d)
            elif op == 5:               # out
                out.append(a % 256)
            elif op == 23:              # in
                ch = next(stdin_iter, None)
                a = -1 if ch is None else ch
            elif op == 39:              # rot
                dd = d % limit if limit is not None else d
                v = self._cell(dd)
                if self.growth_policy == "epochal":
                    w = self.padwidth
                elif self.growth_policy == "pad_to_padwidth":
                    w = max(self.padwidth, tritlen(v))
                else:
                    w = self.width
                nv = rotate(v, w)
                self._cell_write(dd, nv)
                a = nv
                self._maybe_grow(a)
            elif op == 40:              # movd
                dd = d % limit if limit is not None else d
                d = self._cell(dd)
                self._maybe_grow(d)
            elif op == 62:              # crazy
                dd = d % limit if limit is not None else d
                v = self._cell(dd)
                if self.growth_policy == "epochal":
                    w = self.padwidth
                elif self.growth_policy == "fixed":
                    w = self.width
                else:
                    w = max(self.padwidth, tritlen(v), tritlen(a if a >= 0 else 0))
                aa = (3 ** w) - 1 if a < 0 else a % (3 ** w)
                nv = crazy(aa, v, w)
                self._cell_write(dd, nv)
                a = nv
            elif op == 68:              # nop
                pass
            elif op == 81:              # hlt
                status = "HALTED"
                if _sink is not None:
                    _sink.append({
                        "step": self.stats["steps"],
                        "c_before": c_before, "d_before": d_before,
                        "op": op, "a_before": a_before, "a_after": a,
                        "c_after": c, "d_after": d,
                        "encrypted_addr": None,
                    })
                break

            # self-encryption after execution
            cc = (c % limit) if limit is not None else c
            mc = self._cell(cc)
            if 33 <= mc <= 126:
                self._cell_write(cc, _ENC[mc])
                self.stats["encrypted_cells"] += 1
                enc_addr = cc

            c = (c + 1) % limit if limit is not None else c + 1
            d = (d + 1) % limit if limit is not None else d + 1
            if _sink is not None:
                _sink.append({
                    "step": self.stats["steps"],
                    "c_before": c_before, "d_before": d_before,
                    "op": op, "a_before": a_before, "a_after": a,
                    "c_after": c, "d_after": d,
                    "encrypted_addr": enc_addr,
                })

        self.stats["final_c"] = c
        self.stats["final_d"] = d

        return {
            "status": status,
            "stdout": bytes(out).decode("latin-1"),
            "steps": self.stats["steps"],
            "max_addr_touched": self.stats["max_addr_touched"],
            "max_value": self.stats["max_value"],
            "padwidth": getattr(self, "padwidth", None),
            "growth_events": len(self.stats["width_growth_events"]),
        }

    def trace_run(self, max_steps: int = 2_000_000, stdin_data: bytes = b"",
                  limit: int | None = None) -> tuple[dict, list]:
        """Run collecting a per-step trace. New additive API for the M7 CLI.

        Returns (summary, events) where summary is IDENTICAL in shape and value
        to run() on the same inputs (asserted by tests/t_trace_equivalence.py),
        and each event carries step/c_before/d_before/op/a_before/a_after/
        c_after/d_after/encrypted_addr. `limit` caps the stored events; the run
        itself always continues to max_steps so the summary is unaffected.
        """
        events: list = []
        res = self.run(max_steps, stdin_data, _sink=events)
        if limit is not None:
            events = events[:limit]
        return res, events
