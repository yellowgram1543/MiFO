"""Rehydrate raw datasets fetchable from this sandbox (GitHub-reachable only).

Usage: python3 scripts/fetch_data.py

Downloads any missing FakeNewsNet CSVs and verifies SHA256 checksums
against the provenance record in data/README.md. Exits non-zero on
checksum mismatch so it can gate other scripts.

NOTE (D8): raw data in this sandbox is EPHEMERAL across sessions
(untracked + git-ignored files do not survive environment restores).
Every dataset must be rehydratable by a committed script like this one.
"""
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "fakenewsnet"

# name -> first 16 hex of SHA256 (full provenance record: data/README.md)
FILES = {
    "politifact_fake.csv": "abe7fe7aad801b1e",
    "politifact_real.csv": "2500f86a7addca0f",
    "gossipcop_fake.csv": "c6932bffadb1230b",
    "gossipcop_real.csv": "d721e9a8b7e660da",
}
API = "repos/KaiDMML/FakeNewsNet/contents/dataset/{name}"


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    ok = True
    for name, expect in FILES.items():
        dest = RAW / name
        if dest.exists() and sha16(dest) == expect:
            print(f"OK (cached)     {name}")
            continue
        r = subprocess.run(
            ["gh", "api", API.format(name=name),
             "-H", "Accept: application/vnd.github.raw"],
            capture_output=True,
        )
        if r.returncode != 0 or not r.stdout:
            print(f"FAIL (download) {name}: {r.stderr.decode()[:120]}")
            ok = False
            continue
        dest.write_bytes(r.stdout)
        got = sha16(dest)
        match = got == expect
        print(f"{'OK' if match else 'MISMATCH':<15} {name}"
              + ("" if match else f" (got {got}, expected {expect})"))
        ok = ok and match
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
