const std = @import("std");
const mb = @import("malbolge_free");
const hell = @import("hell");

// TAPE-V1: celdas de escritura única + re-lecturas direccionadas (random access).
//
// TAPE-V0 demostró construir un cero en runtime y leerlo una vez. Aquí se
// demuestra el mecanismo de puntero: redirigir `d` con MOVD + relleno de NOPs
// (tracking estático, sin saltos) y releer celdas YA ejecutadas en cualquier
// orden. La restricción honesta: en código en línea recta, tras c>126 un MOVD
// solo puede releer celdas ya ejecutadas (su valor final es estable porque
// cada celda se toca una sola vez); leer DATA prístina por delante de `c`
// es imposible sin saltos (fase brackets, pendiente).
//
// Programa (326 instrucciones, línea recta; d==c salvo tras cada MOVD):
//   0..119   NOP x120       (a=0 se conserva)
//   120      OPR            (auto: 36 -> crazy(0,36)=29524, a=29524)
//   121      OUT            (emite 29524%256 = 84)
//   122..213 NOP x92
//   214      OPR            (auto: 36 -> crazy(29524,36)=0, a=0)
//   215      MOVD           (lee mem[215]=107 -> d=108)
//   216..227 NOP x12        (d: 108 -> 120)
//   228      R_MOVD (ROT)   (relee mem[120]=29524, punto fijo, a=29524)
//   229      OUT            (emite 84: prueba la relectura de A)
//   230      MOVD           (lee mem[122]=NOP cifrado='y'=121 -> d=122)
//   231..322 NOP x92        (d: 122 -> 214)
//   323      R_MOVD (ROT)   (relee mem[214]=0, a=0)
//   324      OUT            (emite 0: prueba la relectura de B)
//   325      HALT
// stdout esperado = [84, 84, 0], 326 pasos.

test "tape-v1 math: immediates de redirección y paddings" {
    // Primera redirección: MOVD@215 lee su propia celda (107) -> d=108,
    // 12 NOPs llevan d a 120.
    try std.testing.expectEqual(@as(u8, 107), hell.emitCommandToChar(40, 215));
    try std.testing.expectEqual(@as(usize, 12), 120 - (107 + 1));
    // Segunda redirección: MOVD@230 lee mem[122], el NOP cifrado.
    const nop122 = hell.emitCommandToChar(68, 122);
    try std.testing.expectEqual(@as(u8, 40), nop122);
    const e122: u8 = mb.TRANSLATED[@as(usize, nop122 - 33)];
    try std.testing.expectEqual(@as(u8, 'y'), e122);
    try std.testing.expectEqual(@as(usize, 92), 214 - (@as(usize, e122) + 1));
    // Punto fijo de rotate: la relectura de A vuelve a dar 29524.
    try std.testing.expectEqual(@as(u128, 29524), mb.rotate(29524, 10));
    // Construcción del cero (autocontenida, igual que v0).
    try std.testing.expectEqual(@as(u128, 29524), mb.crazy(0, 36, 10));
    try std.testing.expectEqual(@as(u128, 0), mb.crazy(29524, 36, 10));
    try std.testing.expectEqual(@as(u8, 36), hell.emitCommandToChar(62, 120));
    try std.testing.expectEqual(@as(u8, 36), hell.emitCommandToChar(62, 214));
}

test "tape-v1 e2e: dos celdas escritas, releídas fuera de orden" {
    const allocator = std.testing.allocator;
    // k2 se deriva de la máquina (no a mano): si el cifrado cambiara,
    // el layout se adapta solo y el e2e sigue siendo la verdad.
    const nop122 = hell.emitCommandToChar(68, 122);
    const e122: usize = mb.TRANSLATED[@as(usize, nop122 - 33)];
    const k2: usize = 214 - (e122 + 1);

    var src = std.ArrayListUnmanaged(u8).empty;
    defer src.deinit(allocator);
    try src.appendSlice(allocator, ".CODE\n");
    var i: usize = 0;
    while (i < 120) : (i += 1) try src.appendSlice(allocator, "  NOP\n");
    try src.appendSlice(allocator, "  OPR\n"); // 120
    try src.appendSlice(allocator, "  OUT\n"); // 121
    i = 0;
    while (i < 92) : (i += 1) try src.appendSlice(allocator, "  NOP\n"); // 122..213
    try src.appendSlice(allocator, "  OPR\n"); // 214
    try src.appendSlice(allocator, "  MOVD\n"); // 215
    i = 0;
    while (i < 12) : (i += 1) try src.appendSlice(allocator, "  NOP\n"); // 216..227
    try src.appendSlice(allocator, "  R_MOVD\n"); // 228 ROT
    try src.appendSlice(allocator, "  OUT\n"); // 229
    try src.appendSlice(allocator, "  MOVD\n"); // 230
    i = 0;
    while (i < k2) : (i += 1) try src.appendSlice(allocator, "  NOP\n"); // 231..
    try src.appendSlice(allocator, "  R_MOVD\n"); // ROT relectura de B
    try src.appendSlice(allocator, "  OUT\n");
    try src.appendSlice(allocator, "  HALT\n");

    var parser = hell.Parser.init(src.items);
    var program = try parser.parse(allocator);
    defer program.deinit(allocator);
    var layout = try hell.resolveLayout(&program, allocator);
    defer layout.deinit(allocator);
    try std.testing.expectEqual(@as(usize, 326), layout.instructions.items.len);
    var emitted = try hell.emit(&layout, allocator);
    defer emitted.deinit(allocator);

    var core = mb.MalbolgeCore.initFreeAssisted(allocator, 10, 59049, .fixed);
    defer core.deinit();
    try core.load(emitted.slice());
    var res = try core.run(1000, &.{});
    defer res.stdout.deinit(allocator);

    try std.testing.expectEqualStrings("HALTED", res.status);
    try std.testing.expectEqual(@as(u64, layout.instructions.items.len), res.steps);
    try std.testing.expectEqual(@as(usize, 3), res.stdout.items.len);
    try std.testing.expectEqual(@as(u8, 84), res.stdout.items[0]);
    try std.testing.expectEqual(@as(u8, 84), res.stdout.items[1]);
    try std.testing.expectEqual(@as(u8, 0), res.stdout.items[2]);
}
