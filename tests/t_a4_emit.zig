const std = @import("std");
const hell = @import("hell");
const mb = @import("malbolge_free");
const Parser = hell.Parser;
const Opcode = hell.Opcode;

test "A4 emit: simple HALT produces one character" {
    var parser = Parser.init(".CODE\n  HALT");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    var emitted = try hell.emit(&layout, std.testing.allocator);
    defer emitted.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(usize, 1), emitted.slice().len);
}

test "A4 emit: NOP + HALT produces two characters" {
    var parser = Parser.init(".CODE\n  NOP\n  HALT");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    var emitted = try hell.emit(&layout, std.testing.allocator);
    defer emitted.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(usize, 2), emitted.slice().len);
}

test "A4 emit: data block adds data characters" {
    var parser = Parser.init(".DATA {\n  42\n  65\n}");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    var emitted = try hell.emit(&layout, std.testing.allocator);
    defer emitted.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(usize, 2), emitted.slice().len);
}

test "A4 emit: code + data combined" {
    var parser = Parser.init(".CODE\n  NOP\n.DATA {\n  65\n  70\n}");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    var emitted = try hell.emit(&layout, std.testing.allocator);
    defer emitted.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(usize, 3), emitted.slice().len);
}

test "A4 emit: NOP at position 0 produces printable char" {
    var parser = Parser.init(".CODE\n  NOP");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    var emitted = try hell.emit(&layout, std.testing.allocator);
    defer emitted.deinit(std.testing.allocator);

    const ch = emitted.slice()[0];
    try std.testing.expect(ch >= 33 and ch <= 126);
}

test "A4 emit: all output chars are printable ASCII" {
    var parser = Parser.init(".CODE\n  NOP\n  HALT\n.DATA {\n  42\n}");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    var emitted = try hell.emit(&layout, std.testing.allocator);
    defer emitted.deinit(std.testing.allocator);

    for (emitted.slice()) |ch| {
        try std.testing.expect(ch >= 33 and ch <= 126);
    }
}

test "A4 emit: non-printable data is rejected" {
    var parser = Parser.init(".DATA {\n  0\n}");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    try std.testing.expectError(error.InvalidDataValue, hell.emit(&layout, std.testing.allocator));
}

test "A4 emit: empty program produces empty output" {
    var parser = Parser.init("");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    var emitted = try hell.emit(&layout, std.testing.allocator);
    defer emitted.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(usize, 0), emitted.slice().len);
}

test "A4 emit: commandToChar produces printable char" {
    const valid_cmds = [_]u8{ 4, 5, 23, 39, 40, 62, 68, 81 };
    for (valid_cmds) |cmd| {
        for (0..94) |pos| {
            const ch = hell.emitCommandToChar(cmd, pos);
            try std.testing.expect(ch >= 33 and ch <= 126);
        }
    }
}

test "A4 runtime: emitted NOP/HALT executes in MalbolgeCore" {
    var parser = Parser.init(".CODE\n  NOP\n  HALT");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);
    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);
    var emitted = try hell.emit(&layout, std.testing.allocator);
    defer emitted.deinit(std.testing.allocator);

    var core = mb.MalbolgeCore.initFreeAssisted(std.testing.allocator, 10, null, .fixed);
    defer core.deinit();
    try core.load(emitted.slice());
    const result = try core.run(10, "");
    try std.testing.expectEqualStrings("HALTED", result.status);
    try std.testing.expectEqual(@as(u64, 2), result.steps);
}

test "A4 runtime: emitted IN/OUT relays one byte" {
    var parser = Parser.init(".CODE\n  IN\n  OUT");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);
    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);
    var emitted = try hell.emit(&layout, std.testing.allocator);
    defer emitted.deinit(std.testing.allocator);

    var core = mb.MalbolgeCore.initFreeAssisted(std.testing.allocator, 10, null, .fixed);
    defer core.deinit();
    try core.load(emitted.slice());
    var result = try core.run(10, "A");
    defer result.stdout.deinit(std.testing.allocator);
    try std.testing.expectEqualStrings("MAX_STEPS", result.status);
    try std.testing.expectEqualSlices(u8, "A", result.stdout.items);
    try std.testing.expectEqual(@as(u64, 10), result.steps);
}
