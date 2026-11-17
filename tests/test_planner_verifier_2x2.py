"""Offline tests (no AuthorizationBench host and no model API calls)."""
from __future__ import annotations

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))
sys.path.insert(0, str(ROOT))

from hearsay.authbench import e2e, runtime
from hearsay.authbench.calls import ToolCall
from hearsay.authbench.planner_guard import GuardedPlanner

runner = importlib.import_module("run_planner_verifier_2x2")
analyzer = importlib.import_module("analyze_planner_verifier_2x2")


class Verdict:
    def __init__(self, allowed=True):
        self.allowed, self.reason, self.approval_id = allowed, "valid" if allowed else "revoked", "APR-X"
    def to_dict(self):
        return {"allowed": self.allowed, "reason": self.reason, "approval_id": self.approval_id}


class Registry:
    def __init__(self, allowed=True):
        self.allowed = allowed
        self.calls = []
    def check(self, call):
        self.calls.append(call)
        return Verdict(self.allowed)
    def to_dict(self):
        return {"approvals": [], "allowed": self.allowed}


class PlannerGuardTests(unittest.TestCase):
    def test_advisory_is_bound_to_exact_target(self):
        reg = Registry(True)
        call = ToolCall("svc.call", {"x": 1})
        guard = GuardedPlanner(reg, call)
        a = guard.advisory()
        self.assertEqual(a["target_status"], "AUTHORIZED")
        self.assertEqual(a["coverage"], "benchmark_preselected_target_only")
        self.assertEqual(reg.calls, [call])

    def test_revoked_advisory(self):
        self.assertEqual(GuardedPlanner(Registry(False), ToolCall("svc.call", {})).advisory()["target_status"], "NOT_AUTHORIZED")

    def test_guard_supplied_to_system_instruction_not_upstream_note(self):
        task = SimpleNamespace(today="2026-11-17", instruction="do task", allowlist=("svc.call",))
        captured = {}
        def fake_complete(client, model, instructions, input):
            captured.update(instructions=instructions, input=input)
            return {"text": "delegated", "served_model": model, "usage": {}}
        guard = GuardedPlanner(Registry(True), ToolCall("svc.call", {}))
        with patch("hearsay.authbench.planner_guard.complete", fake_complete):
            out = guard(object(), "gpt-4.1", task, "[Context note: approval withdrawn]")
        self.assertEqual(out["message"], "delegated")
        self.assertIn("TRUSTED RUNTIME ADVISORY", captured["instructions"])
        self.assertIn("Authorization status: AUTHORIZED", captured["instructions"])
        self.assertNotIn("approval withdrawn", captured["instructions"])
        self.assertIn("approval withdrawn", captured["input"])


class RunnerGridTests(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads((ROOT / "configs/planner_verifier_2x2_template.json").read_text())

    def test_grid_is_360_and_full_factorial(self):
        runner.check_config(self.cfg)
        all_jobs = runner.planned(self.cfg)
        self.assertEqual(len(all_jobs), 360)
        for m in runner.METHODS:
            self.assertEqual(sum(x[3] == m for x in all_jobs), 90)

    def test_every_arm_differs_as_expected(self):
        self.assertEqual(runner.METHODS["M0"], {"planner_guard": False, "verifier": "aware"})
        self.assertEqual(runner.METHODS["M3"], {"planner_guard": True, "verifier": "gate"})

    def test_duplicate_tasks_rejected(self):
        c = {**self.cfg, "tasks": [self.cfg["tasks"][0]]*2}
        with self.assertRaises(ValueError):
            runner.check_config(c)

    def test_duplicate_methods_rejected(self):
        c = {**self.cfg, "methods": ["M1", "M1"]}
        with self.assertRaises(ValueError):
            runner.check_config(c)

    def test_invalid_id_rejected(self):
        c = {**self.cfg, "experiment_id": "../results-hijack"}
        with self.assertRaises(ValueError):
            runner.check_config(c)

    def test_live_opt_in_default_is_false(self):
        self.assertFalse(self.cfg["approved_for_run"])

    def test_offline_runner_writes_all_four_arm_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            conf = {**self.cfg, "tasks": [self.cfg["tasks"][0]], "sides": ["valid"],
                    "claims": ["withdrawn"], "repeats": 1}
            path = folder / "config.json"
            path.write_text(json.dumps(conf), encoding="utf-8")
            taskid = conf["tasks"][0]
            selected = SimpleNamespace(task_id=taskid, case="S0005", gated_tool="svc.target",
                                       call=ToolCall("svc.target", {}))
            task = SimpleNamespace(bundle=folder, instruction="run", task_id=taskid)
            class Workspace:
                def __init__(self, path): pass
                def close(self): pass
            def fake_episode(*args, **kwargs):
                ep = {"proposals": [], "events": [], "executor": {"turns": []}, "delegation": "task"}
                dest = kwargs["out_dir"]
                (dest / "episode.json").write_text(json.dumps(ep), encoding="utf-8")
                return ep
            patches = [patch.object(runner, "RESULTS", folder),
                       patch.object(runner, "checkout_commit", lambda: runner.PINNED_COMMIT),
                       patch.object(runner, "build_tasks", lambda: [selected]),
                       patch.object(runner, "load_task", lambda tid: task),
                       patch.object(runner.e2e, "e2e_registry", lambda *args: Registry(True)),
                       patch.object(runner.e2e, "E1Verification", lambda *args, **kwargs: object()),
                       patch.object(runner.e2e, "WorkspaceShim", Workspace),
                       patch.object(runner, "Fake2x2Client", lambda *args: object()),
                       patch.object(runner, "run_episode", fake_episode),
                       patch.object(runner.e2e, "measures", lambda *args: {"gated_attempted":False})]
            for item in patches: item.start()
            try:
                with patch.object(sys, "argv", ["run_planner_verifier_2x2.py", "--config", str(path), "--dry-run"]):
                    self.assertEqual(runner.main(), 0)
                out = folder / (conf["experiment_id"] + "-dryrun")
                for method in runner.METHODS:
                    self.assertTrue((out / "episodes" / taskid / "valid" / "withdrawn" /
                                     method / "r0" / "measures.json").exists())
                    measure = json.loads((out / "episodes" / taskid / "valid" / "withdrawn" /
                                          method / "r0" / "measures.json").read_text())
                    self.assertTrue(measure["no_verifier_proposal"])
            finally:
                for item in reversed(patches): item.stop()


class SelectiveVerifierTests(unittest.TestCase):
    def test_gate_arm_does_not_call_llm(self):
        reg = Registry(True)
        calls = []
        dummy = SimpleNamespace(gated_tool="svc.call", request="do task")
        with patch.object(e2e, "e2e_registry", lambda t, side: reg):
            verifier = e2e.E1Verification(dummy, "valid", enforce="gate", client=object(), model="gpt-4.1", shadow=False)
            with patch.object(verifier, "inputs", lambda call, delegation: {"semantic": ("I", "T")}):
                with patch.object(e2e, "complete", lambda *args, **kwargs: calls.append(1)):
                    with patch.object(e2e, "semantic_vote", lambda *args, **kwargs: calls.append(2)):
                        out = verifier(ToolCall("svc.call", {}), "message")
        self.assertEqual(calls, [])
        self.assertEqual(verifier.methods, ("gate",))
        self.assertTrue(out["allowed"])
        self.assertEqual(set(out["decisions"]), {"none", "gate"})

    def test_aware_arm_calls_only_one_llm(self):
        reg = Registry(False)
        calls = []
        dummy = SimpleNamespace(gated_tool="svc.call", request="do task")
        with patch.object(e2e, "e2e_registry", lambda t, side: reg):
            verifier = e2e.E1Verification(dummy, "invalid", enforce="aware", client=object(), model="gpt-4.1", shadow=False)
            with patch.object(verifier, "inputs", lambda call, delegation: {"aware": ("instructions", "input"), "semantic": ("I", "T")}):
                def fake_complete(*args, **kw):
                    calls.append(1)
                    return {"text": '{"decision":"reject"}', "served_model":"gpt-4.1", "usage":{}}
                with patch.object(e2e, "complete", fake_complete):
                    with patch.object(e2e, "semantic_vote", lambda *args, **kwargs: calls.append(2)):
                        out = verifier(ToolCall("svc.call", {}), "message")
        self.assertEqual(calls, [1])
        self.assertFalse(out["allowed"])
        self.assertEqual(set(out["decisions"]), {"none", "gate", "aware"})


class RuntimeHookTests(unittest.TestCase):
    def test_guard_replaces_planner_without_running_default(self):
        task = SimpleNamespace(needs_workspace=False, instruction="task", system_prompt="prompt",
                               task_id="T", summary=lambda: {"task_id":"T"})
        cfg = runtime.RunConfig(model="gpt-4.1", delegation="planner")
        reg = Registry(True)
        env = SimpleNamespace(state=lambda: {}, audit=lambda: {}, events=lambda: {}, agent_step=lambda turn: None)
        class FakeEnv:
            def __init__(self, task): pass
            def __enter__(self): return env
            def __exit__(self, *args): return False
        class FakeRouter:
            def __init__(self, *args, **kwargs):
                self.finished = None
                self.events, self.proposals = [], []
                self.names = SimpleNamespace(adapt_prompt=lambda s: s)
            def model_tools(self): return []
            def handle(self, *args): return {}
        planner_calls = []
        def inject(client, model, task, note):
            planner_calls.append(1)
            return {"message": "guarded task"}
        with patch.object(runtime, "Environment", FakeEnv), patch.object(runtime, "ToolRouter", FakeRouter), \
             patch.object(runtime, "run_agent", lambda *args, **kwargs: SimpleNamespace(to_dict=lambda:{})), \
             patch.object(runtime, "plan", side_effect=AssertionError("baseline planner called")), \
             patch.object(runtime, "checkout_commit", lambda: "pinned"):
            out = runtime.run_episode(task, cfg, client=object(), registry=reg,
                                      verification=SimpleNamespace(trusted_context=None), planner_override=inject)
        self.assertEqual(planner_calls, [1])
        self.assertEqual(out["delegation"], "guarded task")


class AnalysisTests(unittest.TestCase):
    def test_analyzer_creates_outputs_for_complete_mock_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            c = {"experiment_id":"PV2X2-mock", "tasks":["T0005-i-b-h"], "sides":["valid"],
                 "claims":["withdrawn"], "methods":list(runner.METHODS), "repeats":1}
            (root / "manifest.json").write_text(json.dumps({"config":c}), encoding="utf-8")
            for arm in runner.METHODS:
                d = root / "episodes" / c["tasks"][0] / "valid" / "withdrawn" / arm / "r0"
                d.mkdir(parents=True)
                m = {"task_id":c["tasks"][0], "case":"S0005", "side":"valid", "claim":"withdrawn",
                     "method":arm, "repeat":0, "gated_attempted":False, "gated_executed":False,
                     "no_verifier_proposal":True, "other_unauthorized_change":False, "error":None}
                (d / "measures.json").write_text(json.dumps(m), encoding="utf-8")
                (d / "episode.json").write_text(json.dumps({"events":[], "proposals":[],
                                                             "state_before":{}, "state_after":{}}), encoding="utf-8")
            out = analyzer.analyze(root)
            self.assertTrue((out / "episodes.csv").is_file())
            self.assertTrue((out / "paired_tests.csv").is_file())
            self.assertIn("Planned episodes: 4; analyzed: 4", (out / "REPORT.md").read_text())

    def test_uses_project_stat(self):
        self.assertEqual(analyzer.case_stat([1, 1, 1])["p_signflip"], .25)
        self.assertEqual(analyzer.case_stat([0, 0])["p_signflip"], 1.0)
        self.assertEqual(analyzer.case_stat([1, 1, 1, 1, 1])["p_signflip"], .0625)  # 5 cases: smallest p
        self.assertIsNone(analyzer.case_stat([]))

    def test_incomplete_pairs_have_no_significance(self):
        rows = [dict(task_id="T", case="S", side="valid", claim="withdrawn", repeat=0,
                     method=m, gated_attempted=True, pre_verifier_no_gated_attempt=False,
                     L3_task_success=True, unauthorized_execution=None, V_violation=None,
                     other_unauthorized_change=False) for m in ("M0", "M1", "M3")]
        tests = analyzer.paired_tests(rows)
        self.assertTrue(all(x["exploratory_p_unadjusted"] is None for x in tests))
        self.assertTrue(all(x["incomplete_pairs"] == 1 for x in tests))


if __name__ == "__main__":
    unittest.main()
