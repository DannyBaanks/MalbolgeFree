# F10 raw captures (annexed 2026-10-18)

The published F10 result is `evidence/f10_quine_epochal_20261018.json`. This
directory holds the *raw* output that surrounded it: the console summary of the
sealed run, its resource usage, and the two bounded trial reports that were run
before the sealed one. They are byte-for-byte copies of what the machine
produced — nothing here was regenerated, reformatted or edited, and each file's
SHA-256 is listed in `SHA256SUMS.txt` under the 2026-10-18 entry-31 block.

Why keep them: the trials are negative results, and the repository's rule is that
negative results are preserved, not summarized away. The sealed report's `trial`
block describes them in prose; these are the measurements themselves.

## Files

| file | what it is | how it was produced |
|---|---|---|
| `sealed_run_console.txt` | the checker's own stdout: 10 `MATCH` lines, `all_match=True verdicts=10`, and the three profile rows with their steps and stdout lengths | `python3 evidence/compare_quine_epochal.py --output evidence/f10_quine_epochal_20261018.json`, stdout captured |
| `sealed_run_resource_usage.txt` | GNU `/usr/bin/time` report for that same run: wall 1:14.69, user 74.26 s, `Maximum resident set size 110276 kB`, `Exit status: 0` | `/usr/bin/time python3 evidence/compare_quine_epochal.py --output …` |
| `trial_stdout_budget_15000.json` | full report of the first bounded trial (`MALFREE_F10_STDOUT_BUDGET=15000`): `all_match false`, 5 FALSIFIED of 9 verdicts | same script, budget overridden, output to a scratch path |
| `trial_stdout_budget_1000000.json` | full report of the second trial (`MALFREE_F10_STDOUT_BUDGET=1000000`): `all_match false`, 2 FALSIFIED, 10 verdicts | same script, budget overridden, output to a scratch path |

## What each falsification means — read before quoting these files

- **`classic_reproduces_the_quine` is FALSIFIED in both trials for a budget reason,
  not a behavioural one.** Classic needs 69 547 437 steps; the trials stopped at
  `MAX_STEPS` 15 000 (0 bytes emitted so far) and 1 000 000 (837 bytes). Neither
  trial says anything about whether Classic reproduces the quine — only that a
  truncated run cannot show it. The sealed run is the one that measured it.
- **`free_profiles_halt_before_classic` is FALSIFIED in both trials** for the same
  reason: with Classic cut off at `MAX_STEPS`, "before Classic" has no meaning.
- **`pre_execution_images_are_profile_independent` is FALSIFIED only in the
  15 000-step trial, and it is our own defect, visible in the file**: that report's
  `addressed_first_diff` values are the *string* `"null"` rather than JSON `null`.
  The Zig driver prints optional integers with `{?d}`, which emits the literal text
  `null`, and the checker compared it as a string. The parsing was fixed before the
  next trial; in the 1 000 000-step report the same fields are real `null`s and the
  verdict is MATCH.
- **`prefix_preservation_holds_before_the_frontier` is FALSIFIED only in the
  15 000-step trial**, and this is the expectation that was corrected: it required
  the earliest `pure_fixed` vs `epochal` divergence to be within ±1 of the widening
  step. Measured 1274 on the `d_after` field alone and 1246 over all five compared
  fields — both *after* the widening at 1230. Invariant P1 says "equal until the
  first WIDEN", so the expectation became `>=`, and it holds in the second trial and
  in the sealed run. The runtime was not touched to fit; the expectation was.
- **`epochal_diverges_from_classic_in_stdout` exists only in the 15 000-step trial,
  where it is FALSIFIED** — and again the cause is the budget: at that cut the
  `classic` row had emitted 0 bytes, so the comparison was between two empty
  outputs. It was replaced by two separately named claims,
  `epochal_stdout_is_not_classic_stdout` (the two stdout hashes differ) and
  `epochal_diverges_from_classic_from_the_first_byte` (the first differing byte is
  index 0), which is why that trial has 9 verdicts and the later runs have 10. Both
  replacements already hold in the 1 000 000-step trial.
- **One expectation is renamed between the two trials and the sealed report.** The
  15 000-step trial records `divergence_begins_at_the_frontier_step`, the later runs
  record `the_frontier_crossing_explains_the_divergence`; both read MATCH. The name
  changed because the measured relation is that the `classic` vs `pure_fixed`
  divergence falls within ±1 step of the recorded crossing (1229 against 1230), not
  that it begins exactly at it. Nothing was dropped — claim for claim, the two lists
  differ only by that rename and by the stdout split above. The intermediate version
  of the checker is not in git history, so the earlier predicate itself is quoted from
  the trial report's verdict list, not from source.

## Scope of this annex

Nothing here adds a claim. The measurement of `EPOCHAL_ON_REAL_QUINE` is the sealed
report, whose interpretation lives in `evidence/F10_QUINE_EPOCHAL_20261018.hashes.json`
and `docs/HONESTY_LEDGER.md` entry 29; these files document how that report was
arrived at, including the false starts. The trials ran on the same machine, same
Zig 0.16.0 / Python 3.12.3, same pinned program
(`DannyBaanks/MalDOOM:vendor/quines/quine_lutter.malbolge`, sha256 `dca8476f…`).
