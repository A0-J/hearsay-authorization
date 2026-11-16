"""Shared settings for the experiment scripts."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

RESULTS = ROOT / "results"
KEY_FILE = ROOT / "openai_api_key.txt"   # gitignored; used only when OPENAI_API_KEY is not set

COORDINATOR_MODEL = "gpt-4o-mini"
EXECUTOR_MODEL = "gpt-4.1"
VERIFIER_MODEL = "gpt-4.1"
RESTATE_MODEL = "gpt-4o-mini"
N_VERIFY = 3        # verifier votes per guarded call (strict majority approves)
N_RESTATE = 5       # coordinator restatements per base task (the semantic flow's reference)
API_MAX_RETRIES = 8


def openai_client():
    from openai import OpenAI
    if not os.environ.get("OPENAI_API_KEY") and KEY_FILE.exists():
        os.environ["OPENAI_API_KEY"] = KEY_FILE.read_text(encoding="utf-8").strip()
    return OpenAI(max_retries=API_MAX_RETRIES, timeout=120.0)


def git_info() -> dict:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
                                         stderr=subprocess.DEVNULL).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())
        return {"commit": commit, "dirty": dirty}
    except Exception:
        return {"commit": None, "dirty": None}


def run_meta(**extra) -> dict:
    return {"time": datetime.now(timezone.utc).isoformat(), "git": git_info(),
            "python": sys.version.split()[0], **extra}
