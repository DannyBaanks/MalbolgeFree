const std = @import("std");
const ir = @import("bf_to_ir.zig");
const image = @import("bf_ir_image.zig");
const vm = @import("bf_ir_vm.zig");
const backend = @import("backend");
const hell = @import("hell");
const mb = @import("malbolge_free");

// M6.2 differential: tres imágenes BFIR1 lineales (sin loops) ejecutadas
// end-to-end y comparadas contra la referencia BFIR1 en stdout, cinta,
// puntero y terminación. El conteo de pasos se compara a nivel BF: el
// lowering emite varios pasos Malbolge por cada paso BF, así que el conteo
// crudo Malbolge (res.steps) es de codificación, no de semántica.

const Case = struct {
    source: []const u8,
    input: []const u8,
};

const MalbolgeRun = struct {
    status: []const u8,
    stdout: []u8,
    final_d: u128,
    tape: [256]u8,

    fn deinit(self: *MalbolgeRun, allocator: std.mem.Allocator) void {
        allocator.free(self.stdout);
    }
};

fn runMalbolge(img: []const u8, input: []const u8, allocator: std.mem.Allocator) !MalbolgeRun {
    var be_image = try backend.decode(img, allocator);
    defer be_image.deinit(allocator);

    var lowered = try backend.lowerLinear(&be_image, allocator);
    defer lowered.deinit(allocator);

    var parser = hell.Parser.init(lowered.slice());
    var program = try parser.parse(allocator);
    defer program.deinit(allocator);
    var layout = try hell.resolveLayout(&program, allocator);
    defer layout.deinit(allocator);
    var emitted = try hell.emit(&layout, allocator);
    defer emitted.deinit(allocator);

    var core = mb.MalbolgeCore.initFreeAssisted(allocator, 10, 59049, .fixed);
    defer core.deinit();
    try core.load(emitted.slice());
    var res = try core.run(100_000, input);
    defer res.stdout.deinit(allocator);

    const stdout_copy = try allocator.dupe(u8, res.stdout.items);

    var tape: [256]u8 = undefined;
    var i: usize = 0;
    while (i < 256) : (i += 1) {
        tape[i] = @intCast(try core.cell(@as(u128, 1000) + i));
    }

    return .{
        .status = res.status,
        .stdout = stdout_copy,
        .final_d = res.final_d,
        .tape = tape,
    };
}

test "M6.2 differential: tres imágenes lineales comparan stdout/cinta/puntero/terminación" {
    const allocator = std.testing.allocator;
    const cases = [_]Case{
        .{ .source = "+++.-.", .input = "" },
        .{ .source = ">+++<+>.>.", .input = "" },
        .{ .source = ",+.", .input = "A" },
    };

    for (cases) |case| {
        var ir_prog = try ir.compile(case.source, allocator);
        defer ir_prog.deinit();
        try ir.validate(&ir_prog);

        const img = try image.encode(&ir_prog, allocator);
        defer allocator.free(img);

        var ir_prog2 = try image.decode(img, allocator);
        defer ir_prog2.deinit();
        var ref = try vm.run(&ir_prog2, case.input, .{ .tape_size = 256, .max_steps = 1000 }, allocator, false);
        defer ref.deinit();

        var got = try runMalbolge(img, case.input, allocator);
        defer got.deinit(allocator);

        try std.testing.expectEqualStrings("HALTED", got.status);
        try std.testing.expectEqualSlices(u8, ref.output.items, got.stdout);

        var i: usize = 0;
        while (i < 256) : (i += 1) {
            try std.testing.expectEqual(ref.tape.items[i], got.tape[i]);
        }

        try std.testing.expectEqual(@as(u128, @intCast(1000 + ref.pointer)), got.final_d);
        try std.testing.expectEqual(@as(u64, @intCast(ir_prog.code.items.len)), ref.steps);
    }
}
