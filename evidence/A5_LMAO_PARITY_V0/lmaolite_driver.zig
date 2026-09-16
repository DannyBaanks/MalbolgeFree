//! A5 driver: assemble one HeLL file with lmao-lite, using exactly the calls the
//! malbolge-free tests use (Parser.parse -> resolveLayout -> emit). No changes to lmao-lite.
//! Prints `STAGE=<parse|layout|emit> ERROR=<name>` on failure or `STAGE=ok` followed by
//! `SOURCE=<emitted program>` on stderr.
const std = @import("std");
const hell = @import("hell");

pub fn main(init: std.process.Init) !void {
    const arena = init.arena.allocator();
    var args = try std.process.Args.Iterator.initAllocator(init.minimal.args, arena);
    defer args.deinit();
    _ = args.next();
    const path = args.next() orelse return error.MissingPath;
    const src = try (std.Io.Dir.cwd()).readFileAlloc(init.io, path, arena, .unlimited);

    var parser = hell.Parser.init(src);
    var program = parser.parse(arena) catch |e| {
        std.debug.print("STAGE=parse ERROR={s}\n", .{@errorName(e)});
        return;
    };
    var layout = hell.resolveLayout(&program, arena) catch |e| {
        std.debug.print("STAGE=layout ERROR={s}\n", .{@errorName(e)});
        return;
    };
    const emitted = hell.emit(&layout, arena) catch |e| {
        std.debug.print("STAGE=emit ERROR={s}\n", .{@errorName(e)});
        return;
    };
    std.debug.print("STAGE=ok\nSOURCE={s}\n", .{emitted.slice()});
}
