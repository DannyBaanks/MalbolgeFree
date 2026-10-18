#!/usr/bin/env python3
"""Verify the release seal manifest against the bytes actually on disk (S1).

`SHA256SUMS.txt` is this repository's claim about what it shipped. Until now the
claim was only ever checked by whoever ran `sha256sum -c` on the sealing machine,
so CI could publish bytes that no longer matched their own hashes. This gate makes
the seal a per-run measurement on every runner.

Format (GNU coreutils `sha256sum` compatible, read positionally so a path may
contain spaces):

    <64 hex>  <path>      binary mode, two spaces
    <64 hex> *<path>      text mode (never used here, accepted anyway)
    # ...                 comment, including the dated re-seal blocks
    <blank>               ignored

Paths are repository-root-relative. Everything else is an integrity failure, not
a behavioural one, which is why the exit codes deliberately do not follow the
verdict convention used by the parity gates:

    0  every sealed path matches
    4  integrity failure: a hash drifts, a path is missing, a line is malformed,
       a path is absolute or escapes the repository, a path is listed twice, or
       the manifest itself is absent

Exit 3 (skip) is unreachable by design: there is no external input here, so a
checkout either has its seal or it does not. An absent manifest is a hard failure
rather than a skip, because a repository that lost its manifest has lost the claim
this gate exists to test.

The file hashes are computed with `hashlib`, never by shelling out to
`sha256sum`: Windows runners have no such utility, and the whole point is that
the check must run identically on every platform. `.gitattributes` pins `* -text`,
so a fresh checkout is byte-exact and a CRLF re-write on the runner is reported as
drift — the same defect entry 26 caught on a vendored oracle, caught here for the
whole sealed tree.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "SHA256SUMS.txt"
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")


def sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def parse(lines: list[str]) -> tuple[list[tuple[str, str]], list[str]]:
    """Return (entries, malformed). Entries are (expected_hex, relpath)."""
    entries: list[tuple[str, str]] = []
    malformed: list[str] = []
    for number, line in enumerate(lines, start=1):
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if len(line) < 67 or not HEX64.match(line[:64]):
            malformed.append(f"line {number}: {line[:90]}")
            continue
        mode = line[65]
        if mode not in (" ", "*"):
            malformed.append(f"line {number}: separator is {mode!r}, not ' ' or '*'")
            continue
        entries.append((line[:64].lower(), line[66:]))
    return entries, malformed


def main() -> int:
    if not MANIFEST.is_file():
        print("SEAL_MANIFEST_ABSENT: SHA256SUMS.txt is not in this checkout", file=sys.stderr)
        return 4

    raw = MANIFEST.read_bytes()
    manifest_sha = hashlib.sha256(raw).hexdigest()
    entries, malformed = parse(raw.decode("utf-8", errors="replace").splitlines())

    drift: list[str] = []
    missing: list[str] = []
    escaping: list[str] = []
    seen: dict[str, int] = {}
    duplicates: list[str] = []

    for expected, rel in entries:
        if rel in seen:
            seen[rel] += 1
            duplicates.append(f"{rel} listed {seen[rel]} times")
        else:
            seen[rel] = 1

        target = pathlib.PurePosixPath(rel)
        if pathlib.PureWindowsPath(rel).is_absolute() or rel.startswith("/") or target.is_absolute():
            escaping.append(f"{rel}: absolute")
            continue
        if ".." in target.parts:
            escaping.append(f"{rel}: escapes the repository")
            continue

        path = ROOT / rel
        if not path.is_file():
            missing.append(rel)
            continue
        found = sha256_of(path)
        if found != expected:
            drift.append(f"{rel}: sealed {expected[:12]}... found {found[:12]}...")

    checked = len(entries) - len(missing) - len(escaping)
    print(
        "SEAL manifest_sha256={} entries={} checked={} ok={} drift={} "
        "missing={} escaping={} duplicate={} malformed={}".format(
            manifest_sha, len(entries), checked,
            checked - len(drift), len(drift), len(missing), len(escaping),
            len(duplicates), len(malformed),
        )
    )

    for label, items in (
        ("SEAL_DRIFT", drift),
        ("SEAL_MISSING", missing),
        ("SEAL_PATH_ESCAPE", escaping),
        ("SEAL_DUPLICATE", duplicates),
        ("SEAL_MALFORMED_LINE", malformed),
    ):
        for item in items:
            print(f"{label}: {item}", file=sys.stderr)

    broken = drift or missing or escaping or duplicates or malformed
    if broken:
        print("SEAL VERDICT: FAIL", file=sys.stderr)
        return 4
    print("SEAL VERDICT: PASS (every sealed path on disk matches its recorded SHA-256)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
