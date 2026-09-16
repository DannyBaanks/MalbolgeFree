const std = @import("std");
const hell = @import("hell");
const Tokenizer = hell.Tokenizer;
const TokenType = hell.TokenType;
const Parser = hell.Parser;
const Opcode = hell.Opcode;
const Section = hell.Section;
const Modifier = hell.Modifier;
const Prefix = hell.Prefix;
const Operand = hell.Operand;

test "A1 tokenizer: section keywords" {
    var tok = Tokenizer.init(".CODE\n.DATA");
    try std.testing.expectEqual(TokenType.dot_code, tok.nextToken().type);
    _ = tok.nextToken();
    try std.testing.expectEqual(TokenType.dot_data, tok.nextToken().type);
}

test "A1 tokenizer: all opcodes" {
    var tok = Tokenizer.init("MOV MovD NOP In Out Opr Jmp Halt FLAG VAR CALL");
    const expected = [_]TokenType{ .keyword_mov, .keyword_movd, .keyword_nop, .keyword_in, .keyword_out, .keyword_opr, .keyword_jmp, .keyword_halt, .keyword_flag, .keyword_var, .keyword_call };
    for (expected) |exp| {
        try std.testing.expectEqual(exp, tok.nextToken().type);
    }
}

test "A1 tokenizer: labels and colons" {
    var tok = Tokenizer.init("loop:\n  ENTRY:");
    try std.testing.expectEqual(TokenType.label, tok.nextToken().type);
    try std.testing.expectEqual(TokenType.colon, tok.nextToken().type);
    _ = tok.nextToken();
    try std.testing.expectEqual(TokenType.label, tok.nextToken().type);
    try std.testing.expectEqual(TokenType.colon, tok.nextToken().type);
}

test "A1 tokenizer: braces and slash" {
    var tok = Tokenizer.init("{ } /");
    try std.testing.expectEqual(TokenType.lbrace, tok.nextToken().type);
    try std.testing.expectEqual(TokenType.rbrace, tok.nextToken().type);
    try std.testing.expectEqual(TokenType.slash, tok.nextToken().type);
}

test "A1 tokenizer: numbers" {
    var tok = Tokenizer.init("42 0 3");
    try std.testing.expectEqualStrings("42", tok.nextToken().lexeme);
    try std.testing.expectEqualStrings("0", tok.nextToken().lexeme);
    try std.testing.expectEqualStrings("3", tok.nextToken().lexeme);
}

test "A1 tokenizer: question and minus" {
    var tok = Tokenizer.init("?-");
    try std.testing.expectEqual(TokenType.question, tok.nextToken().type);
    try std.testing.expectEqual(TokenType.minus, tok.nextToken().type);
}

test "A1 tokenizer: single-line comments skipped" {
    var tok = Tokenizer.init("// comment\nIN");
    try std.testing.expectEqual(TokenType.eol, tok.nextToken().type);
    try std.testing.expectEqual(TokenType.keyword_in, tok.nextToken().type);
}

test "A1 tokenizer: multi-line comments skipped" {
    var tok = Tokenizer.init("/* block */\nMOV");
    try std.testing.expectEqual(TokenType.eol, tok.nextToken().type);
    try std.testing.expectEqual(TokenType.keyword_mov, tok.nextToken().type);
}

test "A1 tokenizer: prefix split R_MOVD" {
    var tok = Tokenizer.init("R_MOVD");
    const t1 = tok.nextToken();
    try std.testing.expectEqual(TokenType.prefix_r, t1.type);
    try std.testing.expectEqualStrings("R_", t1.lexeme);
    const t2 = tok.nextToken();
    try std.testing.expectEqual(TokenType.keyword_movd, t2.type);
    try std.testing.expectEqualStrings("MOVD", t2.lexeme);
}

test "A1 tokenizer: prefix split U_NOP" {
    var tok = Tokenizer.init("U_NOP");
    try std.testing.expectEqual(TokenType.prefix_u, tok.nextToken().type);
    try std.testing.expectEqual(TokenType.keyword_nop, tok.nextToken().type);
}

test "A1 tokenizer: prefix split C_OPR" {
    var tok = Tokenizer.init("C_OPR");
    try std.testing.expectEqual(TokenType.prefix_c, tok.nextToken().type);
    try std.testing.expectEqual(TokenType.keyword_opr, tok.nextToken().type);
}

test "A1 tokenizer: standalone R_ U_ C_" {
    var tok = Tokenizer.init("R_ U_ C_");
    try std.testing.expectEqual(TokenType.prefix_r, tok.nextToken().type);
    try std.testing.expectEqual(TokenType.prefix_u, tok.nextToken().type);
    try std.testing.expectEqual(TokenType.prefix_c, tok.nextToken().type);
}

test "A1 tokenizer: IN as opcode not label in code" {
    var tok = Tokenizer.init("IN:\n  In/Nop");
    try std.testing.expectEqual(TokenType.keyword_in, tok.nextToken().type);
    try std.testing.expectEqual(TokenType.colon, tok.nextToken().type);
    _ = tok.nextToken();
    try std.testing.expectEqual(TokenType.keyword_in, tok.nextToken().type);
}

test "A1 parser: .CODE HALT" {
    var parser = Parser.init(".CODE\n  HALT");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);
    try std.testing.expectEqual(@as(usize, 1), program.blocks.items.len);
    try std.testing.expectEqual(Section.code, program.blocks.items[0].section);
    try std.testing.expectEqual(@as(usize, 1), program.blocks.items[0].instructions.items.len);
    try std.testing.expectEqual(Opcode.halt, program.blocks.items[0].instructions.items[0].opcode);
}

test "A1 parser: label + MOVD" {
    var parser = Parser.init(".CODE\nloop:\n  MOVD loop");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);
    try std.testing.expectEqual(@as(usize, 1), program.blocks.items.len);
    const inst = program.blocks.items[0].instructions.items[0];
    try std.testing.expect(inst.operand != null);
    try std.testing.expect(inst.operand.? == .label);
}

test "A1 parser: prefix R_ + modifier /Nop" {
    var parser = Parser.init(".CODE\n  R_MOVD\n  NOP");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);
    const insts = program.blocks.items[0].instructions;
    try std.testing.expectEqual(@as(usize, 2), insts.items.len);
    try std.testing.expectEqual(Prefix.r, insts.items[0].prefix);
    try std.testing.expectEqual(Opcode.movd, insts.items[0].opcode);
    try std.testing.expectEqual(Opcode.nop, insts.items[1].opcode);
}

test "A1 parser: multiple sections .CODE + .DATA" {
    var parser = Parser.init(".CODE\n  NOP\n.DATA {\n  42\n}");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);
    try std.testing.expectEqual(@as(usize, 2), program.blocks.items.len);
    try std.testing.expectEqual(Section.code, program.blocks.items[0].section);
    try std.testing.expectEqual(Section.data, program.blocks.items[1].section);
}

test "A1 parser: full simple cat HeLL" {
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

    try std.testing.expectEqual(@as(usize, 2), program.blocks.items.len);

    const code = program.blocks.items[0];
    try std.testing.expectEqual(@as(usize, 6), code.instructions.items.len);
    try std.testing.expectEqual(Opcode.movd, code.instructions.items[0].opcode);
    try std.testing.expectEqual(Modifier.nop, code.instructions.items[0].modifier);
    try std.testing.expectEqual(Prefix.none, code.instructions.items[0].prefix);
    try std.testing.expectEqual(Opcode.jmp, code.instructions.items[1].opcode);

    const data = program.blocks.items[1];
    try std.testing.expectEqual(@as(usize, 6), data.instructions.items.len);
    try std.testing.expectEqual(Opcode.movd, data.instructions.items[0].opcode);
    try std.testing.expectEqual(Prefix.r, data.instructions.items[0].prefix);
    try std.testing.expectEqual(Opcode.in_, data.instructions.items[1].opcode);
    try std.testing.expectEqual(.register_a, data.instructions.items[1].operand.?);
}

test "A1 parser: bare HALT without section" {
    var parser = Parser.init("HALT");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);
    try std.testing.expectEqual(@as(usize, 0), program.blocks.items.len);
}

test "A1 parser: comment-only input" {
    var parser = Parser.init("// just a comment\n// another");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);
    try std.testing.expectEqual(@as(usize, 0), program.blocks.items.len);
}

test "A1 parser: MODIFIER /MovD on MovD" {
    var parser = Parser.init(".CODE\n  MovD/MovD");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);
    const inst = program.blocks.items[0].instructions.items[0];
    try std.testing.expectEqual(Modifier.movd, inst.modifier);
}

test "A1 parser: keyword IN used as label name" {
    var parser = Parser.init(".CODE\nIN:\n  NOP");
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);
    try std.testing.expectEqual(@as(usize, 1), program.blocks.items.len);
    try std.testing.expectEqual(@as(usize, 1), program.blocks.items[0].instructions.items.len);
    try std.testing.expectEqual(Opcode.nop, program.blocks.items[0].instructions.items[0].opcode);
}
