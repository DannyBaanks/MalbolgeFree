# GitHub evidence receipt

Measured commit: edefe6a2eb51bbc33b075382b2d4a55a2fddd551.
Run: https://github.com/DannyBaanks/MalbolgeFree/actions/runs/37850925619
Artifact11581714106, start1-37850925619-1,93382 bytes.
Created2026-10-08T22:09:21Z; remote expiry2027-01-06T22:02:47Z.
GitHub API archive digest:sha256:ad0710a0274a9612f9fbf9c23c7f203b3b94bea938a06b0ef71a865cf3521ebd.
Archive digest is the API value; extracted file hashes were independently verified.
Original hashes.json remains unchanged; added reports/CSV use receipt_hashes.json.

Actually executed, exit0:

```bash
gh run download 37850925619 --repo DannyBaanks/MalbolgeFree --dir /tmp/start1-artifacts-37850925619
python3 evidence/START1_SCALE_CI_20261008/verify_start1.py /tmp/start1-artifacts-37850925619/start1-37850925619-1
```

First download failed transiently connecting to api.github.com; retry succeeded.
Verifier checks original artifact hashes, command exits, raw log parsing,
small original/observed/repeat equality, Python output hashes, all20 rows,
per-row peak within budget and19 events at20. Receipt creation additionally
checked exact source/storage arithmetic and60% RAM budget on all gates.
commands.json records actual build/run arguments and limits. provenance.json
records environment and source hashes. CSV derives only from runs.json (LF).
No original runtime changed; no merge to master; no monorepo push.
Result receipt commit uses [skip ci] to avoid rerunning the full experiment.
