const std = @import("std");
const hell = @import("hell");
const Parser = hell.Parser;

const CAT_HELL =
    \\.CODE
    \\MOVD:
    \\  MovD/Nop
    \\  Jmp
    \\IN:
    \\  In/Nop
    \\  Jmp
    \\OUT:
    \\  Out/Nop
    \\  Jmp
    \\.DATA {
    \\loop:
    \\  R_MOVD
    \\ENTRY:
    \\  IN ?-
    \\  R_IN
    \\  OUT ?-
    \\  R_OUT
    \\  MOVD loop
    \\}
;

test "A6 cat: parse HeLL source" {
    var parser = Parser.init(CAT_HELL);
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(usize, 2), program.blocks.items.len);
    try std.testing.expectEqual(hell.Section.code, program.blocks.items[0].section);
    try std.testing.expectEqual(hell.Section.data, program.blocks.items[1].section);
}

test "A6 cat: resolve layout" {
    var parser = Parser.init(CAT_HELL);
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(usize, 6), layout.code_size);
    try std.testing.expectEqual(@as(usize, 0), layout.data_size);
    try std.testing.expectEqual(@as(usize, 12), layout.instructions.items.len);
}

test "A6 cat: emit valid Malbolge" {
    var parser = Parser.init(CAT_HELL);
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    var emitted = try hell.emit(&layout, std.testing.allocator);
    defer emitted.deinit(std.testing.allocator);

    const src = emitted.slice();
    try std.testing.expect(src.len > 0);

    for (src) |ch| {
        try std.testing.expect(ch >= 33 and ch <= 126);
    }
}

test "A6 cat: emit produces 12 characters" {
    var parser = Parser.init(CAT_HELL);
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    var emitted = try hell.emit(&layout, std.testing.allocator);
    defer emitted.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(usize, 12), emitted.slice().len);
}

test "A6 cat: emitted source is valid Malbolge format" {
    var parser = Parser.init(CAT_HELL);
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    var emitted = try hell.emit(&layout, std.testing.allocator);
    defer emitted.deinit(std.testing.allocator);

    const src = emitted.slice();
    try std.testing.expect(src.len >= 1);
    try std.testing.expect(src.len <= 59049);
}

test "A6 cat: labels resolve to correct positions" {
    var parser = Parser.init(CAT_HELL);
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(usize, 0), layout.code_positions.get("MOVD").?);
    try std.testing.expectEqual(@as(usize, 2), layout.code_positions.get("IN").?);
    try std.testing.expectEqual(@as(usize, 4), layout.code_positions.get("OUT").?);
    try std.testing.expectEqual(@as(usize, 6), layout.data_positions.get("loop").?);
    try std.testing.expectEqual(@as(usize, 7), layout.data_positions.get("ENTRY").?);
}

test "A6 cat: R_MOVD maps to ROT in emitted output" {
    var parser = Parser.init(CAT_HELL);
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    const loop_pos = layout.data_positions.get("loop").?;
    const inst = layout.instructions.items[loop_pos];
    const entry = hell.classifyInstruction(.{
        .opcode = inst.opcode,
        .prefix = inst.prefix,
        .modifier = inst.modifier,
        .operand = inst.operand,
        .line = 0,
    });
    try std.testing.expectEqual(hell.MalbolgeCommand.rot, entry.malbolge_command);
}
