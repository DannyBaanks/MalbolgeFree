const std = @import("std");
const backend = @import("backend");
const hell = @import("hell");

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

test "A7 conditional: simple loop [+] emits JZ + JNZ with inline immediates" {
    const bytes = try imageForWithTargets(
        &.{ .jump_if_zero, .increment, .jump_if_nonzero },
        &.{ @as(?usize, 2), null, @as(?usize, 0) },
        std.testing.allocator,
    );
    defer std.testing.allocator.free(bytes);
    var image = try backend.decode(bytes, std.testing.allocator);
    defer image.deinit(std.testing.allocator);

    var lowered = try backend.lowerBranched(&image, std.testing.allocator);
    defer lowered.deinit(std.testing.allocator);
    const src = lowered.slice();

    try std.testing.expect(std.mem.indexOf(u8, src, "JZ") != null);
    try std.testing.expect(std.mem.indexOf(u8, src, "JNZ") != null);
    try std.testing.expect(std.mem.indexOf(u8, src, ".DATA") == null);

    var parser = hell.Parser.init(src);
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);

    // TAPE_BASE + [JZ + 3 lit] + [INC + D_REWIND] + [JNZ + 3 lit] + HALT = 12
    try std.testing.expectEqual(@as(usize, 12), program.blocks.items[0].instructions.items.len);

    var lit_count: usize = 0;
    for (program.blocks.items[0].instructions.items) |inst| {
        if (inst.opcode == .lit) lit_count += 1;
    }
    try std.testing.expectEqual(@as(usize, 6), lit_count);
}

test "A7 conditional: nested loop emits JZ + JNZ and parses" {
    const bytes = try imageForWithTargets(
        &.{ .jump_if_zero, .decrement, .jump_if_zero, .increment, .decrement, .jump_if_nonzero, .jump_if_nonzero },
        &.{ @as(?usize, 6), null, @as(?usize, 5), null, null, @as(?usize, 2), @as(?usize, 0) },
        std.testing.allocator,
    );
    defer std.testing.allocator.free(bytes);
    var image = try backend.decode(bytes, std.testing.allocator);
    defer image.deinit(std.testing.allocator);

    var lowered = try backend.lowerBranched(&image, std.testing.allocator);
    defer lowered.deinit(std.testing.allocator);
    const src = lowered.slice();

    try std.testing.expect(std.mem.indexOf(u8, src, "JZ") != null);
    try std.testing.expect(std.mem.indexOf(u8, src, "JNZ") != null);

    var parser = hell.Parser.init(src);
    var program = try parser.parse(std.testing.allocator);
    defer program.deinit(std.testing.allocator);
    try std.testing.expect(program.blocks.items.len >= 1);
}