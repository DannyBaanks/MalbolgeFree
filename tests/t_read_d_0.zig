const std = @import("std");
const mb = @import("malbolge_free");
const hell = @import("hell");

test "READ_D_0 HeLL roundtrip: parse → layout → emit → VM" {
    var lowered = std.ArrayListUnmanaged(u8).empty;
    defer lowered.deinit(std.testing.allocator);
    try lowered.appendSlice(std.testing.allocator, ".CODE\n  READ_D_0\n  OUT\n  HALT\n");

    var parser = hell.Parser.init(lowered.items);
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    var emitted = try hell.emit(&layout, std.testing.allocator);
    defer emitted.deinit(std.testing.allocator);

    var core = mb.MalbolgeCore.initFreeAssisted(std.testing.allocator, 10, null, .fixed);
    defer core.deinit();
    try core.load(emitted.slice());
    var result = try core.run(100, "");
    defer result.stdout.deinit(std.testing.allocator);

    try std.testing.expectEqualStrings("HALTED", result.status);
    // cell[0] = source[0] = emitCommandToChar(69, 0) = 69 ('E')
    // READ_D_0: a = cell[0] = 69
    // OUT: outputs a % 256 = 69 = 'E'
    try std.testing.expectEqual(@as(usize, 1), result.stdout.items.len);
    try std.testing.expectEqual(@as(u8, 69), result.stdout.items[0]);
}

test "READ_D_0 does not modify cell[0] (encryption modifies cell[0] after, not READ_D_0)" {
    // READ_D_0 reads cell[0] without writing.
    // After the step, encryption modifies cell[c=0] = TRANSLATED[source[0]-33].
    // So cell[0] IS modified by encryption, NOT by READ_D_0 itself.
    // Second READ_D_0 reads the ENCRYPTED cell[0].
    var lowered = std.ArrayListUnmanaged(u8).empty;
    defer lowered.deinit(std.testing.allocator);
    try lowered.appendSlice(std.testing.allocator, ".CODE\n  READ_D_0\n  READ_D_0\n  OUT\n  HALT\n");

    var parser = hell.Parser.init(lowered.items);
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    var emitted = try hell.emit(&layout, std.testing.allocator);
    defer emitted.deinit(std.testing.allocator);

    var core = mb.MalbolgeCore.initFreeAssisted(std.testing.allocator, 10, null, .fixed);
    defer core.deinit();
    try core.load(emitted.slice());
    var result = try core.run(100, "");
    defer result.stdout.deinit(std.testing.allocator);

    try std.testing.expectEqualStrings("HALTED", result.status);
    // First READ_D_0: a = cell[0] = 69 ('E')
    // Encryption modifies cell[0] = TRANSLATED[69-33] = TRANSLATED[36] = 'p' (112)
    // Second READ_D_0: a = cell[0] = 112 ('p')
    // OUT: outputs 112 = 'p'
    try std.testing.expectEqual(@as(u8, 112), result.stdout.items[0]);
}

test "READ_D_0 bijection: rotate(bf, 10) for various bf values" {
    try std.testing.expectEqual(@as(u128, 0), mb.rotate(0, 10));
    try std.testing.expect(mb.rotate(1, 10) != 0);
    try std.testing.expect(mb.rotate(33, 10) != mb.rotate(34, 10));
    // rotate is a bijection: different inputs produce different outputs
    var seen = std.AutoHashMap(u128, void).init(std.testing.allocator);
    defer seen.deinit();
    var bf: u128 = 0;
    while (bf < 256) : (bf += 1) {
        const r = mb.rotate(bf, 10);
        try std.testing.expect(!seen.contains(r));
        try seen.put(r, {});
    }
}

test "READ_D_0 HeLL parser recognizes keyword" {
    var lowered = std.ArrayListUnmanaged(u8).empty;
    defer lowered.deinit(std.testing.allocator);
    try lowered.appendSlice(std.testing.allocator, ".CODE\n  READ_D_0\n  HALT\n");

    var parser = hell.Parser.init(lowered.items);
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(usize, 1), program.blocks.items.len);
    try std.testing.expectEqual(@as(usize, 2), program.blocks.items[0].instructions.items.len);
    try std.testing.expectEqual(hell.Opcode.read_d_0, program.blocks.items[0].instructions.items[0].opcode);
    try std.testing.expectEqual(hell.Opcode.halt, program.blocks.items[0].instructions.items[1].opcode);
}

test "JMP_A HeLL parser and opcode table" {
    var source = std.ArrayListUnmanaged(u8).empty;
    defer source.deinit(std.testing.allocator);
    try source.appendSlice(std.testing.allocator, ".CODE\n  JMP_A\n  HALT\n");

    var parser = hell.Parser.init(source.items);
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    try std.testing.expectEqual(hell.Opcode.jmp_a, program.blocks.items[0].instructions.items[0].opcode);
    const entry = hell.classifyInstruction(program.blocks.items[0].instructions.items[0]);
    try std.testing.expectEqual(hell.MalbolgeCommand.jmp_a, entry.malbolge_command);
}

test "JMP_A jumps to the accumulator value" {
    var source = std.ArrayListUnmanaged(u8).empty;
    defer source.deinit(std.testing.allocator);
    try source.appendSlice(std.testing.allocator, ".CODE\n  IN\n  JMP_A\n  NOP\n  NOP\n  HALT\n");

    var parser = hell.Parser.init(source.items);
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);
    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);
    var emitted = try hell.emit(&layout, std.testing.allocator);
    defer emitted.deinit(std.testing.allocator);

    var core = mb.MalbolgeCore.initFreeAssisted(std.testing.allocator, 10, null, .fixed);
    defer core.deinit();
    try core.load(emitted.slice());
    var result = try core.run(10, &.{3});
    defer result.stdout.deinit(std.testing.allocator);

    try std.testing.expectEqualStrings("HALTED", result.status);
    try std.testing.expectEqual(@as(u64, 3), result.steps);
}

test "READ_D_0 roundtrip: parse → layout → emit → VM verifies opcode 69" {
    var lowered = std.ArrayListUnmanaged(u8).empty;
    defer lowered.deinit(std.testing.allocator);
    try lowered.appendSlice(std.testing.allocator, ".CODE\n  READ_D_0\n  OUT\n  HALT\n");

    var parser = hell.Parser.init(lowered.items);
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    // Verify READ_D_0 maps to MalbolgeCommand.read_d_0 (opcode 69)
    const inst = layout.instructions.items[0];
    const entry = hell.classifyInstruction(hell.Instruction{
        .opcode = inst.opcode,
        .prefix = inst.prefix,
        .modifier = inst.modifier,
        .operand = inst.operand,
        .line = 0,
    });
    try std.testing.expectEqual(hell.MalbolgeCommand.read_d_0, entry.malbolge_command);

    var emitted = try hell.emit(&layout, std.testing.allocator);
    defer emitted.deinit(std.testing.allocator);

    // Verify source char at pos 0 decodes to opcode 69
    const ch = emitted.slice()[0];
    const pos_mod: u8 = @intCast(0 % 94);
    var cmd: u8 = (ch +% pos_mod) % 94;
    if (cmd < 33) cmd += 94;
    try std.testing.expectEqual(@as(u8, 69), cmd);
}

test "READ_D_0 output matches source char at position 0" {
    // Use HeLL to generate the program, then verify the output
    var lowered = std.ArrayListUnmanaged(u8).empty;
    defer lowered.deinit(std.testing.allocator);
    try lowered.appendSlice(std.testing.allocator, ".CODE\n  READ_D_0\n  OUT\n  HALT\n");

    var parser = hell.Parser.init(lowered.items);
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    var emitted = try hell.emit(&layout, std.testing.allocator);
    defer emitted.deinit(std.testing.allocator);

    // The source char at pos 0 IS the value that READ_D_0 will read
    const source_char = emitted.slice()[0];

    var core = mb.MalbolgeCore.initFreeAssisted(std.testing.allocator, 10, null, .fixed);
    defer core.deinit();
    try core.load(emitted.slice());
    var result = try core.run(100, "");
    defer result.stdout.deinit(std.testing.allocator);

    try std.testing.expectEqualStrings("HALTED", result.status);
    // READ_D_0 reads cell[0] = source_char, OUT outputs it
    try std.testing.expectEqual(@as(usize, 1), result.stdout.items.len);
    try std.testing.expectEqual(source_char, result.stdout.items[0]);
}
