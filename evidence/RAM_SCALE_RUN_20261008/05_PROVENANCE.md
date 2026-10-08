# RAM sweep evidence receipt

Measured commit: f472b42953a6cece12d4615a41219586eaffe2b7.
Run: https://github.com/DannyBaanks/MalbolgeFree/actions/runs/37848647590
Artifact ID: 11581386500; size 39451 bytes; created 2026-10-08T21:47:20Z;
remote expiry 2027-01-06T21:42:31Z.
API archive digest: sha256:40c286942e491eb9fa6bafb72e062f17720ae47d7faf99dc65decafba17a81b8.
Archive digest is GitHub's API value; extracted original file hashes were
independently verified locally after download. Original hashes.json was not
rewritten. Added reports and CSV are covered by receipt_hashes.json.

Actually executed commands, exit 0:

```bash
python3 -m unittest discover -s evidence/RAM_SCALE_CI_20261008 -p 'test_*.py' -v
git push origin research/e20-controlled-20261008
gh run view 37848647590 --repo DannyBaanks/MalbolgeFree --json status,conclusion
gh run download 37848647590 --repo DannyBaanks/MalbolgeFree --dir /tmp/ram-scale-artifacts-37848647590
python3 evidence/RAM_SCALE_CI_20261008/verify_scale.py /tmp/ram-scale-artifacts-37848647590/ram-scale-37848647590-1
```

The same verifier was run on evidence/RAM_SCALE_RUN_20261008 after copying
the extracted artifact byte-for-byte. It checks source/event/result hashes,
each rung's peak within budget, and absence of next-rung source configuration
or execution log. E20 hashes/events/fields were also compared with the prior
E20_GITHUB_RUN_20261008 evidence and matched exactly.

commands.json records precise build/run arguments, exit codes, limits and log
hashes. provenance.json records harness hash, measured commit, platform, Zig,
and original observation-only core/probe provenance. environment_before_*.json
contains MemTotal/MemAvailable/swap/disk, memory pressure and process limits.
All benchmark commands returned 0; NO_GO is a preventative result, not failure
of the hypothesis. Only seven real rungs ran; 21 was neither built nor run.

CSV is derived from runs.json with exact bytes and parent-measured executable
wall seconds; timing includes generation/load/run/hashes, no compilation.
Ideal bigger-RAM tables are derived integer arithmetic on this witness's
source/storage requirements, not measurements. No global dependencies were
installed, no runtime changed, no remote larger runner rented, no OOM.

The receipt-only commit uses [skip ci] to avoid repeating the measured sweep.
Historical artifacts remain unchanged. This is a finite workload experiment,
not a universal relation between physical RAM and Malbolge word width.
