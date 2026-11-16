"""Against live AuthorizationBench services (0 API calls). Skipped without the pinned checkout and its deps.

Runs in subprocesses because the benchmark needs UTF-8 mode on Windows (PYTHONUTF8=1).
"""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from hearsay.authbench.locate import DEFAULT_ROOT

ROOT = Path(__file__).resolve().parents[1]
TASK = "T0010-l-b-h"
pytestmark = pytest.mark.skipif(
    not (Path(os.environ.get("AUTHBENCH_ROOT") or DEFAULT_ROOT) / "authorization_eva_sandbox").is_dir()
    or importlib.util.find_spec("fastapi") is None or importlib.util.find_spec("uvicorn") is None,
    reason="AuthorizationBench checkout or its dependencies are not installed")


def run(*args, cwd=ROOT):
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONPATH": str(ROOT / "src")}
    return subprocess.run([sys.executable, *args], cwd=cwd, env=env, capture_output=True, text=True,
                          encoding="utf-8", timeout=300)


def test_blocked_calls_never_reach_the_service():
    p = run("-m", "hearsay.authbench.selfcheck", "--task", TASK, "--args",
            json.dumps({"to": ["selfcheck@example.com"], "subject": "selfcheck", "body": "selfcheck"}))
    report = json.loads(p.stdout[p.stdout.index("{"):])
    assert p.returncode == 0 and report["passed"], json.dumps(report, indent=2)
    assert len(report["checks"]) == 5


def test_dry_run_episode(tmp_path):
    name = f"pytest_{os.getpid()}"
    record = tmp_path / "record.json"
    record.write_text(json.dumps({"roles": {"lead": "Team lead"}, "authority": {"lead": ["email_client.*"]},
                                  "approvals": [{"approval_id": "APR-7", "issuer": "lead",
                                                 "tool": "email_client.send_message"}]}))
    out = ROOT / "results" / "authbench" / name
    try:
        for enforce, record_args, executed in (("provenance_gate", [], 0),
                                               ("provenance_gate", ["--record", str(record)], 1)):
            p = run("experiments/run_authbench.py", "--task", TASK, "--name", name, "--dry-run",
                    "--enforce", enforce, *record_args)
            assert p.returncode == 0, p.stderr[-2000:]
            ep = json.loads((out / TASK / "r0" / "episode.json").read_text(encoding="utf-8"))
            assert len(ep["proposals"]) == 1 and len(ep["executed_state_changes"]) == executed
            assert set(ep["proposals"][0]["decisions"]) == {"none", "llm_claim_only", "llm_with_evidence",
                                                             "provenance_gate"}
            assert ep["unexplained_state_changes"] == []
            assert ep["config"]["role_models"] == {"planner": "gpt-4.1", "executor": "gpt-4.1", "verifier": "gpt-4.1"}
            if not executed:
                assert "email_client" not in ep["services_changed"]
    finally:
        import shutil
        shutil.rmtree(out, ignore_errors=True)
