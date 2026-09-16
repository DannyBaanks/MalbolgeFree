const std = @import("std");
const backend = @import("backend");
const hell = @import("hell");
const mb = @import("malbolge_free");

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

fn imageForWithTargets(ops: []const backend.Op, targets: []const ?usize, allocator: std.mem.Allocator) ![]u8 {
    std.debug.assert(ops.len == targets.len);
    const size = 9 + ops.len * 12;
    var bytes = try allocator.alloc(u8, size);
    @memset(bytes, 0);
    @memcpy(bytes[0..5], "BFIR1");
    std.mem.writeInt(u32, bytes[5..9], @intCast(ops.len), .little);
    for (ops, 0..) |op, index| {
        const offset = 9 + index * 12;
        bytes[offset] = @intFromEnum(op);
        bytes[offset + 1] = if (targets[index] != null) 1 else 0;
        if (targets[index]) |t| {
            std.mem.writeInt(u32, bytes[offset + 4 ..][0..4], @intCast(t), .little);
        }
        std.mem.writeInt(u32, bytes[offset + 8 ..][0..4], @intCast(index), .little);
    }
    return bytes;
}

test "A7 decodes BFIR1 linear image" {
    const bytes = try imageFor(&.{ .move_right, .increment, .output }, std.testing.allocator);
    defer std.testing.allocator.free(bytes);
    var image = try backend.decode(bytes, std.testing.allocator);
    defer image.deinit(std.testing.allocator);
    try std.testing.expectEqual(@as(usize, 3), image.code.items.len);
    try std.testing.expectEqual(backend.Op.output, image.code.items[2].op);
}

test "A7 lowers linear BFIR1 to parseable HeLL" {
    const bytes = try imageFor(&.{ .move_right, .move_left, .increment, .decrement, .output, .input }, std.testing.allocator);
    defer std.testing.allocator.free(bytes);
    var lowered = try backend.lowerImage(bytes, std.testing.allocator);
    defer lowered.deinit(std.testing.allocator);

    var parser = hell.Parser.init(lowered.slice());
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);
    // TAPE_BASE + six source ops, with pointer compensation, plus HALT.
    try std.testing.expectEqual(@as(usize, 16), program.blocks.items[0].instructions.items.len);
}

test "A7 linear lowering rejects branches (branches go through lowerBranched)" {
    const bytes = try imageFor(&.{ .jump_if_zero }, std.testing.allocator);
    defer std.testing.allocator.free(bytes);
    var image = try backend.decode(bytes, std.testing.allocator);
    defer image.deinit(std.testing.allocator);
    try std.testing.expectError(error.UnexpectedBranch, backend.lowerLinear(&image, std.testing.allocator));
}

test "A7 rejects malformed BFIR1" {
    try std.testing.expectError(error.InvalidHeader, backend.decode("bad", std.testing.allocator));
}

test "A7 e2e: BFIR1 NOP/HALT loads and halts in MalbolgeCore" {
    const bytes = try imageFor(&.{ .increment, .output }, std.testing.allocator);
    defer std.testing.allocator.free(bytes);

    var lowered = try backend.lowerImage(bytes, std.testing.allocator);
    defer lowered.deinit(std.testing.allocator);

    var parser = hell.Parser.init(lowered.slice());
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    var layout = try hell.resolveLayout(&program, std.testing.allocator);
    defer layout.deinit(std.testing.allocator);

    var emitted = try hell.emit(&layout, std.testing.allocator);
    defer emitted.deinit(std.testing.allocator);

    try std.testing.expect(emitted.slice().len > 0);

    var core = mb.MalbolgeCore.initFreeAssisted(std.testing.allocator, 10, null, .fixed);
    defer core.deinit();
    try core.load(emitted.slice());
    var result = try core.run(100, "");
    defer result.stdout.deinit(std.testing.allocator);

    try std.testing.expectEqualStrings("HALTED", result.status);
    try std.testing.expect(result.steps > 0);
    try std.testing.expect(result.steps <= 100);
}

test "A7 bracket map: matched [ ]" {
    const bytes = try imageForWithTargets(
        &.{ .increment, .jump_if_zero, .move_right, .increment, .move_left, .jump_if_nonzero },
        &.{ null, @as(?usize, 5), null, null, null, @as(?usize, 1) },
        std.testing.allocator,
    );
    defer std.testing.allocator.free(bytes);
    var image = try backend.decode(bytes, std.testing.allocator);
    defer image.deinit(std.testing.allocator);

    var map = try backend.buildBracketMap(&image, std.testing.allocator);
    defer map.deinit();

    try std.testing.expectEqual(@as(?usize, 5), map.get(1));
    try std.testing.expectEqual(@as(?usize, 1), map.get(5));
}

test "A7 bracket map: unmatched [ rejects" {
    const bytes = try imageFor(&.{ .jump_if_zero }, std.testing.allocator);
    defer std.testing.allocator.free(bytes);
    var image = try backend.decode(bytes, std.testing.allocator);
    defer image.deinit(std.testing.allocator);

    try std.testing.expectError(error.UnmatchedBracket, backend.buildBracketMap(&image, std.testing.allocator));
}

test "A7 bracket map: unmatched ] rejects" {
    const bytes = try imageFor(&.{ .jump_if_nonzero }, std.testing.allocator);
    defer std.testing.allocator.free(bytes);
    var image = try backend.decode(bytes, std.testing.allocator);
    defer image.deinit(std.testing.allocator);

    try std.testing.expectError(error.UnmatchedBracket, backend.buildBracketMap(&image, std.testing.allocator));
}

test "A7 lowerBranched: simple loop emits JZ + JNZ" {
    const bytes = try imageForWithTargets(
        &.{ .increment, .jump_if_zero, .move_right, .increment, .move_left, .jump_if_nonzero },
        &.{ null, @as(?usize, 5), null, null, null, @as(?usize, 1) },
        std.testing.allocator,
    );
    defer std.testing.allocator.free(bytes);
    var image = try backend.decode(bytes, std.testing.allocator);
    defer image.deinit(std.testing.allocator);

    var lowered = try backend.lowerBranched(&image, std.testing.allocator);
    defer lowered.deinit(std.testing.allocator);

    const src = lowered.slice();
    try std.testing.expect(src.len > 0);
    try std.testing.expect(std.mem.indexOf(u8, src, "JZ") != null);
    try std.testing.expect(std.mem.indexOf(u8, src, "JNZ") != null);

    var parser = hell.Parser.init(src);
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    try std.testing.expect(program.blocks.items.len >= 1);
    try std.testing.expect(program.blocks.items[0].instructions.items.len > 0);
}

test "A7 lowerBranched: nested loop emits JZ + JNZ" {
    const bytes = try imageForWithTargets(
        &.{ .increment, .jump_if_zero, .increment, .jump_if_zero, .move_right, .jump_if_nonzero, .jump_if_nonzero },
        &.{ null, @as(?usize, 6), null, @as(?usize, 5), null, @as(?usize, 3), @as(?usize, 1) },
        std.testing.allocator,
    );
    defer std.testing.allocator.free(bytes);
    var image = try backend.decode(bytes, std.testing.allocator);
    defer image.deinit(std.testing.allocator);

    var lowered = try backend.lowerBranched(&image, std.testing.allocator);
    defer lowered.deinit(std.testing.allocator);

    const src = lowered.slice();
    try std.testing.expect(src.len > 0);
    try std.testing.expect(std.mem.indexOf(u8, src, "JZ") != null);
    try std.testing.expect(std.mem.indexOf(u8, src, "JNZ") != null);

    var parser = hell.Parser.init(src);
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    try std.testing.expect(program.blocks.items.len >= 1);
}
