# Fixed20 versus original Nagoya: FAIL_SEMANTICS (scoped counterexample)

Reference downloaded from the [Nagoya project GitLab](https://git.trs.css.i.nagoya-u.ac.jp/malbolge/malbolge20-interpreter)
master archive on 2026-10-08. Its LICENSE is MIT, copyright Nagoya Univ.
Unmodified source, original sample and license are preserved in `nagoya/`.
Remote HEAD lookup: `21ebda787362ab009276e216be34c169e4d049f4`.
The archive is identified by SHA-256; a HEAD lookup alone does not establish
that mutable master archive is byte-identical to that commit.

The original C interpreter compiled with GCC, without modifications. Both
Free cores used `fixed`, width 20 **at boot**, and `mem_limit=3^20`, which
matches the reference address wrap. Epochal was not used in this comparison.

| Program / input | Nagoya stdout hex | Free Zig / Python hex | Outcome |
|---|---|---|---|
| original `hello20.mb` / empty | 48656c6c6f576f726c64 | same / same | stdout parity, successful termination |
| `ubO` / ASCII A | 41 | 41 / 41 | stdout parity, successful termination |
| `ubO` / EOF | a9 | ff / ff | disagreement |

All three programs were accepted and terminated by the unmodified Nagoya
loader/runtime, so these are valid Malbolge20 inputs. `ubO` is the
three-instruction sequence INPUT, OUTPUT, HALT under the shared positional
decoder; its use here rests on reference acceptance, not an assumption that
Classic fixtures are interchangeable. No assertion of global source compatibility.

First source-level divergence: original `malbolge20.c` INPUT assigns 59049
at EOF, then OUTPUT calls `putc(a, stdout)`, emitting 59049 % 256 = 169 (a9).
Free Python assigns -1; the Zig core uses its EOF sentinel. Both emit ff.
Free terminated at step 3. The original does not expose step counts, so no
cross-runtime step-count or bit-exact state parity is claimed.

The reference's ROT is width 20, crazy covers 20 trits, memory is lazily
materialized in 59049-cell blocks, encryption uses xlat2, and pointers wrap
at 3^20. The original sample exercises a nontrivial execution (Free reports
46418 steps, max touched address 531501). Opcode coverage was not measured.
Further targeted ROT/crazy/jump corpus work is deferred at the demonstrated
semantic disagreement as specified by the STOP gate. No runtime rewrite.

`FIXED20_NAGOYA_PARITY: FAIL` for the corpus including EOF.
This does not imply failure of epochal address widening or mathematical impossibility.
