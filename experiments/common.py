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

# One model for every LLM role: the independent variable is the evidence a verifier sees, not the model.
# Mixed models belong only to the separate model-comparison experiments.
MODEL = "gpt-4.1"
COORDINATOR_MODEL = EXECUTOR_MODEL = VERIFIER_MODEL = RESTATE_MODEL = MODEL
N_VERIFY = 3        # verifier votes per guarded call (strict majority approves)
N_RESTATE = 5       # coordinator restatements per base task (the semantic flow's reference)
API_MAX_RETRIES = 8


ANTHROPIC_KEY_FILE = ROOT / "anthropic_api_key.txt"   # gitignored; used only when ANTHROPIC_API_KEY is not set


def anthropic_client():
    from hearsay.anthropic_client import AnthropicClient
    key = os.environ.get("ANTHROPIC_API_KEY") or (
        ANTHROPIC_KEY_FILE.read_text(encoding="utf-8").strip() if ANTHROPIC_KEY_FILE.exists() else "")
    return AnthropicClient(key, max_retries=API_MAX_RETRIES)


def client_for(model: str):
    """The API client that serves `model` (Claude models through the Anthropic adapter)."""
    return anthropic_client() if model.startswith("claude-") else openai_client()


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


FATAL_MARKERS = ("usage limit", "credit balance", "insufficient_quota", "exceeded your current quota",
                 "billing", "invalid x-api-key", "invalid api key", "incorrect api key", "authentication",
                 "permission_denied", "HTTP 401", "HTTP 403")


def fatal_api_error(e: BaseException) -> str | None:
    """A reason if retrying cannot help (usage limit, quota, billing, authentication): the run should pause rather
    than record failures. Keys are never included in the reason."""
    text = f"{type(e).__name__}: {e}"
    low = text.lower()
    if any(m.lower() in low for m in FATAL_MARKERS):
        import re
        return re.sub(r"(sk-[A-Za-z0-9_\-]{6})[A-Za-z0-9_\-]+", r"\1...", text)[:500]
    return None


def write_paused(out, *, reason: str, done: int, total: int, resume: str) -> None:
    import json
    (out / "PAUSED.json").write_text(json.dumps({
        "time": datetime.now(timezone.utc).isoformat(), "reason": reason, "recorded": done, "planned": total,
        "remaining": total - done, "resume": resume,
        "note": "every completed call/episode is already saved; rerunning the same command resumes"}, indent=2) + "\n",
        encoding="utf-8")
