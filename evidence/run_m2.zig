//! M2 trace exporter. It is intentionally read-only: callers own the output path.
const std = @import("std");
const core = @import("malbolge_free");

const Case = struct { name: []const u8, source: []const u8, input: []const u8, max_steps: u64 };
const CASES = [_]Case{
    .{ .name = "out", .source = "cP", .input = "", .max_steps = 16 },
    .{ .name = "input", .source = "uP", .input = "A", .max_steps = 16 },
    .{ .name = "eof", .source = "uP", .input = "", .max_steps = 16 },
    .{ .name = "rot", .source = "'P", .input = "", .max_steps = 16 },
    .{ .name = "movd", .source = "(P", .input = "", .max_steps = 16 },
    .{ .name = "crazy", .source = ">P", .input = "", .max_steps = 16 },
    .{ .name = "jmp", .source = "bP", .input = "", .max_steps = 16 },
    .{ .name = "nop", .source = "DC", .input = "", .max_steps = 16 },
};

pub fn main() !void {
    for (CASES) |case| {
        var vm = core.MalbolgeCore.initClassic(std.heap.page_allocator);
        defer vm.deinit();
        try vm.load(case.source);
        var trace = std.ArrayList(core.TraceEvent).empty;
        defer trace.deinit(std.heap.page_allocator);
        const result = try vm.runWithTrace(case.max_steps, case.input, &trace);
        std.debug.print("CASE {s} status={s} steps={d} stdout=", .{ case.name, result.status, result.steps });
        for (result.stdout.items) |byte| std.debug.print("{x:0>2}", .{byte});
        std.debug.print(" trace=", .{});
        for (trace.items, 0..) |event, index| {
            if (index != 0) std.debug.print(";", .{});
            std.debug.print("{d},{d},{d},{d},{d},{d},{d},{d},{d},{d},{d}", .{
                event.step, event.a_before, event.c_before, event.d_before, event.op,
                event.cell_before, event.a_after, event.c_after, event.d_after,
                event.encrypted_addr orelse std.math.maxInt(u128),
                event.encrypted_value orelse std.math.maxInt(u128),
            });
        }
        std.debug.print("\n", .{});
    }

    const invalid = [_]Case{
        .{ .name = "non_printable", .source = "u\x01", .input = "", .max_steps = 0 },
        .{ .name = "positional_opcode", .source = "!!", .input = "", .max_steps = 0 },
        .{ .name = "too_short", .source = "b", .input = "", .max_steps = 0 },
    };
    for (invalid) |case| {
        var vm = core.MalbolgeCore.initClassic(std.heap.page_allocator);
        defer vm.deinit();
        vm.load(case.source) catch |err| {
            std.debug.print("ERROR {s} error={s}\n", .{ case.name, @errorName(err) });
            continue;
        };
        return error.ExpectedLoadFailure;
    }
}
