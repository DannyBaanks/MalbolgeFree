// bf_image_vm.zig — VM entrypoint consuming BFIR1 images.
const std = @import("std");
const bf = @import("bf_interpreter.zig");
const image = @import("bf_ir_image.zig");
const ir_vm = @import("bf_ir_vm.zig");

pub fn run(
    bytes: []const u8,
    input: []const u8,
    config: bf.Config,
    allocator: std.mem.Allocator,
    capture_trace: bool,
) !bf.Outcome {
    var program = try image.decode(bytes, allocator);
    defer program.deinit();
    return ir_vm.run(&program, input, config, allocator, capture_trace);
}
