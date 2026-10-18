//! F13 — run one program under the explicit `unshackled_k19` profile and print
//! the observables the parity gate compares against the external reference.
//!
//! Why this driver exists as its own file: `t_unshackled_k19.zig` asserts the
//! profile is constructible and deterministic, and `run_f11_observations.zig`
//! sweeps the three width-10 profiles. Neither prints the pair (steps, halt
//! address, first stdout byte) for an arbitrary program at k=19, which is what
//! a differential against `bolge19` needs. This driver reads nothing but the
//! program path, writes no file and mutates nothing in src/.
//!
//!   zig run --dep malbolge_free=malbolge_free \
//!     -Mroot=evidence/run_f13_k19.zig -Mmalbolge_free=src/malbolge_free.zig \
//!     -- <image> <stdin-hex-or--> <budget>
const std = @import("std");
const core = @import("malbolge_free");

fn shaHex(bytes: []const u8) [64]u8 {
    var h = std.crypto.hash.sha2.Sha256.init(.{});
    h.update(bytes);
    var digest: [32]u8 = undefined;
    h.final(&digest);
    return std.fmt.bytesToHex(digest, .lower);
}

/// `bolge19` takes stdin on the real fd 0, so the case spec carries it as hex.
/// "-" means empty input.
fn unhex(text: []const u8, alloc: std.mem.Allocator) ![]u8 {
    if (std.mem.eql(u8, text, "-")) return alloc.alloc(u8, 0);
    const buf = try alloc.alloc(u8, text.len / 2);
    for (buf, 0..) |*slot, i| {
        slot.* = std.fmt.parseUnsigned(u8, text[i * 2 .. i * 2 + 2], 16) catch
            return error.BadStdinHex;
    }
    return buf;
}

pub fn main(init: std.process.Init) !void {
    const alloc = init.arena.allocator();
    var args = try std.process.Args.Iterator.initAllocator(init.minimal.args, alloc);
    _ = args.next();
    const program_path = args.next() orelse return error.MissingProgram;
    const stdin_hex = args.next() orelse "-";
    const budget: u64 = if (args.next()) |raw|
        try std.fmt.parseInt(u64, raw, 10)
    else
        100;

    const src = try std.Io.Dir.cwd().readFileAlloc(init.io, program_path, alloc, .unlimited);
    std.debug.print("PROG bytes={d} sha={s}\n", .{ src.len, shaHex(src) });

    var vm = core.MalbolgeCore.initUnshackledK19(alloc);
    defer vm.deinit();
    std.debug.print(
        \\PARAM width={d} padwidth={d} mem_limit={d} growth={s} profile={s} pow3_19={d}
        \\
    , .{
        vm.width,
        vm.padwidth,
        vm.mem_limit orelse 0,
        @tagName(vm.growth),
        @tagName(vm.profile),
        core.pow3(19),
    });

    try vm.load(src);
    const stdin = try unhex(stdin_hex, alloc);
    const res = try vm.run(budget, stdin);
    std.debug.print(
        \\RUN status={s} steps={d} out_len={d} out_first={?d} out_sha={s} final_c={d} final_d={d} cells={d} encrypted={d}
        \\
    , .{
        res.status,
        res.steps,
        res.stdout.items.len,
        if (res.stdout.items.len == 0) null else res.stdout.items[0],
        shaHex(res.stdout.items),
        res.final_c,
        res.final_d,
        res.cells_materialized,
        res.encrypted_cells,
    });
}
