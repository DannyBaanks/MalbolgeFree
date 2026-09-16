// bf_tape.zig — shared BF tape module for IR VM and Malbolge backend.
const std = @import("std");

pub const TapeError = error{
    PointerOutOfBounds,
    OutOfMemory,
};

pub const Tape = struct {
    cells: std.ArrayListUnmanaged(u8),
    pointer: usize,
    max_pointer: usize,

    pub fn init(allocator: std.mem.Allocator, size: usize) !Tape {
        var tape = Tape{
            .cells = .empty,
            .pointer = 0,
            .max_pointer = size -| 1,
        };
        try tape.cells.appendNTimes(allocator, 0, size);
        return tape;
    }

    pub fn deinit(self: *Tape, allocator: std.mem.Allocator) void {
        self.cells.deinit(allocator);
    }

    pub fn get(self: *const Tape) u8 {
        return self.cells.items[self.pointer];
    }

    pub fn set(self: *Tape, value: u8) void {
        self.cells.items[self.pointer] = value;
    }

    pub fn moveRight(self: *Tape) TapeError!void {
        if (self.pointer >= self.max_pointer) return error.PointerOutOfBounds;
        self.pointer += 1;
    }

    pub fn moveLeft(self: *Tape) TapeError!void {
        if (self.pointer == 0) return error.PointerOutOfBounds;
        self.pointer -= 1;
    }

    pub fn increment(self: *Tape) void {
        self.cells.items[self.pointer] +%= 1;
    }

    pub fn decrement(self: *Tape) void {
        self.cells.items[self.pointer] -%= 1;
    }

    pub fn inputByte(self: *Tape, byte: u8) void {
        self.cells.items[self.pointer] = byte;
    }

    pub fn isZero(self: *const Tape) bool {
        return self.cells.items[self.pointer] == 0;
    }
};

test "Tape: init and basic ops" {
    var tape = try Tape.init(std.testing.allocator, 10);
    defer tape.deinit(std.testing.allocator);

    try std.testing.expectEqual(@as(u8, 0), tape.get());
    tape.set(42);
    try std.testing.expectEqual(@as(u8, 42), tape.get());

    tape.increment();
    try std.testing.expectEqual(@as(u8, 43), tape.get());

    tape.decrement();
    try std.testing.expectEqual(@as(u8, 42), tape.get());
}

test "Tape: move right and left" {
    var tape = try Tape.init(std.testing.allocator, 4);
    defer tape.deinit(std.testing.allocator);

    try tape.moveRight();
    tape.set(10);
    try std.testing.expectEqual(@as(usize, 1), tape.pointer);
    try std.testing.expectEqual(@as(u8, 10), tape.get());

    try tape.moveLeft();
    try std.testing.expectEqual(@as(usize, 0), tape.pointer);
    try std.testing.expectEqual(@as(u8, 0), tape.get());
}

test "Tape: bounds checking" {
    var tape = try Tape.init(std.testing.allocator, 2);
    defer tape.deinit(std.testing.allocator);

    try std.testing.expectError(error.PointerOutOfBounds, tape.moveLeft());
    try tape.moveRight();
    try std.testing.expectError(error.PointerOutOfBounds, tape.moveRight());
}

test "Tape: byte wrapping" {
    var tape = try Tape.init(std.testing.allocator, 2);
    defer tape.deinit(std.testing.allocator);

    tape.set(255);
    tape.increment();
    try std.testing.expectEqual(@as(u8, 0), tape.get());

    tape.decrement();
    try std.testing.expectEqual(@as(u8, 255), tape.get());
}

test "Tape: isZero" {
    var tape = try Tape.init(std.testing.allocator, 2);
    defer tape.deinit(std.testing.allocator);

    try std.testing.expect(tape.isZero());
    tape.set(1);
    try std.testing.expect(!tape.isZero());
}
