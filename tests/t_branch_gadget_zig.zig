const std = @import("std");
const mb = @import("malbolge_free");
const hell = @import("hell");

// Busca gadgets CHASE con divergencia de flujo de control dependiente de `a`
// en la VM real (no en modelo Python).
//
// Plantilla por candidato:
//   IN, <prefijo>, JMP, NOP, NOP, HALT
// Sin OUT: si steps/status difieren entre stdin 0x00 y 0x01, la divergencia
// es de flujo de control (distinto destino de CHASE o distinto opcode
// auto-modificado), no un mero eco de datos.

const OpChoice = enum { rot, movd, opr, nop };

fn mnemonic(op: OpChoice) []const u8 {
    return switch (op) {
        .rot => "R_MOVD",
        .movd => "MOVD",
        .opr => "OPR",
        .nop => "NOP",
    };
}

const Outcome = struct {
    status_is_halted: bool,
    steps: u64,
    stdout_len: usize,
    stdout0: u8,
};

fn runOnce(allocator: std.mem.Allocator, source: []const u8, input: []const u8) !Outcome {
    var parser = hell.Parser.init(source);
    var program = try parser.parse(allocator);
    defer program.deinit(allocator);
    var layout = try hell.resolveLayout(&program, allocator);
    defer layout.deinit(allocator);
    var emitted = try hell.emit(&layout, allocator);
    defer emitted.deinit(allocator);
    // mem_limit 59049 = paridad Classic (Translator/Autobolge); también evita
    // overflow de c/d en modo no acotado cuando CHASE salta lejos.
    var core = mb.MalbolgeCore.initFreeAssisted(allocator, 10, null, .fixed);
    defer core.deinit();
    try core.load(emitted.slice());
    var res = try core.run(200, input);
    defer res.stdout.deinit(allocator);
    return .{
        .status_is_halted = std.mem.eql(u8, res.status, "HALTED"),
        .steps = res.steps,
        .stdout_len = res.stdout.items.len,
        .stdout0 = if (res.stdout.items.len > 0) res.stdout.items[0] else 0,
    };
}

fn diverges(a: Outcome, b: Outcome) bool {
    // Sin OUT en la plantilla, stdout siempre vacío; cualquier diferencia
    // en steps/status es divergencia de control.
    return (a.status_is_halted != b.status_is_halted) or (a.steps != b.steps);
}

test "branch gadget: IN-driven control-flow divergence exists in real VM" {
    const allocator = std.testing.allocator;
    const choices = [_]OpChoice{ .rot, .movd, .opr, .nop };
    var found: usize = 0;

    // profundidades 0..4 (1+4+16+64+256 = 341 plantillas x2 ejecuciones)
    var depth: usize = 0;
    while (depth <= 4) : (depth += 1) {
        // contador en base 4 de `depth` dígitos
        var total: usize = 1;
        var i: usize = 0;
        while (i < depth) : (i += 1) total *= 4;
        var idx: usize = 0;
        while (idx < total) : (idx += 1) {
            var src_buf = std.ArrayListUnmanaged(u8).empty;
            defer src_buf.deinit(allocator);
            try src_buf.appendSlice(allocator, ".CODE\n  IN\n");
            var tmp = idx;
            var k: usize = 0;
            while (k < depth) : (k += 1) {
                const c = choices[tmp % 4];
                tmp /= 4;
                try src_buf.appendSlice(allocator, "  ");
                try src_buf.appendSlice(allocator, mnemonic(c));
                try src_buf.appendSlice(allocator, "\n");
            }
            try src_buf.appendSlice(allocator, "  JMP\n  NOP\n  NOP\n  HALT\n");
            const src = src_buf.items;

            const r0 = try runOnce(allocator, src, &.{0});
            const r1 = try runOnce(allocator, src, &.{1});
            if (diverges(r0, r1)) {
                found += 1;
                if (found <= 5) {
                    std.debug.print("GADGET depth={d} idx={d} steps0={d} steps1={d} halted0={any} halted1={any}\n", .{ depth, idx, r0.steps, r1.steps, r0.status_is_halted, r1.status_is_halted });
                }
            }
        }
    }
    std.debug.print("TOTAL_DIVERGENT={d}\n", .{found});
    try std.testing.expect(found > 0);
}
