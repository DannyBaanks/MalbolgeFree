//! F4c — canonical parity driver (hand-written; unlike run_f4.zig it is not generated).
//! Reads a case manifest, one case per line as `name<TAB>program_path<TAB>stdin`,
//! runs each case through the Zig core in Classic mode and prints one line per
//! case on stderr. The checker (`compare_f4_canonical.py`) compares those bytes
//! with the canonical oracles.

const std = @import("std");
const core = @import("malbolge_free");
const MalbolgeCore = core.MalbolgeCore;

pub fn main(init: std.process.Init) !void {
    const arena = init.arena.allocator();
    var args = try std.process.Args.Iterator.initAllocator(init.minimal.args, arena);
    _ = args.next();
    const manifest_path = args.next() orelse return error.MissingManifest;
    const manifest = try std.Io.Dir.cwd().readFileAlloc(
        init.io,
        manifest_path,
        arena,
        .unlimited,
    );

    var lines = std.mem.splitScalar(u8, manifest, '\n');
    while (lines.next()) |raw_line| {
        // A CRLF manifest would otherwise leak 0x0d into the last field (stdin),
        // which is what made the Zig core look wrong on windows-latest 2026-10-18.
        const line = std.mem.trimEnd(u8, raw_line, "\r");
        if (line.len == 0 or line[0] == '#') continue;
        var fields = std.mem.splitScalar(u8, line, '\t');
        const name = fields.next() orelse continue;
        const program_path = fields.next() orelse return error.MalformedManifest;
        const stdin_data = fields.next() orelse "";

        const src = try std.Io.Dir.cwd().readFileAlloc(init.io, program_path, arena, .unlimited);

        var vm = MalbolgeCore.initClassic(arena);
        try vm.load(src);
        const res = try vm.run(2_000_000, stdin_data);

        var h = std.crypto.hash.sha2.Sha256.init(.{});
        h.update(res.stdout.items);
        var digest: [32]u8 = undefined;
        h.final(&digest);
        const hex = std.fmt.bytesToHex(digest, .lower);

        std.debug.print("case={s} status={s} steps={d} sha256={s} stdout_hex=[", .{
            name, res.status, res.steps, hex,
        });
        for (res.stdout.items) |ch| std.debug.print("{x:0>2}", .{ch});
        std.debug.print("]\n", .{});
    }
}
