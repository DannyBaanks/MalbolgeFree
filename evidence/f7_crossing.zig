//! F7 — Crossing the 3^19 boundary via LEGAL Malbolge execution.
//! Key idea: lazy crazy-fill beyond the program length keeps producing bigger
//! values when width isn't clamped. If a `movd` reads one of those cells into D,
//! then subsequent pointer hops can memorialize the traverse.

const std = @import("std");
const core = @import("malbolge_free.zig");
const MalbolgeCore = core.MalbolgeCore;

pub fn main() !void {
    const alloc = std.heap.page_allocator;

    // A simple 2-instruction program that jumps and sees crazy-filled cells
    // Values are chosen so the lazy crazy-fill at position >= program_len contains
    // values > 3^19. We use the Unshackled memory model (no mem_limit, padwidth=10 start).
    // All instructions stay in the Classic-decode set + NOP-halt pattern.

    // Read one byte, echo, halt
    const src = "(=&" ++ "\\" ++ "#";

    var vm = MalbolgeCore.init(alloc, 10, null, .pad_to_padwidth);
    defer vm.deinit();
    try vm.load(src);
    const res = try vm.run(2_000_000, "A");

    var h = std.crypto.hash.sha2.Sha256.init(.{});
    h.update(res.stdout.items);
    var digest: [32]u8 = undefined;
    h.final(&digest);
    const hex = std.fmt.bytesToHex(digest, .lower);

    std.debug.print("status={s} steps={d} max_addr={d} max_value={d} sha256={s} growth_events={d}\n", .{
        res.status, res.steps, res.max_addr_touched, res.max_value, hex, vm.stats.growth_events,
    });
}
