const std = @import("std");
const mb = @import("malbolge_free");
const hell = @import("hell");

// TAPE-V0: modelo de cinta BF sobre memoria Malbolge + cero construido en runtime.
//
// Problema: la fuente Malbolge solo admite 33..126, así que un literal 0 no
// existe en el programa inicial. Pero 36 ('$') no tiene ningún trit 2
// (36 = 1100_3), y con eso:
//   OPR con a=0 sobre celda 36  -> crazy(0,36,10) = 29524 (todo unos)
//   OPR con a=29524 sobre celda 36 -> crazy(29524,36,10) = 0
// Luego ROT carga ese 0 con a=rotate(0)=0 (cero se preserva) y OUT lo observa.
//
// Programa (línea recta, sin saltos; d==c en todo momento salvo tras el MOVD):
//   0..25   NOP x26        (a=0 se conserva)
//   26      OPR            (celda auto: 36 -> 29524, a=29524)
//   27      OUT            (emite 29524%256 = 84)
//   28..119 NOP x92        (a=29524 se conserva)
//   120     OPR            (celda auto: 36 -> 0, a=0)
//   121     MOVD           (d: 121 -> mem[121]=107 -> 108 tras d++)
//   122..133 NOP x12       (d: 108 -> 120)
//   134     R_MOVD (ROT)   (lee mem[120]=0, a=0)
//   135     OUT            (emite 0)
//   136     HALT
// Total: 137 instrucciones, 137 pasos, stdout = [84, 0].

test "tape-v0 math: zero construction from printable 36" {
    // 36 = '$', ternario 0000001100: sin doses.
    try std.testing.expectEqual(@as(u128, 29524), mb.crazy(0, 36, 10));
    try std.testing.expectEqual(@as(u128, 0), mb.crazy(29524, 36, 10));
    try std.testing.expectEqual(@as(u128, 0), mb.rotate(0, 10));
    try std.testing.expectEqual(@as(u128, 84), @as(u128, 29524 % 256));
    // Alineación posicional: OPR en pos 26 y 120 parte del char 36.
    try std.testing.expectEqual(@as(u8, 36), hell.emitCommandToChar(62, 26));
    try std.testing.expectEqual(@as(u8, 36), hell.emitCommandToChar(62, 120));
    // El MOVD en 121 lee su propia celda (107) y deja d=108 tras d++.
    try std.testing.expectEqual(@as(u8, 107), hell.emitCommandToChar(40, 121));
}

test "tape-v0 e2e: runtime zero built, loaded via ROT, observed via OUT" {
    const allocator = std.testing.allocator;
    var src = std.ArrayListUnmanaged(u8).empty;
    defer src.deinit(allocator);
    try src.appendSlice(allocator, ".CODE\n");
    var i: usize = 0;
    while (i < 26) : (i += 1) try src.appendSlice(allocator, "  NOP\n");
    try src.appendSlice(allocator, "  OPR\n"); // 26
    try src.appendSlice(allocator, "  OUT\n"); // 27
    i = 0;
    while (i < 92) : (i += 1) try src.appendSlice(allocator, "  NOP\n"); // 28..119
    try src.appendSlice(allocator, "  OPR\n"); // 120
    try src.appendSlice(allocator, "  MOVD\n"); // 121
    i = 0;
    while (i < 12) : (i += 1) try src.appendSlice(allocator, "  NOP\n"); // 122..133
    try src.appendSlice(allocator, "  R_MOVD\n"); // 134 ROT
    try src.appendSlice(allocator, "  OUT\n"); // 135
    try src.appendSlice(allocator, "  HALT\n"); // 136

    var parser = hell.Parser.init(src.items);
    var program = try parser.parse(allocator);
    defer program.deinit(allocator);
    var layout = try hell.resolveLayout(&program, allocator);
    defer layout.deinit(allocator);
    try std.testing.expectEqual(@as(usize, 137), layout.instructions.items.len);
    var emitted = try hell.emit(&layout, allocator);
    defer emitted.deinit(allocator);

    var core = mb.MalbolgeCore.initFreeAssisted(allocator, 10, 59049, .fixed);
    defer core.deinit();
    try core.load(emitted.slice());
    var res = try core.run(500, &.{});
    defer res.stdout.deinit(allocator);

    try std.testing.expectEqualStrings("HALTED", res.status);
    try std.testing.expectEqual(@as(u64, 137), res.steps);
    try std.testing.expectEqual(@as(usize, 2), res.stdout.items.len);
    try std.testing.expectEqual(@as(u8, 84), res.stdout.items[0]);
    try std.testing.expectEqual(@as(u8, 0), res.stdout.items[1]);
}
