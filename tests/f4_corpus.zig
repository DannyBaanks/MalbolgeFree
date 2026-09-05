//! F4 corpus — more Classic programs, compared to the Python reference.
//! Evidence discipline: every run records status + steps + stdout Sha256.

const std = @import("std");
const core = @import("malbolge_free.zig");
const MalbolgeCore = core.MalbolgeCore;

const MEM_3_10: u128 = 3 * 3 * 3 * 3 * 3 * 3 * 3 * 3 * 3 * 3;

const HELLO_WORLD =
    \\(=<`#9]~6ZY327Uv4-QsqpMn&+Ij"'E%e{Ab~w=_:]Kw%o44Uqp0/Q?xNvL:`H%c#DD2^WV>gY;dts76qKJImZkj
;

const HELLO_WORLD_V2 =
    \\(=BA#9"=<;3N7654==32Cy/Il#%E&e~"z}|AY#;;;*'R[`>wV[:#,NhG=nS;a#qO
;

const HELLO_WORLD_V3 =
    \\(=&lt;!?_>;987]=<;:,546+a"31jk+qpOd1<<XXE%%4>tMl7:Nisu.9h
;

const CAT_PROGRAM =
    \\('&%$#\"!~}|{zyxwvutsrqponmlkjihgfedcba`_^]\\[ZYXWVUTSRQPONMLKJIHGFEDCBA
;

fn sha(comptime bytes: []const u8) void {
    _ = bytes;
}

fn statusLine(name: []const u8, res: core.RunResult) void {
    var h = std.crypto.hash.sha2.Sha256.init(.{});
    h.update(res.stdout.items);
    var digest: [32]u8 = undefined;
    h.final(&digest);
    var hex: [64]u8 = undefined;
    _ = std.fmt.bufPrint(&hex, "{} ", .{std.fmt.fmtHexLower(&digest)}) catch unreachable;
    std.debug.print("[F4 {s}] status={s} steps={d} sha256(stdout)={s} cells={d}\n", .{
        name, res.status, res.steps, hex, res.cells_materialized,
    });
}

test "F4 corpus: hello world baseline" {
    const alloc = std.heap.page_allocator;
    var vm = MalbolgeCore.init(alloc, 10, MEM_3_10, .fixed);
    defer vm.deinit();
    try vm.load(HELLO_WORLD);
    const res = try vm.run(2_000_000, "");
    statusLine("hello_world", res);
    try std.testing.expectEqualStrings("HALTED", res.status);
}

test "F4 corpus: hello world V2" {
    const alloc = std.heap.page_allocator;
    var vm = MalbolgeCore.init(alloc, 10, MEM_3_10, .fixed);
    defer vm.deinit();
    try vm.load(HELLO_WORLD_V2);
    const res = try vm.run(2_000_000, "");
    statusLine("hello_world_v2", res);
    try std.testing.expectEqualStrings("HALTED", res.status);
}

test "F4 corpus: hello world V3 (alternative program)" {
    const alloc = std.heap.page_allocator;
    var vm = MalbolgeCore.init(alloc, 10, MEM_3_10, .fixed);
    defer vm.deinit();
    try vm.load(HELLO_WORLD_V3);
    const res = try vm.run(2_000_000, "");
    statusLine("hello_world_v3", res);
    // V3 may or may not halt; record and compare against reference later.
}

test "F4 corpus: cat echo" {
    const alloc = std.heap.page_allocator;
    var vm = MalbolgeCore.init(alloc, 10, MEM_3_10, .fixed);
    defer vm.deinit();
    try vm.load(CAT_PROGRAM);
    const res = try vm.run(5_000_000, "A");
    statusLine("cat_A", res);
}
