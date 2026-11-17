# Hearsay Is Not Authorization

In a multi-agent delegation, an upstream agent tells a downstream agent that an action is authorized, or
that its approval was withdrawn. An LLM verifier then decides whether the action may run. This project
measures whether such **unverified claims change the verifier's decision even when the verifier also sees
the independent approval records** (the policy and the approval system's state).

Status: 2026-11-18. The research is in progress and experiments are paused while the next step is planned.
Start here: **[results/synthesis/REPORT.md](results/synthesis/REPORT.md)** has the risk map, the comparisons, the
figures and representative cases in one place. For writing up, **[results/synthesis/EVIDENCE_MAP.md](results/synthesis/EVIDENCE_MAP.md)**
links each finding to its tests, numbers, limits, figures and sources.
Full index of experiments, runs and outputs: **[docs/EXPERIMENTS.md](docs/EXPERIMENTS.md)**.

## Main findings so far

All values are differences in approval rate (percentage points), with 95% bootstrap intervals over tasks or
cases. Details and tests are in each run's `analysis/REPORT.md`.

| finding | evidence | status |
|---|---|---|
| **A withdrawal claim overrides valid records.** "The approval was withdrawn" lowers approval of calls that valid, complete records authorize. | 11 tasks, evidence-aware: GPT-4.1 −82.6 [−93.2, −72.0]; gpt-4o −75.0; gpt-4.1-mini −60.6; Claude Sonnet 4.6 −47.0; gpt-5.5, Claude Haiku 5.5 and Claude Sonnet 5.5 (thinking on or off) ≈ 0 | secondary in Experiment 1 (H5); confirmed as a primary test in Experiment 2 (P1), which re-samples the same inputs |
| It replicates on new tasks (GPT-4.1) | AuthorizationBench new tasks −79.3 [−88.2, −67.5] (8 cases: 7 are new domains of Experiment 1 cases, 1 is a new case); AgentDojo −85.5 [−92.5, −77.6] (19 independent cases) | pre-registered primary (G1) |
| **Asymmetry.** Generic approval claims do not move invalid evidence; a named approval ID can. | positive claims on invalid evidence: +0.7 (11 tasks), +0.7 (AB new), +1.9 [+1.1, +2.6] (AgentDojo); in AgentDojo all of it comes from the specific-ID claim (+7.5), the generic claims are 0 (post-hoc split); asymmetry S1 +93 to +100 | H1–H3 (Experiment 1 primary) not supported; G2 (generalization primary) not supported on AB new, supported on AgentDojo (Holm p = 0.0003) |
| Mechanism (GPT-4.1, three task sets) | not claim timing (P2 = 0), not source authority (S3 ≈ 0), not fixed by a policy rule (S4 = 0); removed by an evidence-priority instruction (S5 +95 to +97). Caveat (post hoc): 23–41% of the refusals misread 09:00 as after the 10:00 snapshot, so the timing manipulation is weak | Experiment 2, pre-registered reading rules |
| The instruction fix depends on the model | evidence-explicit leaves −32.6 (gpt-4.1-mini) and −34.1 (Claude Sonnet 4.6; −10.6 if self-corrected replies are read by their last decision) | model panel; parser sensitivity in results/synthesis/ |
| A policy rule undoes the instruction fix (post hoc) | with the record_authority rule, evidence-explicit approval of a valid call whose claimed withdrawal predates the snapshot falls from 85–88% to 0–6% (GPT-4.1, three sets); Claude Sonnet 5.5 without thinking: 100% → 0–8% by the first decision of each reply, 30–45% by the last; not with thinking | results/synthesis/ |
| End-to-end, partial: the withdrawal claim stops work before any verifier sees a call | Experiment 3 (paused, 5 tasks): with the withdrawal note no episode attempts the gated call (0/94); without a claim 81/106 do. The planner relays the claim with an instruction not to proceed; planner and executor were not separated | descriptive; results/synthesis/ |
| With a DEFER option (GPT-4.1) | a withdrawal claim → 100% defer, 0% reject; a 5.5-hour-old snapshot without a claim → 100% approve (normative: defer) | exploratory, descriptive |
| Forged approval IDs (exploratory, post hoc) | an approval id named in the task message but absent from the records is accepted in 29 of 57 calls (51%) against a complete lookup that found nothing (GPT-4.1, AgentDojo, 19 primary cases; 29/60 with Abank00 in results/invalid-approvals/) and recorded as the decision basis | results/invalid-approvals/, results/synthesis/ |

Not established yet:
- whether the effect generalizes to independent tasks for models other than GPT-4.1;
- end-to-end harm (Experiment 3 is paused at 301 of 792 episodes; see the design audit);
- the error-cause coding, which is model-assisted and still awaits the human check;
- the mitigation experiment, which is a draft pre-registration with no runs;
- where in the agent the withdrawal claim stops work, and whether a planner-side check restores it: a planner ×
  verifier 2×2 is coded but not run, for after the thesis
  ([docs/PLANNER_VERIFIER_2X2_PREREG_DRAFT.md](docs/PLANNER_VERIFIER_2X2_PREREG_DRAFT.md); its planner advisory
  is an oracle, and separating planner and executor needs a further experiment);
- how to read Claude replies that state a decision and then correct it: the frozen parser takes the first
  decision; no GPT result depends on this (results/synthesis/, Section 9);
- a gate that enforces freshness: the provenance gate checks record validity only, so it allows the stale and
  re-check cells of Experiment 2 and the DEFER arm (results/synthesis/, Section 10).

## Where to look

| what | where |
|---|---|
| Synthesis: risks, comparisons, figures, cases | [results/synthesis/REPORT.md](results/synthesis/REPORT.md) (`experiments/synthesis.py`) |
| Evidence map: each finding → tests, numbers, limits, figures, sources | [results/synthesis/EVIDENCE_MAP.md](results/synthesis/EVIDENCE_MAP.md) (`experiments/evidence_map.py`; every recorded test in `tables/prereg_tests.csv`) |
| Experiment index (IDs, runs, status, outputs) | [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md) |
| Pre-registrations (frozen before data; amendments appended) | `docs/*_PREREG.md` (listed in the index) |
| Related work and how this study differs | [docs/RELATED_WORK.md](docs/RELATED_WORK.md) |
| Figures (PNG) | `results/E1-figures/png/`, `results/E2-figures/png/`, `results/generalization-figures/png/` |
| Per-run analysis | `results/<run-id>/analysis/REPORT.md`, `tests.json` |
| Cross-run analyses | `results/ablation-*/`, `results/error-stages/`, `results/invalid-approvals/`, `results/h3-completeness/`, `results/E3-checks/`, `results/m-design/` |
| Raw results (not in git) | `archives/` zips, with SHA-256 in [results/registry.json](results/registry.json) |
| Provenance: code version, launch logs, pre-registration timing | [results/provenance/](results/provenance/README.md) |
| Datasets (frozen cells and labels) | [dataset/](dataset/README.md): `exp1`, `exp2`, `exp2_defer`, `ablation_*`, `*_gen` (new AuthorizationBench tasks), `*_ad` (AgentDojo) |
| Code | `src/hearsay/authbench/` (cells, evidence rendering, verifiers, gate, E2E runtime); `experiments/` (build, run, analyze, figures) |

## How to run

```bash
pip install -e .[dev,authbench]
python experiments/fetch_authbench.py            # AuthorizationBench at the pinned commit
python -m pytest                                 # 0 API calls
# Windows: set PYTHONUTF8=1

# verifier-only experiments (Experiments 1 and 2, panel, generalization, ablation): one config per run
python experiments/run_exp1.py --config configs/exp1_gpt41.json --plan      # counts and token estimate
python experiments/run_exp1.py --config configs/exp1_gpt41.json --dry-run   # fake client, 0 calls
python experiments/run_exp1.py --config configs/exp1_gpt41.json             # real calls; resumable, pause-safe

# analysis (no API calls)
python experiments/analyze_exp1.py results/E1-gpt-4.1-run1        # Experiment 1 and panel cells
python experiments/analyze_exp2.py results/E2-gpt-4.1-run1        # Experiment 2 (and DEFER mode)
python experiments/analyze_gen.py  results/G1-gpt-4.1-run1        # generalization, case level
python experiments/analyze_ablation.py --help                     # verification-method ablation
python experiments/figures_exp1.py ; python experiments/figures_exp2.py ; python experiments/figures_gen.py

# raw results stay out of git
python experiments/archive_run.py results/<run-id> --label "..."   # zip + SHA-256 into results/registry.json
```

API keys are read from `openai_api_key.txt` and `anthropic_api_key.txt` (both gitignored) or from the
environment.

A run pauses instead of failing:
- on a quota, billing or authentication error;
- on a `STOP` file in its directory;
- at `--stop-after N`.

It then writes `PAUSED.json`, and rerunning the same command resumes it.

## Working rules

- Pre-register before data. Changes go in dated amendments, never as silent edits.
- Never pool models, settings or task sets. The unit of analysis is the task or case, never the call.
- Report every result, including nulls and paused runs. A post-hoc result is labelled as post hoc.
- The provenance gate defines the Experiment 1 labels, so its zero error there is by construction and is not a
  finding. It checks record validity only, not the freshness rule of Experiment 2 and the DEFER arm.
- `semantic_provenance_direct` is a simplified variant of DualFlow, not DualFlow itself.

## Earlier stages

These are kept for the record and are not the current main line:
- the first mock-service sandbox (`src/hearsay/scenarios.py`, `experiments/run.py`; 64 scenarios);
- Experiment A, the pilot verifier-only run (`configs/experiment_a*.json`, `results/A-*`; 891 calls).

Their design is in [PLAN.md](PLAN.md) and [docs/RESEARCH_PROGRAM.md](docs/RESEARCH_PROGRAM.md).
