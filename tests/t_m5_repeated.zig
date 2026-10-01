//! M5: repeated epochal widening, 10 -> 11 -> 12.
const std = @import("std");
const core = @import("malbolge_free");

test "epochal crosses two frontiers" {
    const alloc = std.testing.allocator;
    const src = @embedFile("frontier_witness.txt");
    var vm = core.MalbolgeCore.initFreePure(alloc, 10, .epochal);
    defer vm.deinit();
    try vm.load(src);

    var a: u128 = 0;
    var c: u128 = 0;
    var d: u128 = 0;
    var steps: u64 = 0;
    var widen_steps: [2]u64 = undefined;
    var widen_count: usize = 0;

    while (steps < 190_000) {
        steps += 1;
        const cell = try vm.cell(c);
        const op = (cell + c) % 94;
        // NOTE (2026-10-01): if-chain on purpose, not switch: `switch` on a
        // computed u128 misdispatches (and can corrupt the scrutinee value)
        // in Zig 0.16.0 Debug. Same root cause as src/malbolge_free.zig
        // isClassicSourceOpcode. See evidence pack mf_fix_20261001.
        if (op == 5) {
        } else if (op == 23) {
            a = 255;
        } else if (op == 62) {
        } else if (op == 68) {
        } else return error.UnexpectedWitnessOpcode;

        const old_w = vm.padwidth;
        vm.frontierTrigger(c, d);
        if (vm.padwidth != old_w) {
            if (widen_count >= widen_steps.len) return error.TooManyWidenings;
            widen_steps[widen_count] = steps;
            widen_count += 1;
        }
        c += 1;
        d += 1;
    }

    try std.testing.expectEqual(@as(usize, 2), widen_count);
    try std.testing.expectEqual(@as(u64, 59050), widen_steps[0]);
    try std.testing.expectEqual(@as(u64, 177148), widen_steps[1]);
    try std.testing.expectEqual(@as(u8, 12), vm.padwidth);
    try std.testing.expectEqual(@as(u32, 2), vm.stats.growth_events);
}
