# Evidence receipt

GitHub run: https://github.com/DannyBaanks/MalbolgeFree/actions/runs/37847283479
Measured commit: ac94be2b92345e2d872f05e265f853b4d3afac3e.
GitHub runner image ubuntu-24.04, version 20261004.327.1, Ubuntu 24.04.5;
Zig 0.16.0. API artifact 11580581035, created 2026-10-08T21:34:18Z, 26623 bytes,
archive digest sha256:718ef08cbddd7878cacd5c55e952f51b967054f987b31a87bfb5ff0e4927303d.
The remote artifact expires 2027-01-06; its extracted contents are preserved
in Git here with their original hashes.json. Archive digest is GitHub's API
value; extracted file hashes were independently checked locally.

Commands actually executed (all exit 0):

```bash
git push origin research/e20-controlled-20261008
gh run view 37847283479 --repo DannyBaanks/MalbolgeFree --json status,conclusion
gh run download 37847283479 --repo DannyBaanks/MalbolgeFree --dir /tmp/e20-github-artifacts-37847283479
python3 evidence/E20_CI_20261008/verify_ci.py /tmp/e20-github-artifacts-37847283479/e20-37847283479-1
```

The last command reported DEMONSTRATED_SCOPED and verified raw file hashes,
small differential, all ten boundary events, final pointers and resource budget.
The same verifier was run on the Git-preserved directory.
receipt_hashes.json also covers these added report files; original downloaded
hashes.json remains unchanged. No giant source/stdout or binary is committed.

Resource observations are in preflight.json and calibration18.json; GNU time
logs show command limits were accepted. The collector code applies CPU 600 s,
wall 660 s and an address-space cap equal to 60% of available RAM. Inherited
process-limit and /proc/pressure snapshots were not collected on the CI host;
this is an evidence limitation, not an inferred pressure measurement. The
fresh GitHub VM ran one experiment job. Its full public job log retains the
runner image details, action revisions and success status.

No regression checks were bypassed: runtime tests and comparison preceded the
full run. The results-only documentation commit uses [skip ci] to avoid running
the billion-step experiment again; the measured commit is explicitly separate.
Master was not merged or rewritten. Older local blocked evidence is preserved.
