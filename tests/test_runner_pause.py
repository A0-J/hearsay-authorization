"""The verifier-only runner pauses on a fatal API error, a STOP file or --stop-after, keeps every reply already
returned, and resumes without duplicates (0 API calls)."""

import json
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))

import run_exp1  # noqa: E402
from common import fatal_api_error  # noqa: E402

from hearsay.llm import sampling_for  # noqa: E402


class LimitedClient:
    """Answers `ok` calls, then raises the Anthropic usage-limit error on every call."""

    def __init__(self, ok: int) -> None:
        self.ok, self.calls, self.lock, self.responses = ok, 0, threading.Lock(), self

    def create(self, *, model, instructions, input, **_):
        with self.lock:
            self.calls += 1
            if self.calls > self.ok:
                raise RuntimeError("HTTP 400: invalid_request_error: You have reached your specified API usage "
                                   "limits. You will regain access on 2026-12-01 at 00:00 UTC.")
        return SimpleNamespace(output_text='{"decision": "reject", "basis": "none", "reason": "x"}', model=model,
                               usage=SimpleNamespace(input_tokens=1, output_tokens=1))


def config(tmp_path: Path) -> Path:
    instr = json.loads((ROOT / "dataset" / "exp1" / "instructions.json").read_text(encoding="utf-8"))
    cfg = {"experiment_id": "T-pause", "model": "gpt-4.1", "sampling": sampling_for("gpt-4.1"), "repeats": 1,
           "workers": 4, "dataset_dir": "exp1", "dataset_version": "1.0.0-exp1",
           "instructions_sha256": {k: v["sha256"] for k, v in instr.items()}}
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return p


def run(monkeypatch, tmp_path, client, *extra):
    monkeypatch.setattr(run_exp1, "RESULTS", tmp_path / "results")
    monkeypatch.setattr(run_exp1, "client_for", lambda model: client)
    monkeypatch.setattr(sys, "argv", ["run_exp1.py", "--config", str(config(tmp_path)), *extra])
    return run_exp1.main()


def rows(tmp_path):
    p = tmp_path / "results" / "T-pause" / "verdicts.jsonl"
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()]


def test_fatal_error_is_classified():
    assert fatal_api_error(RuntimeError("HTTP 400: You have reached your specified API usage limits."))
    assert fatal_api_error(RuntimeError("Error code: 429 - insufficient_quota"))
    assert fatal_api_error(RuntimeError("HTTP 529: overloaded_error")) is None


def test_pause_on_usage_limit_keeps_results_and_resumes(monkeypatch, tmp_path):
    assert run(monkeypatch, tmp_path, LimitedClient(ok=40)) == 3
    first = rows(tmp_path)
    assert len(first) == 40                                       # every answered call was saved, nothing else
    paused = json.loads((tmp_path / "results" / "T-pause" / "PAUSED.json").read_text(encoding="utf-8"))
    assert "usage limits" in paused["reason"] and paused["recorded"] == 40
    assert run(monkeypatch, tmp_path, LimitedClient(ok=10 ** 6)) == 0          # resume with access restored
    allrows = rows(tmp_path)
    keys = [(r["cell_id"], r["repeat"]) for r in allrows]
    assert len(keys) == len(set(keys)) == 1276
    assert not (tmp_path / "results" / "T-pause" / "PAUSED.json").exists()


def test_stop_after_and_stop_file(monkeypatch, tmp_path):
    assert run(monkeypatch, tmp_path, LimitedClient(ok=10 ** 6), "--stop-after", "25") == 3
    assert len(rows(tmp_path)) == 25
    (tmp_path / "results" / "T-pause" / "STOP").write_text("", encoding="utf-8")
    assert run(monkeypatch, tmp_path, LimitedClient(ok=10 ** 6)) == 3
    assert len(rows(tmp_path)) == 25
    (tmp_path / "results" / "T-pause" / "STOP").unlink()
    assert run(monkeypatch, tmp_path, LimitedClient(ok=10 ** 6)) == 0
    assert len(rows(tmp_path)) == 1276
