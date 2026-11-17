# Hearsay Is Not Authorization

In a multi-agent delegation, an upstream agent tells a downstream agent that an action is authorized, or
that its approval was withdrawn. An LLM verifier then decides whether the action may run. This project
measures whether such **unverified claims change the verifier's decision even when the verifier also sees
the independent approval records** (the policy and the approval system's state).

Status: 2026-11-17. The research is in progress and experiments are paused while the next step is planned.
Full index of experiments, runs and outputs: **[docs/EXPERIMENTS.md](docs/EXPERIMENTS.md)**.

## Main findings so far

All values are differences in approval rate (percentage points), with 95% bootstrap intervals over tasks or
cases. Details and tests are in each run's `analysis/REPORT.md`.

| finding | evidence | status |
|---|---|---|
| **A withdrawal claim overrides valid records.** "The approval was withdrawn" lowers approval of calls that valid, complete records authorize. | 11 tasks, evidence-aware: GPT-4.1 −82.6 [−93.2, −72.0]; gpt-4o −75.0; gpt-4.1-mini −60.6; Claude Sonnet 4.6 −47.0; gpt-5.5, Claude Haiku 5.5 and Claude Sonnet 5.5 (thinking on or off) ≈ 0 | secondary in Experiment 1 (H5); confirmed as a primary test in Experiment 2 (P1) |
| It replicates on independent tasks (GPT-4.1) | AuthorizationBench new tasks −79.3 [−88.2, −67.5] (8 cases); AgentDojo −85.5 [−92.5, −77.6] (19 cases) | pre-registered primary (G1) |
| **Asymmetry.** Approval claims barely move invalid evidence. | positive claims on invalid evidence: +0.7 (11 tasks), +0.7 (AB new), +1.9 (AgentDojo); asymmetry S1 +93 to +100 | H1–H3 (Experiment 1 primary) not supported |
| Mechanism (GPT-4.1, three task sets) | not claim timing (P2 = 0), not source authority (S3 ≈ 0), not fixed by a policy rule (S4 = 0); removed by an evidence-priority instruction (S5 +95 to +97) | Experiment 2, pre-registered reading rules |
| The instruction fix depends on the model | evidence-explicit leaves −32.6 (gpt-4.1-mini) and −34.1 (Claude Sonnet 4.6) | model panel |
| With a DEFER option (GPT-4.1) | a withdrawal claim → 100% defer, 0% reject; a 5.5-hour-old snapshot without a claim → 100% approve (normative: defer) | exploratory, descriptive |
| Forged approval IDs (exploratory, post hoc) | an approval id named in the task message but absent from the records is accepted up to 48% (GPT-4.1, AgentDojo) and recorded as the decision basis | results/invalid-approvals/ |

Not established yet:
- whether the effect generalizes to independent tasks for models other than GPT-4.1;
- end-to-end harm (Experiment 3 is paused at 301 of 792 episodes; see the design audit);
- the error-cause coding, which is model-assisted and still awaits the human check;
- the mitigation experiment, which is a draft pre-registration with no runs.

## Where to look

| what | where |
|---|---|
| Experiment index (IDs, runs, status, outputs) | [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md) |
| Pre-registrations (frozen before data; amendments appended) | `docs/*_PREREG.md` (listed in the index) |
| Related work and how this study differs | [docs/RELATED_WORK.md](docs/RELATED_WORK.md) |
| Figures (PNG) | `results/E1-figures/png/`, `results/E2-figures/png/`, `results/generalization-figures/png/` |
| Per-run analysis | `results/<run-id>/analysis/REPORT.md`, `tests.json` |
| Cross-run analyses | `results/ablation-*/`, `results/error-stages/`, `results/invalid-approvals/`, `results/h3-completeness/`, `results/E3-checks/`, `results/m-design/` |
| Raw results (not in git) | `archives/` zips, with SHA-256 in [results/registry.json](results/registry.json) |
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
- The provenance gate defines the labels, so its zero error is by construction and is not a finding.
- `semantic_provenance_direct` is a simplified variant of DualFlow, not DualFlow itself.

## Earlier stages

These are kept for the record and are not the current main line:
- the first mock-service sandbox (`src/hearsay/scenarios.py`, `experiments/run.py`; 64 scenarios);
- Experiment A, the pilot verifier-only run (`configs/experiment_a*.json`, `results/A-*`; 891 calls).

Their design is in [PLAN.md](PLAN.md) and [docs/RESEARCH_PROGRAM.md](docs/RESEARCH_PROGRAM.md).
