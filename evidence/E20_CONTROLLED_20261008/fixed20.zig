const std = @import("std");
const core = @import("malbolge_free");

pub fn main() !void {
    const cases = [_]struct { name: []const u8, source: []const u8, input: []const u8 }{
        .{ .name = "hello20", .source = @embedFile("nagoya/hello20.mb"), .input = "" },
        .{ .name = "eof_echo", .source = "ubO", .input = "" },
        .{ .name = "byte_echo", .source = "ubO", .input = "A" },
    };
    for (cases) |case| {
        var vm = core.MalbolgeCore.init(std.heap.page_allocator, 20, core.pow3(20), .fixed);
        defer vm.deinit();
        try vm.load(case.source);
        var result = try vm.run(2_000_000, case.input);
        defer result.stdout.deinit(std.heap.page_allocator);
        std.debug.print("CASE name={s} status={s} steps={d} width={d} growth={d} stdout_hex=", .{case.name, result.status, result.steps, vm.padwidth, vm.stats.growth_events});
        for (result.stdout.items) |byte| std.debug.print("{x:0>2}", .{byte});
        std.debug.print("\n", .{});
    }
}
