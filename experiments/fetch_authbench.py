"""Clone AuthorizationBench at the pinned commit into third_party/AuthorizationBench (gitignored)."""

from __future__ import annotations

import subprocess
import sys

import common  # noqa: F401  (puts src/ on sys.path)

from hearsay.authbench.locate import DEFAULT_ROOT, PINNED_COMMIT, REPO_URL


def git(*args: str) -> None:
    subprocess.run(["git", "-c", "core.longpaths=true", *args], check=True)


def main() -> None:
    if not (DEFAULT_ROOT / ".git").is_dir():
        DEFAULT_ROOT.parent.mkdir(parents=True, exist_ok=True)
        git("clone", "--quiet", REPO_URL, str(DEFAULT_ROOT))
    git("-C", str(DEFAULT_ROOT), "fetch", "--quiet", "origin")
    git("-C", str(DEFAULT_ROOT), "checkout", "--quiet", PINNED_COMMIT)
    print(f"AuthorizationBench at {PINNED_COMMIT[:12]} in {DEFAULT_ROOT}")


if __name__ == "__main__":
    sys.exit(main())
