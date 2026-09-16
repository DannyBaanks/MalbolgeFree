const std = @import("std");
const ir = @import("bf_to_ir.zig");
const image = @import("bf_ir_image.zig");
const vm = @import("bf_ir_vm.zig");
const backend = @import("backend");
const hell = @import("hell");
const mb = @import("malbolge_free");

// M6.5 full differential: al menos cinco programas BF con output, input,
// cinta final, puntero y terminación comparados end-to-end contra la
// referencia BFIR1 (misma forma que M6.4, más casos y el Hello World
// canónico con su loop de inicialización).

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
    var lowered = try backend.lowerImage(img, allocator);
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
    var res = try core.run(5_000_000, input);
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

// Hello World! verificada en dos intérpretes independientes (raw y BFIR1):
// esquema de celda fresca por carácter >N[>M<-]>R. = N*M+R, acumulador en
// P+2 (cero por construcción). Hex esperado: 48 65 6c 6c 6f 20 57 6f 72 6c 64 21.
const HELLO_WORLD =
    ">++++++++[>+++++++++<-]>." ++ //  8*9    = 72 'H'
    ">++++++++++[>++++++++++<-]>+." ++ // 10*10+1 = 101 'e'
    ">++++++++++[>++++++++++<-]>++++++++." ++ // 10*10+8 = 108 'l'
    ">++++++++++[>++++++++++<-]>++++++++." ++ // 10*10+8 = 108 'l'
    ">++++++++++[>++++++++++<-]>+++++++++++." ++ // 10*10+11 = 111 'o'
    ">++++[>++++++++<-]>." ++ //  4*8    = 32 ' '
    ">++++++++++[>++++++++<-]>+++++++." ++ // 10*8+7  = 87 'W'
    ">++++++++++[>++++++++++<-]>+++++++++++." ++ // 10*10+11 = 111 'o'
    ">++++++++++[>++++++++++<-]>++++++++++++++." ++ // 10*10+14 = 114 'r'
    ">++++++++++[>++++++++++<-]>++++++++." ++ // 10*10+8 = 108 'l'
    ">++++++++++[>++++++++++<-]>." ++ // 10*10  = 100 'd'
    ">++++[>++++++++<-]>+."; //  4*8+1  = 33 '!'

test "M6.5 full differential: cinco programas comparan stdout/cinta/puntero/terminación" {
    const allocator = std.testing.allocator;
    const cases = [_]Case{
        .{ .source = "+++[-].", .input = "" },
        .{ .source = "++[>++<-]>.", .input = "" },
        .{ .source = ",[.,]", .input = "AB" },
        .{ .source = "+[>+<-]>.", .input = "" },
        .{ .source = HELLO_WORLD, .input = "" },
    };

    for (cases) |case| {
        var ir_prog = try ir.compile(case.source, allocator);
        defer ir_prog.deinit();
        try ir.validate(&ir_prog);

        const img = try image.encode(&ir_prog, allocator);
        defer allocator.free(img);

        var ir_prog2 = try image.decode(img, allocator);
        defer ir_prog2.deinit();
        var ref = try vm.run(&ir_prog2, case.input, .{ .tape_size = 256, .max_steps = 1_000_000 }, allocator, false);
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
    }
}

test "M6.5 sanity: el Hello World Malbolge imprime el mensaje exacto" {
    const allocator = std.testing.allocator;

    var ir_prog = try ir.compile(HELLO_WORLD, allocator);
    defer ir_prog.deinit();
    try ir.validate(&ir_prog);

    const img = try image.encode(&ir_prog, allocator);
    defer allocator.free(img);

    var got = try runMalbolge(img, "", allocator);
    defer got.deinit(allocator);

    try std.testing.expectEqualStrings("HALTED", got.status);
    try std.testing.expectEqualStrings("Hello World!", got.stdout);
}
