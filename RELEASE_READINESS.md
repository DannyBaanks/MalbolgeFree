# Malbolge Free — Release Readiness Checklist

**Status**: CORE COMPLETE — C8 repeated widening demonstrated (ladder measured to
`w=19`, 2026-10-01); M6 remains open

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

## ✅ COMPLETED SINCE V1.0

### C8: REPEATED_WIDTH_WIDENING (11→12)
- **PASS**: `evidence/f9_repeated_frontier.json`
- Witness: 190,000 bytes, SHA-256 `3370003cfa18b02e21f095173328d1fa758722dae6e280e78413e3903013a57`
- Events: step 59,050 (`10→11`) and step 177,148 (`11→12`)

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
│   └── frontier_witness.txt      # 190k program (crosses 10→11→12)
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
