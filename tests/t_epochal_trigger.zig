//! epochal-from-k10 nop test: if `c` passes 3^10 the width must advance to k=11.
//! Expected behavior from the ANCHORED-EPOCHAL model.
//!
//! The program is entirely NOPs, so pointer advance is exactly c=d=step.

const std = @import("std");
const core = @import("malbolge_free.zig");
const MalbolgeCore = core.MalbolgeCore;

pub fn main() !void {
    const alloc = std.heap.page_allocator;

    // 1000 NOPs (any printable char behaves the same as nop if not in the
    // 8-opcode set at the current position)
    var prog_buf: [1000]u8 = undefined;
    for (&prog_buf) |*b| b.* = 'z';

    var vm = MalbolgeCore.init(alloc, 10, null, .epochal);
    defer vm.deinit();
    try vm.load(&prog_buf);

    const res = try vm.run(59_060, "");
    const boundary = std.math.pow(u128, 3, 10);
    std.debug.print(
        "epochal from k=10, NOP program, 59060 steps:\n  status={s} steps={d} growth_events={d} final_padwidth={d}\n  (frontier 3^10 = {d})\n",
        .{ res.status, res.steps, vm.stats.growth_events, vm.padwidth, boundary },
    );

    if (vm.padwidth == 11 and vm.stats.growth_events == 1) {
        std.debug.print("=> FRONTERA DETECTADA: width widened exactly once at the 3^10 boundary\n", .{});
    } else if (vm.padwidth == 10) {
        std.debug.print("=> FRONTIER NOT CROSSED: program never reached step 59049\n", .{});
    } else {
        std.debug.print("=> SURPRISE: padwidth={d}\n", .{vm.padwidth});
    }
}
