const std = @import("std");
const hell = @import("hell");
const Parser = hell.Parser;
const Opcode = hell.Opcode;
const Section = hell.Section;

test "A3 layout: resolve simple HALT program" {
    var parser = Parser.init(".CODE\n  HALT");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(usize, 1), layout.code_size);
    try std.testing.expectEqual(@as(usize, 0), layout.data_size);
    try std.testing.expectEqual(@as(usize, 1), layout.instructions.items.len);
    try std.testing.expectEqual(Opcode.halt, layout.instructions.items[0].opcode);
    try std.testing.expectEqual(@as(usize, 0), layout.instructions.items[0].position);
}

test "A3 layout: NOP + HALT two instructions" {
    var parser = Parser.init(".CODE\n  NOP\n  HALT");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(usize, 2), layout.code_size);
    try std.testing.expectEqual(@as(usize, 0), layout.instructions.items[0].position);
    try std.testing.expectEqual(@as(usize, 1), layout.instructions.items[1].position);
    try std.testing.expectEqual(Opcode.nop, layout.instructions.items[0].opcode);
    try std.testing.expectEqual(Opcode.halt, layout.instructions.items[1].opcode);
}

test "A3 layout: data block accumulates values" {
    var parser = Parser.init(".DATA {\n  42\n  0\n  7\n}");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(usize, 0), layout.code_size);
    try std.testing.expectEqual(@as(usize, 3), layout.data_size);
    try std.testing.expectEqual(@as(u32, 42), layout.data_values.items[0]);
    try std.testing.expectEqual(@as(u32, 0), layout.data_values.items[1]);
    try std.testing.expectEqual(@as(u32, 7), layout.data_values.items[2]);
}

test "A3 layout: code + data combined" {
    var parser = Parser.init(".CODE\n  NOP\n.DATA {\n  10\n  20\n}");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(usize, 1), layout.code_size);
    try std.testing.expectEqual(@as(usize, 2), layout.data_size);
    try std.testing.expectEqual(@as(u32, 10), layout.data_values.items[0]);
    try std.testing.expectEqual(@as(u32, 20), layout.data_values.items[1]);
}

test "A3 layout: full simple cat instruction count" {
    const src =
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
    var parser = Parser.init(src);
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(usize, 6), layout.code_size);
    try std.testing.expectEqual(@as(usize, 0), layout.data_size);
    try std.testing.expectEqual(@as(usize, 12), layout.instructions.items.len);
}

test "A3 layout: labels are tracked from code blocks" {
    var parser = Parser.init(".CODE\nloop:\n  NOP");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(usize, 1), layout.code_size);
    try std.testing.expectEqual(@as(usize, 1), layout.instructions.items.len);
    try std.testing.expectEqual(Opcode.nop, layout.instructions.items[0].opcode);
    try std.testing.expectEqual(@as(usize, 0), layout.code_positions.get("loop").?);
}

test "A3 layout: data label uses value offset" {
    var parser = Parser.init(".DATA {\n  42\n target:\n  43\n}");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(usize, 1), layout.data_positions.get("target").?);
}

test "A3 layout: forward and backward labels resolve" {
    var parser = Parser.init(".CODE\n  JMP end\nstart:\n  NOP\nend:\n  HALT\n  JMP start");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(usize, 2), layout.code_positions.get("end").?);
    try std.testing.expectEqual(@as(usize, 1), layout.code_positions.get("start").?);
    try std.testing.expectEqual(hell.Operand.number, std.meta.activeTag(layout.instructions.items[0].operand.?));
    try std.testing.expectEqual(@as(u32, 2), layout.instructions.items[0].operand.?.number);
    try std.testing.expectEqual(@as(u32, 1), layout.instructions.items[3].operand.?.number);
}

test "A3 layout: duplicate labels are rejected" {
    var parser = Parser.init(".CODE\na:\n  NOP\na:\n  HALT");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);
    try std.testing.expectError(error.DuplicateLabel, hell.resolveLayout(&program, std.testing.allocator));
}

test "A3 layout: unknown label is rejected" {
    var parser = Parser.init(".CODE\n  JMP missing");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);
    try std.testing.expectError(error.UnknownLabel, hell.resolveLayout(&program, std.testing.allocator));
}

test "A3 layout: multiple code sections accumulate" {
    var parser = Parser.init(".CODE\n  NOP\n.CODE\n  HALT");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(usize, 2), layout.code_size);
    try std.testing.expectEqual(Opcode.nop, layout.instructions.items[0].opcode);
    try std.testing.expectEqual(Opcode.halt, layout.instructions.items[1].opcode);
}

test "A3 layout: empty program" {
    var parser = Parser.init("");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(usize, 0), layout.code_size);
    try std.testing.expectEqual(@as(usize, 0), layout.data_size);
    try std.testing.expectEqual(@as(usize, 0), layout.instructions.items.len);
}
