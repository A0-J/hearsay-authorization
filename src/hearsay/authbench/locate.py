"""The pinned AuthorizationBench checkout.

The benchmark is not vendored. `experiments/fetch_authbench.py` clones it into
third_party/AuthorizationBench at PINNED_COMMIT (or set AUTHBENCH_ROOT to another
checkout). Its modules are imported as the `authorization_eva_sandbox` package.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/PEACH-Research-Lab/AuthorizationBench.git"
PINNED_COMMIT = "bfe1fc27b513d47dd02a0b5625ccb4f9a2b0e47c"
DEFAULT_ROOT = Path(__file__).resolve().parents[3] / "third_party" / "AuthorizationBench"


def authbench_root() -> Path:
    root = Path(os.environ.get("AUTHBENCH_ROOT") or DEFAULT_ROOT).resolve()
    if not (root / "authorization_eva_sandbox").is_dir():
        raise RuntimeError(f"AuthorizationBench checkout not found at {root}. "
                           "Run `python experiments/fetch_authbench.py` or set AUTHBENCH_ROOT.")
    return root


def tasks_dir() -> Path:
    return authbench_root() / "authorization_eva_sandbox" / "tasks"


def ensure_importable() -> Path:
    """Put the checkout on sys.path so `authorization_eva_sandbox.*` imports resolve."""
    root = authbench_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def checkout_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=authbench_root(), text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError, RuntimeError):
        return None


def require_utf8_mode() -> None:
    """The benchmark reads its bundles with the platform default encoding; on Windows that is not UTF-8."""
    if os.name == "nt" and not sys.flags.utf8_mode:
        raise RuntimeError("Run with PYTHONUTF8=1 (Windows): AuthorizationBench reads its UTF-8 bundles with the "
                           "platform default encoding.")
