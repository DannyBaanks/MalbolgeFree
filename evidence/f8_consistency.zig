//! F8 — width extension consistency.
//! Compare Free(k) vs Free(k+1) on a same program: does one project's output
//! project onto the other on the region they share?
//!
//! Proposition: for STARTING padwidth=k, any operation whose operand best fits
//! in ≤k trits yields the same result under width k and width k+1…k+n, up to
//! the point a rotate *pads* an operand wider than k. The pad is the source of
//! difference, because rotate(10-trit value, width=11) writes a NEW highest
//! trit at position 10 that cannot exist under width 10.
//!
//! We quantify: percentage of programs / ops where the width=k+1 trace equals
//! the width=k trace over N steps. If it's not 100%, dynamic growth is
//! inconsistent.

const std = @import("std");
const core = @import("malbolge_free.zig");
const MalbolgeCore = core.MalbolgeCore;

pub fn main() !void {
    const alloc = std.heap.page_allocator;
    // Probe programs: all single-char literals in printable range [33,126]
    // Actually — the "op encoding" is what we want. Let's enumerate distinct
    // ops by searching for (cell, c) pairs.
    const ops = [_]u8{ 39, 40, 62, 68, 81 };

    // For each k in {10, 11, 19, 20}, build the "same program" (a fixed
    // 100-instruction sequence), then run 100 steps and compare memory snapshots
    // on the region [0, min_addr)*3^k + c) written by runs of both widths.
    // Simpler: just enumerate a couple of pairs (state, op) and test
    //   rotate(x) != equality modulo k-trit padding
    // directly.
    for (@as([_]u8{ 10, 20 }._.type) |_| {} }
}
