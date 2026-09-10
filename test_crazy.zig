// Test crazy op fix
const std = @import("std");
const core = @import("src/malbolge_free.zig");

pub fn main() !void {
    // Test case from hello.mal step 3: a=29524, mem[d]=something
    // Python crazy_op(29524, 29524) = 0
    // With buggy bitwise AND: a & (3^10 - 1) = 29524 & 59048 = 25088
    // crazy_op(25088, 29524) != 0

    const a: u128 = 29524;
    const b: u128 = 29524;
    const w: u8 = 10;
    const modulus = core.pow3(w);

    std.debug.print("a={d}, b={d}, w={d}, modulus={d}\n", .{a, b, w, modulus});
    std.debug.print("a % modulus = {d}\n", .{a % modulus});
    std.debug.print("a & (modulus-1) = {d}\n", .{a & (modulus - 1)});

    const result_mod = core.crazy(a % modulus, b, w);
    const result_and = core.crazy(a & (modulus - 1), b, w);
    const result_raw = core.crazy(a, b, w);

    std.debug.print("crazy(a%mod, b, w) = {d}\n", .{result_mod});
    std.debug.print("crazy(a&mask, b, w) = {d}\n", .{result_and});
    std.debug.print("crazy(a, b, w) = {d}\n", .{result_raw});

    // Python reference: crazy_op(29524, 29524) = 0
    std.debug.print("Expected (Python): 0\n", .{});
}