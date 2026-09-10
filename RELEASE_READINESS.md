# Malbolge Free — Release Readiness Checklist

**Status**: CORE COMPLETE — ready for v1.0 tag once C8 is resolved

---

## ✅ COMPLETE (as of 2026-09-09)

| Item | Evidence |
|---|---|
| **Classic Parity (6/6 corpus)** | `evidence/f4_classic_parity.json` — all match |
| **Frontier Widening 10→11** | `tests/t_frontier_moment.zig` — WIDEN at step 59050 |
| **3^19 Crossing (k=20)** | `evidence/f7_witness.zig` — d = 1,743,392,210 > 3^19 |
| **Epochal Invariants** | `tests/t_epochal.zig` — 2/2 tests pass |
| **Lazy == Eager Fill** | `tests/t_phase23.py` — bit-for-bit at k=10 (59049 cells) |
| **Width-Extension Brokenness** | `evidence/f8_check.py` — rotate 33.3%, crazy 100% |
| **Zero Python in Zig Toolchain** | `Malbolge-Translator/zig/parity_check.exe` is Zig reference |

---

## ❌ BLOCKING FOR "COMPLETE MACHINE" RELEASE

### C8: REPEATED_WIDTH_WIDENING (11→12)
- **What**: Demonstrate second frontier crossing at 3^11 = 177,147
- **Blocker**: Current `frontier_witness.txt` is only 70,000 chars (reaches 59,049 but not 177,147)
- **Fix**: Generate longer witness (~180k+ chars) using `gen_frontier_witness.py` scaled up
- **Estimated effort**: ~30 min to generate + verify

---

## 📋 OPTIONAL POLISH (not blocking)

| Item | Notes |
|---|---|
| Version tag / CHANGELOG | v1.0.0 |
| GitHub release with binaries | `malbolge-free.exe` (Zig core), `parity_check.exe` (ref) |
| docs/HONESTY_LEDGER.md sync | Already current |
| CI badge | Optional |

---

## QUICK VERIFY ALL GATES

```bash
# 1. Classic parity (Zig vs Zig)
cd malbolge-free && py evidence/compare_f4.py
# => PASS

# 2. Frontier 10→11
zig run tests/t_frontier_moment.zig
# => WIDEN step=59050 ... final padwidth=11

# 3. 3^19 crossing
zig run evidence/f7_witness.zig
# => max_addr=1743392210 >3^19=true

# 4. Epochal invariants
zig test tests/t_epochal.zig
# => All 2 tests passed

# 5. Lazy/eager parity
py tests/t_phase23.py
# => k=10: lazy == Classic eager loader (59049 cells bit-for-bit)  OK

# 6. Width-extension evidence
py evidence/f8_check.py
# => crazy same=729/729 (100.0%)   rotate same=9/27 (33.3%)
```

---

## ARCHITECTURE SNAPSHOT

```
malbolge-free/
├── src/
│   ├── malbolge_core.py          # Python reference core (parametric, lazy fill)
│   └── malbolge_free.zig         # Zig core (u128, epochal/fixed/pad_to_padwidth)
├── evidence/
│   ├── f4_classic_parity.json    # 6/6 corpus SHA256 matches
│   ├── compare_f4.py             # Runner: Zig ref vs Zig core
│   ├── f7_witness.zig            # 3^19 crossing
│   └── f8_check.py               # Width-extension consistency
├── tests/
│   ├── t_frontier_moment.zig     # 10→11 widening demo
│   ├── t_epochal.zig             # Invariants
│   ├── t_phase23.py              # Lazy/eager + Classic loader parity
│   └── frontier_witness.txt      # 70k program (needs 180k+ for 11→12)
└── Malbolge-Translator/zig/      # External Zig reference (generator, PCA, epoch, etc.)
    └── parity_check.exe          # 6/6 corpus JSON oracle
```

---

## DECISION POINT

**If C8 is not a release requirement**: Tag v1.0 now. The machine is:
- Classic-compatible (6/6)
- Frontier-widening demonstrated (10→11)
- Unbounded memory with epochal policy working
- All evidence hashed and reproducible

**If C8 is required**: Generate 180k+ witness, verify 11→12, then tag.

---

*Generated 2026-09-09 — ^w^*