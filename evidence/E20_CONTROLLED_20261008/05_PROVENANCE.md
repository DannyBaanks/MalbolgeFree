# Provenance and reproduction

Base runtime commit: 621fa40d29571f8f0bc44ff7af279b18e10479df.
All changes are under this new evidence directory. Historical evidence and
runtime source were not modified. `source_hashes.json` identifies the runtime,
tests, witness and stock probe; `hashes.json` identifies every evidence artifact
except itself. No credentials, hostnames or source over 1 GB are included.

External reference archive URL:
https://git.trs.css.i.nagoya-u.ac.jp/malbolge/malbolge20-interpreter/-/archive/master/malbolge20-interpreter-master.tar.gz

Executed acquisition commands (temporary filenames anonymized consistently):
`curl -L --max-time 20 -I <archive-url>` failed with exit 6 (sandbox DNS).
`curl -L --max-time 30 -o /tmp/nagoya-malbolge20-master.tar.gz <archive-url>`
ran with network approval, exit 0. `tar -tzf` and `tar -xzf ... -C /tmp`, exit 0.
`git ls-remote <project-url>.git HEAD` failed with exit 128 (sandbox DNS),
then succeeded with network approval, exit 0; HEAD is recorded separately from
the archive hash, not asserted as a content-pinned archive revision.
Archive SHA-256 is in `source_hashes.json`. MIT LICENSE accompanies all copies.

Execution commands and exit codes are recorded exactly as argument arrays in
`02_RUN.json` and `nagoya_compare.json`; raw command output and GNU time
metrics are in adjacent `.log` files. GNU time wraps all their child commands.
Compiler/runtime versions are in `versions.log`. All experimental commands
returned 0. Semantic comparison failed despite successful process exits.

Reproduce from repository root, choosing **new** output directories:

```bash
env E20_OUTPUT=/tmp/e20-fresh-calibration PYTHONDONTWRITEBYTECODE=1 python3 evidence/E20_CONTROLLED_20261008/collect.py
env E20_OUTPUT=/tmp/e20-fresh-compare PYTHONDONTWRITEBYTECODE=1 python3 evidence/E20_CONTROLLED_20261008/compare.py
python3 evidence/E20_CONTROLLED_20261008/verify.py
```

`collect.py` is intentionally a small-run collector, never an E20 launcher.
Its recorded decision is for this blocked session; reassess resource gates
manually before any future full-run experiment. Freeze guards refuse reusing
existing output manifests. Both collectors were replayed after the output
guards were added; replay outputs are preserved under `recheck/`.
Small child processes used RLIMIT_AS=2 GiB, CPU=180 s, no core dump,
subprocess timeout=240 s. Python reference comparison itself runs the modest
corpus directly; it is not a large-memory benchmark.

The original three historical dense rungs were checked against their recorded
steps, widths, growth and cells, and their file bytes against the base Git blob.
This verifies preservation/internal consistency, not historical execution time
or a fresh real-VM replication. Stock SHA256SUMS is not assumed current.

Limits: no billion-step run, no per-WIDEN event collection, no VM stdout hash
for the stock calibration (it exposes only length), no global conformance.
EOF mismatch is a measured negative, not repaired. The finite corpus includes
an official sample and two small accepted cases; targeted operation coverage
was not audited after the STOP condition.
