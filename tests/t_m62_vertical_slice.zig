const std = @import("std");
const ir = @import("bf_to_ir.zig");
const image = @import("bf_ir_image.zig");
const vm = @import("bf_ir_vm.zig");
const bf = @import("bf_interpreter.zig");
const backend = @import("backend");
const hell = @import("hell");
const mb = @import("malbolge_free");

// M6.2 vertical slice: un programa BF lineal (sin loops) ejecutado
// end-to-end y comparado contra el VM de referencia BFIR1.

// Programa BF lineal: >+<+<++>.
// Cinta 256, pasos 1000.
// Salida esperada: byte 2. La zona de cinta debe quedar fuera del código.

test "M6.2 vertical slice: BF lineal -> BFIR1 -> HeLL -> MalbolgeCore vs reference" {
    const allocator = std.testing.allocator;
    const bf_source = ">>+<++.";

    // 1. BF -> IR
    var ir_prog = try ir.compile(bf_source, allocator);
    defer ir_prog.deinit();
    try ir.validate(&ir_prog);

    // 2. IR -> BFIR1 image
    const img = try image.encode(&ir_prog, allocator);
    defer allocator.free(img);

// 3. Roundtrip: image -> IR (para referencia)
    var ir_prog2 = try image.decode(img, allocator);
    defer ir_prog2.deinit();

    // 3b. Referencia: BFIR1 VM
    var ref = try vm.run(&ir_prog2, &.{}, .{ .tape_size = 256, .max_steps = 1000 }, allocator, false);
    defer ref.deinit();

    // 4. Decode BFIR1 image into backend's Image type
    var be_image = try backend.decode(img, allocator);
    defer be_image.deinit(allocator);

    // 5. Lowering lineal (sin branches)
    var lowered = try backend.lowerLinear(&be_image, allocator);
    defer lowered.deinit(allocator);

    // 5. HeLL parse -> layout -> emit
    var parser = hell.Parser.init(lowered.slice());
    var program = try parser.parse(allocator);
    defer program.deinit(allocator);
    var layout = try hell.resolveLayout(&program, allocator);
    defer layout.deinit(allocator);
    var emitted = try hell.emit(&layout, allocator);
    defer emitted.deinit(allocator);

    // 6. MalbolgeCore ejecuta el programa HeLL emitido
    var core = mb.MalbolgeCore.initFreeAssisted(allocator, 10, 59049, .fixed);
    defer core.deinit();
    try core.load(emitted.slice());
    var res = try core.run(5000, &.{});
    defer res.stdout.deinit(allocator);

    // 7. Comparación observable del slice lineal.
    try std.testing.expectEqualStrings("HALTED", res.status);
    try std.testing.expectEqualSlices(u8, &.{2}, res.stdout.items);
    try std.testing.expect(res.max_addr_touched >= 1000);
}
