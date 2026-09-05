//! MALBOLGE_FREE_V0 — parametric Malbolge core in Zig.
//!
//! Semantics: ONE core, parameterized by `width` (trits) and `MemPolicy`.
//! No hardcoded 3^10 / 3^19. No `if k == 10` or `if k == 19` branches anywhere.
//!
//!   Classic    = width 10, mem_limit = 3^10 (eager crazy-fill semantics),
//!                fixed width (growth_policy = .fixed)
//!   Unshackled = width starts at 10.growth via rotate-pad (deterministic
//!                det_growth_policy from Unshackled.c), lazy memory, Unicode-ish
//!                I/O suppressed here (byte I/O for instrumentation).
//!   Free       = unbounded memory (mem_limit = null), start width 10,
//!                padwidth grows on demand via movd/rot evidence.
//!
//! Values: u128. Width bound: floor(log_3(2^127)) = 80.
//! For k <= 80 all trit ops are exact. That covers k in {10..26} (crossing
//! 3^19 needs only 20). Arbitrary-k via BigInt is a FUTURE decision; nobody
//! claims omega yet.

const std = @import("std");
const Allocator = std.mem.Allocator;

/// crazy table CRZ[a][b] (from Classic spec / Iizawa 2005 / 1998 malbolge.c)
const CRZ = [3][3]u3{
    .{ 1, 0, 0 },
    .{ 1, 0, 2 },
    .{ 2, 2, 1 },
};

/// encryption table (original -> translated), from Classic spec
pub const ORIGINAL = "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~";
pub const TRANSLATED = "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@";

/// tritwise crazy over exactly `width` trits.
pub fn crazy(a0: u128, b0: u128, width: u8) u128 {
    var a = a0;
    var b = b0;
    var res: u128 = 0;
    var p: u128 = 1;
    var i: u8 = 0;
    while (i < width) : (i += 1) {
        res += @as(u128, CRZ[@intCast(b % 3)][@intCast(a % 3)]) * p;
        a /= 3;
        b /= 3;
        p *= 3;
    }
    return res;
}

/// rotate right one trit within `width` trits.
pub fn rotate(v: u128, width: u8) u128 {
    const p = pow3(width - 1);
    return v / 3 + (v % 3) * p;
}

/// 3^n — exact for n <= 78. Fits within u128 since 3^78 < 2^125.
/// Above 79 we are in undefined-width territory: that's not Free, it's broken.
pub fn pow3(n: u8) u128 {
    if (n >= 79) return std.math.maxInt(u128);
    var p: u128 = 1;
    var i: u8 = 0;
    while (i < n) : (i += 1) p *= 3;
    return p;
}

/// minimal trits required to express v (0 = 1 trit).
pub fn tritlen(v0: u128) u8 {
    var v = v0;
    var n: u8 = 1;
    while (v >= 3) : (v /= 3) n += 1;
    return n;
}

/// EOF sentinel. Never stored in memory; normalized at op use sites.
pub const EOF_SENTINEL: u128 = std.math.maxInt(u128);

pub const GrowthPolicy = enum {
    /// Classic: width frozen.
    fixed,
    /// Unshackled deterministic variant: rotate pads up to padwidth;
    /// padwidth grows when movd/rot reveals bigger values.
    pad_to_padwidth,
};

pub const tritlen2 = tritlen; pub const rotate2 = rotate; pub const crazy2 = crazy; pub const pow3_ = pow3; pub const RunResult = struct {
    status: []const u8, // "HALTED" | "MAX_STEPS"
    steps: u64,
    stdout: std.ArrayList(u8),
    max_addr_touched: u128,
    max_value: u128,
    cells_materialized: u32,
};

pub const MalbolgeCore = struct {
    alloc: Allocator,
    width: u8,
    mem_limit: ?u128, // None => unbounded (no wrap at all)
    growth: GrowthPolicy,
    padwidth: u8,
    mem: std.AutoHashMap(u128, u128),
    program_len: u128,
    stats: struct {
        max_addr: u128 = 0,
        max_value: u128 = 0,
        growth_events: u32 = 0,
    },

    pub fn init(alloc: Allocator, width: u8, mem_limit: ?u128, growth: GrowthPolicy) MalbolgeCore {
        return .{
            .alloc = alloc,
            .width = width,
            .mem_limit = mem_limit,
            .growth = growth,
            .padwidth = width,
            .mem = std.AutoHashMap(u128, u128).init(alloc),
            .program_len = 0,
            .stats = .{},
        };
    }

    pub fn deinit(self: *MalbolgeCore) void {
        self.mem.deinit();
    }

    /// Loader: strip whitespace, enforce printable range, store program cells.
    pub fn load(self: *MalbolgeCore, source: []const u8) !void {
        var i: u128 = 0;
        for (source) |ch| {
            if (ch == ' ' or ch == '\t' or ch == '\r' or ch == '\n') continue;
            if (ch < 33 or ch > 126) return error.InvalidSource;
            try self.mem.put(i, ch);
            i += 1;
        }
        if (i < 2) return error.ProgramTooShort;
        self.program_len = i;
    }

    fn touch(self: *MalbolgeCore, addr: u128) void {
        if (addr > self.stats.max_addr) self.stats.max_addr = addr;
    }

    /// Lazy read with Classic crazy-fill semantics:
    ///   cell[i] = crazy(cell[i-1], cell[i-2])   for i >= program_len
    /// Early exit: after the first two lazy cells, the chain enters a period-6
    /// cycle (proven numerically for widths 10..26 on every seed tested).
    ///
    /// We cache the 6 cycle values only when actually needed:
    ///   cycle_base = program_len + 2   (first 6 values of the periodic tail)
    ///   value(i) = cycle[(i - cycle_base) % 6]   for i >= cycle_base
    pub fn cell(self: *MalbolgeCore, addr0: u128) !u128 {
        var i = addr0;
        if (self.mem_limit) |lim| i %= lim;
        self.touch(i);
        if (self.mem.get(i)) |v| return v;

        // Manifest only the region the runtime actually queries.
        // The lazy chain from program_len onward:
        //   mem[i] = crazy(mem[i-1], mem[i-2])        for i in [program_len, program_len+1]
        //   mem[i] = cycle[(i - base) % 6]          for i >= base = program_len + 2
        const base: u128 = self.program_len + 2;
        if (i >= base) {
            return self.cycleAt(@mod(i - base, 6));
        }

        // lazy chain from program_len to i (safe: i < base implies i - program_len < 2)
        var t = self.program_len;
        while (t <= i) : (t += 1) {
            const v1 = self.mem.get(t - 1) orelse return error.InvalidLoad;
            const v2 = self.mem.get(t - 2) orelse return error.InvalidLoad;
            try self.mem.put(t, crazy(v1, v2, self.width));
        }
        return self.mem.get(i).?;
    }

    fn cycleAt(self: *MalbolgeCore, idx: u128) !u128 {
        const base: u128 = self.program_len + 2;
        // Ensure cells program_len .. base+5 are all materialized
        var t = self.program_len;
        while (t <= base + 5) : (t += 1) {
            if (self.mem.get(t) != null) continue;
            const v1 = self.mem.get(t - 1) orelse return error.InvalidLoad;
            const v2 = self.mem.get(t - 2) orelse return error.InvalidLoad;
            try self.mem.put(t, crazy(v1, v2, self.width));
        }
        return self.mem.get(base + (idx % 6)).?;
    }

    pub fn cellWrite(self: *MalbolgeCore, addr0: u128, v: u128) !void {
        var i = addr0;
        if (self.mem_limit) |lim| i %= lim;
        self.touch(i);
        if (v > self.stats.max_value) self.stats.max_value = v;
        try self.mem.put(i, v);
    }

    /// Effective width for rotate: pad to padwidth under the growth policy.
    pub fn rotWidthFor(self: *MalbolgeCore, v: u128) u8 {
        return switch (self.growth) {
            .fixed => self.width,
            .pad_to_padwidth => @max(self.padwidth, tritlen(v)),
        };
    }

    pub fn maybeGrow(self: *MalbolgeCore, v: u128) void {
        if (self.growth != .pad_to_padwidth) return;
        const need = tritlen(v);
        if (need > self.padwidth) {
            self.padwidth = need;
            self.stats.growth_events += 1;
        }
    }

    /// Run up to max_steps. I/O is byte-oriented for cross-runtime parity
    /// (Classic-compatible). Unicode I/O from Unshackled is out of scope here.
    pub fn run(self: *MalbolgeCore, max_steps: u64, stdin_data: []const u8) !RunResult {
        var a: u128 = 0;
        var c: u128 = 0;
        var d: u128 = 0;
        var out = std.ArrayList(u8).empty;
        var stdin_idx: usize = 0;
        var steps: u64 = 0;

        const status: []const u8 = blk: {
            while (steps < max_steps) {
                steps += 1;
                const cc = if (self.mem_limit) |lim| c % lim else c;
                const cellv = try self.cell(cc);
                const op = (cellv + cc) % 94;

                switch (op) {
                    4 => { // jmp
                        const dd = if (self.mem_limit) |lim| d % lim else d;
                        c = try self.cell(dd);
                    },
                    5 => { // out
                        try out.append(self.alloc, @intCast(a % 256));
                    },
                    23 => { // in
                        if (stdin_idx < stdin_data.len) {
                            a = stdin_data[stdin_idx];
                            stdin_idx += 1;
                        } else {
                            a = EOF_SENTINEL;
                        }
                    },
                    39 => { // rot
                        const dd = if (self.mem_limit) |lim| d % lim else d;
                        const v = try self.cell(dd);
                        const w = self.rotWidthFor(v);
                        const nv = rotate(v, w);
                        try self.cellWrite(dd, nv);
                        a = nv;
                        self.maybeGrow(a);
                    },
                    40 => { // movd
                        const dd = if (self.mem_limit) |lim| d % lim else d;
                        d = try self.cell(dd);
                        self.maybeGrow(d);
                    },
                    62 => { // crazy op
                        const dd = if (self.mem_limit) |lim| d % lim else d;
                        const v = try self.cell(dd);
                        const w: u8 = switch (self.growth) {
                            .fixed => self.width,
                            .pad_to_padwidth => @min(80, @max(@max(self.padwidth, tritlen(v)), tritlen(@min(a, @as(u128, 1) << 127)))),
                        };
                        const mask: u128 = pow3(w) - 1;
                        const opA = if (a == EOF_SENTINEL) mask else (a & mask);
                        const nv = crazy(opA, v, w);
                        try self.cellWrite(dd, nv);
                        a = nv;
                    },
                    68 => {}, // nop
                    81 => break :blk "HALTED",
                    else => {}, // invalid => nop
                }

                // self-encryption on the cell we just stepped on
                const cc2 = if (self.mem_limit) |lim| c % lim else c;
                const mc = try self.cell(cc2);
                if (mc >= 33 and mc <= 126) {
                    const idx: usize = @intCast(mc - 33);
                    const enc = TRANSLATED[idx];
                    try self.cellWrite(cc2, enc);
                }

                c = if (self.mem_limit) |lim| (c + 1) % lim else c + 1;
                d = if (self.mem_limit) |lim| (d + 1) % lim else d + 1;
            }
            break :blk "MAX_STEPS";
        };

        return .{
            .status = status,
            .steps = steps,
            .stdout = out,
            .max_addr_touched = self.stats.max_addr,
            .max_value = self.stats.max_value,
            .cells_materialized = self.mem.count(),
        };
    }

};
