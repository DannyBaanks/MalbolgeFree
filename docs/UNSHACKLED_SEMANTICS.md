# UNSHACKLED semantics — extracted from `MALDOOM/vendor/Unshackled.c` (Matthias Lutter)

## What stays the same vs Classic

- Ternary machine, 8 same opcodes (jmp/out/in/rot/movd/crazy/nop/hlt)
- Same `_CRAZY` 3×3 trit table, same `_ENC` xlat table
- Same `op = (cell + pos) % 94` decode, `pos` incremented per step
- Loader: read source, reject non-op chars (per-position check `(char+pos)%94 ∈ [4,5,23,39,40,62,68,81]`), so source semantics match Classic's "valid chars" idea
- Loader crazy-fills memory — but lazily now, not by allocating 3^k cells

## What changed

### 1. Width is a DATA-LEVEL property, not a machine constant

- `rotwidth` starts random in `[10, 15]` and grows
- grown by `det_growth_policy` / `nondet_growth_policy` when `movd` reveals big trits
- deterministic variant: `if (new_wordwidth > (old_rotwidth - slack)/2): rotwidth += step`
- `Number.width` exists per-value; it's the minimal trit count that expresses
  the value semantically, after trimming.

### 2. rotate() is width-relative, not fixed

```c
rotate_r(n, rotwidth):
    while n->width < rotwidth: append a zero-trit (PAD the representation)
    rot within that width
```

Key: **`rotate` pads. The pad is the mechanism by which wide values enter
the system.** Without padding, you'd rotate 10 trits forever. With pad-to-
rotwidth, rotate produces a rotwidth-trit value, which then (via `movd` to C
/ `j` path) can widen the machine's observed `max_wordwidth`, which then
grows `rotwidth`, and so on.

### 3. Memory is lazy

- Memory: a ternary tree of MemCell pointers (trie by trit), not an array
- uninitialized cells don't exist physically; only `initial_values[0..5]`
  (derived from the last two loaded cells via crazy) serve as the "next-cell"
  default pattern, cycling `initial_values[pos % 6]`
- `update_memptr(n)` lazily walks/creates trie nodes as the machine touches
  them

### 4. Size is unbounded

No `MAX_ADDR`. Addresses are `Number` (arbitrary-width), positions `pos` are
`mod 564` = `mod (6 * 94)` — cyclic, not capped.

### 5. I/O is Unicode

- Source is read byte-wise (fread); UTF-8 encoded, so I/O is codepoint-based.
- `in` reads a Unicode codepoint; EOF = -1; `\n` input is normalized so `a`
  becomes a special "1,2 as trits" form. Output uses `is_nl(a)` to map to
  `"\n"` — newline is not raw 10 in the character space, it's a distinguished
  value that the host translates.

## Width growth vs width capping

`nondet_growth_policy` may arbitrarily return `old + step` regardless of data.
`det_growth_policy` grows only when `new_wordwidth > (old - slack)/2`.

This is the mechanism that lets Unshackled remain Malbolge-shaped at k=10
but not get stuck at any fixed k.

## What we'd need for `FREE(k=19)` == `Unshackled`

- ramp `rotwidth` the same way? **No — nondeterministic in the original.**
- A faithful reproduction requires choosing the deterministic variant, NOT
  the `rand()`-driven one. So `FREE(k=19)` is deterministic while
  `Unshackled.c` is not. Exact parity needs pinning `srand(0)` or replacing
  the growth policy with a documented deterministic one.
