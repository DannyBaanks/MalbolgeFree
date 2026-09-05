//! F4 — Classic parity.
//! Criterion: FREE(k=10, mem_limit=3^10, fixed) == reference Classic
//! on stdout, halt, steps. Reference = vendored malbolge.py (Python).
//!
//! Evidence '{"program","stdout","steps","status","sha"}.claim' produced per run.

const std = @import("std");
const core = @import("malbolge_free.zig");
const MalbolgeCore = core.MalbolgeCore;

const HELLO_WORLD =
    \\(=<`#9]~6ZY327Uv4-QsqpMn&+Ij"'E%e{Ab~w=_:]Kw%o44Uqp0/Q?xNvL:`H%c#DD2^WV>gY;dts76qKJImZkj
;

test "F4 classic hello world" {
    const alloc = std.heap.page_allocator;

    var vm = MalbolgeCore.init(alloc, 10, 3 * 3 * 3 * 3 * 3 * 3 * 3 * 3 * 3 * 3, .fixed);
    defer vm.deinit();
    try vm.load(HELLO_WORLD);

    const res = try vm.run(2_000_000, "");
    std.debug.print("\nF4-hello: status={s} steps={d} stdout={s}\n", .{
        res.status, res.steps, res.stdout.items,
    });
    try std.testing.expectEqualStrings("HALTED", res.status);
    try std.testing.expectEqualStrings("Hello, world.", res.stdout.items);
}
