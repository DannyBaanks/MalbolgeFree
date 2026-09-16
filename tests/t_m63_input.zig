const std = @import("std");
const backend = @import("backend");
const hell = @import("hell");
const mb = @import("malbolge_free");

// M6.3 gate: input (,) y EOF. La cinta Free se coloca fuera del código y las
// primitivas D_REWIND compensan el d++ automático entre accesos sucesivos.

fn imageFor(ops: []const backend.Op, allocator: std.mem.Allocator) ![]u8 {
    const size = 9 + ops.len * 12;
    var bytes = try allocator.alloc(u8, size);
    @memset(bytes, 0);
    @memcpy(bytes[0..5], "BFIR1");
    std.mem.writeInt(u32, bytes[5..9], @intCast(ops.len), .little);
    for (ops, 0..) |op, index| {
        const offset = 9 + index * 12;
        bytes[offset] = @intFromEnum(op);
        std.mem.writeInt(u32, bytes[offset + 8 ..][0..4], @intCast(index), .little);
    }
    return bytes;
}

test "M6.3 input: linear echo devuelve el byte recibido" {
    const allocator = std.testing.allocator;
    // Programa: , (input) . (output) — debería hacer echo
    const bytes = try imageFor(&.{ .input, .output }, allocator);
    defer allocator.free(bytes);

    var be_image = try backend.decode(bytes, allocator);
    defer be_image.deinit(allocator);
    var lowered = try backend.lowerLinear(&be_image, allocator);
    defer lowered.deinit(allocator);

    var parser = hell.Parser.init(lowered.slice());
    var program = try parser.parse(allocator);
    defer program.deinit(allocator);
    var layout = try hell.resolveLayout(&program, allocator);
    defer layout.deinit(allocator);
    var emitted = try hell.emit(&layout, allocator);
    defer emitted.deinit(allocator);

    var core = mb.MalbolgeCore.initFreeAssisted(allocator, 10, 59049, .fixed);
    defer core.deinit();
    try core.load(emitted.slice());
    var res = try core.run(1000, "A");
    defer res.stdout.deinit(allocator);

    try std.testing.expectEqualStrings("HALTED", res.status);
    try std.testing.expectEqual(@as(usize, 1), res.stdout.items.len);
    try std.testing.expectEqual(@as(u8, 'A'), res.stdout.items[0]);
}

test "M6.3 input: EOF se almacena como cero" {
    const allocator = std.testing.allocator;
    const bytes = try imageFor(&.{ .input, .output }, allocator);
    defer allocator.free(bytes);

    var be_image = try backend.decode(bytes, allocator);
    defer be_image.deinit(allocator);
    var lowered = try backend.lowerLinear(&be_image, allocator);
    defer lowered.deinit(allocator);

    var parser = hell.Parser.init(lowered.slice());
    var program = try parser.parse(allocator);
    defer program.deinit(allocator);
    var layout = try hell.resolveLayout(&program, allocator);
    defer layout.deinit(allocator);
    var emitted = try hell.emit(&layout, allocator);
    defer emitted.deinit(allocator);

    var core = mb.MalbolgeCore.initFreeAssisted(allocator, 10, 59049, .fixed);
    defer core.deinit();
    try core.load(emitted.slice());
    var res = try core.run(1000, "");
    defer res.stdout.deinit(allocator);

    try std.testing.expectEqualStrings("HALTED", res.status);
    try std.testing.expectEqual(@as(usize, 1), res.stdout.items.len);
    try std.testing.expectEqual(@as(u8, 0), res.stdout.items[0]);
}
