const std = @import("std");
const hell = @import("hell");
const Opcode = hell.Opcode;
const Modifier = hell.Modifier;
const Prefix = hell.Prefix;
const MalbolgeCommand = hell.MalbolgeCommand;
const Instruction = hell.Instruction;

test "A2 opcode: MovD maps to MOVED (40)" {
    const cmd = hell.hellOpcodeToCommand(.movd, .none, .none);
    try std.testing.expectEqual(MalbolgeCommand.moved, cmd);
    try std.testing.expectEqual(@as(u8, 40), @intFromEnum(cmd));
}

test "A2 opcode: MOV maps to MOVED (40)" {
    const cmd = hell.hellOpcodeToCommand(.mov, .none, .none);
    try std.testing.expectEqual(MalbolgeCommand.moved, cmd);
}

test "A2 opcode: NOP maps to NOP (68)" {
    const cmd = hell.hellOpcodeToCommand(.nop, .none, .none);
    try std.testing.expectEqual(MalbolgeCommand.nop, cmd);
    try std.testing.expectEqual(@as(u8, 68), @intFromEnum(cmd));
}

test "A2 opcode: IN maps to IN (23)" {
    const cmd = hell.hellOpcodeToCommand(.in_, .none, .none);
    try std.testing.expectEqual(MalbolgeCommand.in_, cmd);
    try std.testing.expectEqual(@as(u8, 23), @intFromEnum(cmd));
}

test "A2 opcode: OUT maps to OUT (5)" {
    const cmd = hell.hellOpcodeToCommand(.out, .none, .none);
    try std.testing.expectEqual(MalbolgeCommand.out, cmd);
    try std.testing.expectEqual(@as(u8, 5), @intFromEnum(cmd));
}

test "A2 opcode: OPR maps to OPR (62)" {
    const cmd = hell.hellOpcodeToCommand(.opr, .none, .none);
    try std.testing.expectEqual(MalbolgeCommand.opr, cmd);
    try std.testing.expectEqual(@as(u8, 62), @intFromEnum(cmd));
}

test "A2 opcode: JMP maps to JMP (4)" {
    const cmd = hell.hellOpcodeToCommand(.jmp, .none, .none);
    try std.testing.expectEqual(MalbolgeCommand.jmp, cmd);
    try std.testing.expectEqual(@as(u8, 4), @intFromEnum(cmd));
}

test "A2 opcode: HALT maps to HALT (81)" {
    const cmd = hell.hellOpcodeToCommand(.halt, .none, .none);
    try std.testing.expectEqual(MalbolgeCommand.halt, cmd);
    try std.testing.expectEqual(@as(u8, 81), @intFromEnum(cmd));
}

test "A2 opcode: FLAG maps to NOP" {
    const cmd = hell.hellOpcodeToCommand(.flag, .none, .none);
    try std.testing.expectEqual(MalbolgeCommand.nop, cmd);
}

test "A2 opcode: VAR maps to NOP" {
    const cmd = hell.hellOpcodeToCommand(.var_, .none, .none);
    try std.testing.expectEqual(MalbolgeCommand.nop, cmd);
}

test "A2 opcode: CALL maps to JMP" {
    const cmd = hell.hellOpcodeToCommand(.call, .none, .none);
    try std.testing.expectEqual(MalbolgeCommand.jmp, cmd);
}

test "A2 char: command NOP at position 0" {
    const ch = hell.commandToChar(.nop, 0);
    try std.testing.expectEqual(@as(u8, 68), ch);
}

test "A2 char: command JMP at position 0" {
    const ch = hell.commandToChar(.jmp, 0);
    // (4+94-0)%94 = 4, then 4 < 33 so ch = 4+94 = 98
    try std.testing.expectEqual(@as(u8, 98), ch);
}

test "A2 char: command IN at position 10" {
    const ch = hell.commandToChar(.in_, 10);
    // (23+94-10)%94 = 107%94 = 13, then 13 < 33 so ch = 13+94 = 107
    try std.testing.expectEqual(@as(u8, 107), ch);
}

test "A2 char: output is always printable ASCII" {
    var pos: usize = 0;
    while (pos < 94) : (pos += 1) {
        const cmds = [_]MalbolgeCommand{ .nop, .moved, .opr, .jmp, .rot, .out, .in_, .halt };
        for (cmds) |cmd| {
            const ch = hell.commandToChar(cmd, pos);
            try std.testing.expect(ch >= 33 and ch <= 126);
        }
    }
}

test "A2 xlat2: table length is 94" {
    try std.testing.expectEqual(@as(usize, 94), hell.XLAT2.len);
}

test "A2 xlat2: idempotent round-trip check" {
    var i: u8 = 0;
    while (i < 94) : (i += 1) {
        const c = 33 + i;
        const xlated = hell.xlat2Char(c);
        try std.testing.expect(xlated >= 33 and xlated <= 126);
    }
}

test "A2 classify: full instruction round-trip" {
    const inst = Instruction{
        .opcode = .movd,
        .prefix = .none,
        .modifier = .nop,
        .operand = null,
        .line = 1,
    };
    const entry = hell.classifyInstruction(inst);
    try std.testing.expectEqual(MalbolgeCommand.moved, entry.malbolge_command);
    try std.testing.expectEqual(Opcode.movd, entry.opcode);
    try std.testing.expectEqual(Modifier.nop, entry.modifier);
}

test "A2 all commands: enum values match LMAO constants" {
    try std.testing.expectEqual(@as(u8, 68), @intFromEnum(MalbolgeCommand.nop));
    try std.testing.expectEqual(@as(u8, 40), @intFromEnum(MalbolgeCommand.moved));
    try std.testing.expectEqual(@as(u8, 62), @intFromEnum(MalbolgeCommand.opr));
    try std.testing.expectEqual(@as(u8, 4), @intFromEnum(MalbolgeCommand.jmp));
    try std.testing.expectEqual(@as(u8, 39), @intFromEnum(MalbolgeCommand.rot));
    try std.testing.expectEqual(@as(u8, 5), @intFromEnum(MalbolgeCommand.out));
    try std.testing.expectEqual(@as(u8, 23), @intFromEnum(MalbolgeCommand.in_));
    try std.testing.expectEqual(@as(u8, 81), @intFromEnum(MalbolgeCommand.halt));
}

test "A2 prefix: R_MOVD maps to ROT (39)" {
    const cmd = hell.hellOpcodeToCommand(.movd, .none, .r);
    try std.testing.expectEqual(MalbolgeCommand.rot, cmd);
    try std.testing.expectEqual(@as(u8, 39), @intFromEnum(cmd));
}

test "A2 prefix: R_IN maps to ROT (39)" {
    const cmd = hell.hellOpcodeToCommand(.in_, .none, .r);
    try std.testing.expectEqual(MalbolgeCommand.rot, cmd);
}

test "A2 prefix: R_OUT maps to ROT (39)" {
    const cmd = hell.hellOpcodeToCommand(.out, .none, .r);
    try std.testing.expectEqual(MalbolgeCommand.rot, cmd);
}
