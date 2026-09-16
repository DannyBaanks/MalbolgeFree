const std = @import("std");
const translator = @import("bf_to_ir.zig");
const image = @import("bf_ir_image.zig");

const COMPILER_SEED =
    "+[-->-[>>+>-----<<]<--<---]>-.>>>+.>>..+++[>++++<-]>++.";

test "Quinepiler seed compilation is canonical and reproducible" {
    const allocator = std.testing.allocator;
    var first_program = try translator.compile(COMPILER_SEED, allocator);
    defer first_program.deinit();
    var second_program = try translator.compile(COMPILER_SEED, allocator);
    defer second_program.deinit();
    const first = try image.encode(&first_program, allocator);
    defer allocator.free(first);
    const second = try image.encode(&second_program, allocator);
    defer allocator.free(second);

    try std.testing.expectEqualSlices(u8, first, second);
    try std.testing.expectEqual(@as(usize, 55), first_program.code.items.len);
    try std.testing.expectEqual(@as(usize, 55), second_program.code.items.len);
    std.debug.print("QUINEPILER_SEED source_bytes={d} image_bytes={d} deterministic=PASS\n", .{
        COMPILER_SEED.len, first.len,
    });
}
