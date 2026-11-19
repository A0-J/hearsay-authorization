"""Record or check the files a pre-registration fixes. No API calls.

    python experiments/check_freeze.py docs/SIG_FREEZE_r3.json                 # check: exit 1 if any file differs
    python experiments/check_freeze.py docs/SIG_FREEZE_r3.json --write PATH... # record (files or directories)

Each file's SHA-256 is taken with CRLF normalized to LF, so a checkout with other line-ending settings gives the same
hashes. The freeze file also holds one hash over all entries (`all_files_sha256`), the single value to cite or
timestamp elsewhere.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def expand(paths: list[str]) -> list[str]:
    out = []
    for p in paths:
        full = ROOT / p
        if full.is_dir():
            out += [x.relative_to(ROOT).as_posix() for x in sorted(full.rglob("*")) if x.is_file()]
        elif full.is_file():
            out.append(Path(p).as_posix())
        else:
            raise SystemExit(f"no such file or directory: {p}")
    return sorted(set(out))


def overall(files: dict[str, str]) -> str:
    return hashlib.sha256("".join(f"{k}\0{v}\n" for k, v in sorted(files.items())).encode()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("freeze_file")
    ap.add_argument("--write", nargs="+", metavar="PATH")
    ap.add_argument("--note", default="")
    a = ap.parse_args()
    target = ROOT / a.freeze_file
    if a.write:
        files = {p: file_sha(ROOT / p) for p in expand(a.write)}
        target.write_text(json.dumps({"recorded": date.today().isoformat(), "note": a.note,
                                      "hash": "sha256 of each file with CRLF normalized to LF",
                                      "all_files_sha256": overall(files), "files": files},
                                     indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"recorded {len(files)} files -> {a.freeze_file}; all_files_sha256 {overall(files)}")
        return 0
    frozen = json.loads(target.read_text(encoding="utf-8"))
    bad = []
    for p, want in frozen["files"].items():
        full = ROOT / p
        if not full.is_file():
            bad.append(f"missing: {p}")
        elif file_sha(full) != want:
            bad.append(f"changed: {p}")
    if overall(frozen["files"]) != frozen["all_files_sha256"]:
        bad.append("the freeze file's own entries were edited")
    if bad:
        print(f"FREEZE CHECK FAILED ({a.freeze_file}):\n  " + "\n  ".join(bad))
        return 1
    print(f"freeze check passed: {len(frozen['files'])} files match {a.freeze_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
