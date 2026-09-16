const std = @import("std");
const translator = @import("bf_to_ir.zig");

test "translator lowers instructions and resolves nested loops" {
    const allocator = std.testing.allocator;
    var program = try translator.compile(" +[->++[<]>] ., ", allocator);
    defer program.deinit();

    try std.testing.expectEqual(@as(usize, 13), program.code.items.len);
    try std.testing.expectEqual(translator.Op.jump_if_zero, program.code.items[1].op);
    try std.testing.expectEqual(@as(?usize, 10), program.code.items[1].target);
    try std.testing.expectEqual(translator.Op.jump_if_nonzero, program.code.items[8].op);
    try std.testing.expectEqual(@as(?usize, 6), program.code.items[8].target);
    try std.testing.expectEqual(@as(usize, 2), program.code.items[1].source_pos);
}

test "translator ignores comments but preserves source positions" {
    const allocator = std.testing.allocator;
    var program = try translator.compile("comment + output .", allocator);
    defer program.deinit();

    try std.testing.expectEqual(@as(usize, 2), program.code.items.len);
    try std.testing.expectEqual(@as(usize, 8), program.code.items[0].source_pos);
    try std.testing.expectEqual(@as(usize, 17), program.code.items[1].source_pos);
}

test "translator rejects unbalanced loops" {
    const allocator = std.testing.allocator;
    try std.testing.expectError(translator.Error.UnmatchedBracket, translator.compile("+[", allocator));
    try std.testing.expectError(translator.Error.UnmatchedBracket, translator.compile("]", allocator));
}

test "IR validator rejects malformed jump targets" {
    const allocator = std.testing.allocator;
    var program = try translator.compile("[]", allocator);
    defer program.deinit();

    program.code.items[0].target = null;
    try std.testing.expectError(translator.Error.MissingJumpTarget, translator.validate(&program));

    program.code.items[0].target = 99;
    try std.testing.expectError(translator.Error.InvalidJumpTarget, translator.validate(&program));
}
