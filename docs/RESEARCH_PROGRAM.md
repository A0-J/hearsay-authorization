# Research program after Experiment 1: questions, experiments and run matrix

Fixed 2026-11-16, after Experiment 1 run 1 (GPT-4.1 and the Claude Sonnet 5.5 replication) and before any data
of the experiments below. Each experiment has its own pre-registration file; the commit that adds a file freezes
that experiment. Results of different experiments, models, settings or task sets are reported separately and
never pooled. This file is a planning document, not paper text.

## Where we start

- Experiment 1 (11 tasks, GPT-4.1): the primary hypotheses H1–H3 (positive claims raise approval on invalid
  evidence) were not supported.
- The secondary hypothesis H5 (a withdrawal claim lowers approval on valid evidence) showed −82.6 points under
  evidence-aware and 0 under evidence-explicit.
- The Claude Sonnet 5.5 replication made 0 errors in 3,828 calls; its run used the model's default (adaptive)
  thinking.
- **Status of H5.** It was pre-registered as a secondary hypothesis. Making it the focus of the follow-up work
  was decided after the results, so it is a post-hoc selected effect. Two follow-ups test it:
  - re-testing it on the same 11 tasks (Experiment 2, block A) gives new samples, not independent items;
  - its confirmatory test is on new tasks (the generalization experiment).

## Research questions

| RQ | question | experiments |
|---|---|---|
| RQ1, phenomenon | Given independent authorization evidence, does an upstream claim change a verifier's decision? Is the change specific to a model, a reasoning setting or a task set? | Experiment 1, model panel, generalization |
| RQ2, cause | What drives the change: uncertainty about how recent the evidence is, trust in the claim's source, or the verifier's guidance (policy, instruction)? Is it deference to claims or conservative refusal? | Experiment 2 (blocks A and B), DEFER arm |
| RQ3, response | Which verification path keeps unauthorized execution low *and* legitimate task completion high? | Ablation, E2E (Experiment 3) |

## Thesis mapping (planning only)

| chapter | content | figures and tables |
|---|---|---|
| Problem definition | threat model; Claim Non-Amplification; the verifier's inputs (π, σ, claim) | definitions, a diagram |
| Dataset and system | AuthorizationBench cases, task selection, evidence conditions, runtime gate | dataset tables, the selection log |
| RQ1 | Experiment 1, model panel, generalization | Fig. 1 (approval by evidence form), Fig. 2 (per task), Table (per model) |
| RQ2 | Experiment 2, DEFER | timing × source × policy × instruction tables, contrast plots |
| RQ3 | ablation, E2E | Table (method × unauthorized/false rejection), E2E outcome table |
| Cost and limits | tokens and cost per run; verifier-only vs E2E; task reuse | cost table |

## Experiments and run matrix

Repeats are independent single calls per cell (3, unless stated). "Setting" means a model plus its request
options. The three core settings are:
- GPT-4.1 (temperature 1, top_p 1);
- Claude Sonnet 5.5 with no thinking field ("adaptive", the model default);
- Claude Sonnet 5.5 with `thinking: {"type": "between_tools"}` ("no thinking before the reply").

| experiment | pre-registration | items | cells | settings | calls per setting |
|---|---|---|---|---|---|
| Model panel (Experiment 1 replications) | MODEL_PANEL_PREREG.md | 11 E1 tasks | 1,276 (frozen) | 6 further settings | 3,828 |
| Experiment 2 (mechanism) | EXPERIMENT2_PREREG.md | 11 E1 tasks | 1,364 | 3 core | 4,092 |
| DEFER arm (exploratory) | EXPERIMENT2_DEFER_PREREG.md | 11 E1 tasks | 352 | 3 core | 1,056 |
| Ablation (claim-only, semantic) | ABLATION_PREREG.md | 11 E1 tasks | 121 + 22 | 3 core | 363 + 198 |
| Generalization | GENERALIZATION_PREREG.md | new tasks (≤ 24) | E1 + E2 + ablation cells | 3 core | 3 × (116 + 124) × n + ablation |
| E2E (Experiment 3) | EXPERIMENT3_E2E_PREREG.md | 11 E1 tasks | episodes | GPT-4.1 | see file |

## Order of execution

1. Model panel, Experiment 2, DEFER and ablation on the 11 tasks. These are built and tested, and they run in
   parallel. Within Experiment 2, DEFER and the ablation, GPT-4.1 runs first and Claude after. Both are fixed
   here, so Claude's conditions cannot change after the GPT-4.1 results.
2. Generalization: review and construct the tasks under the frozen rule, record the review, then run.
3. E2E: validate the environment (dry run, then one smoke episode kept apart as a pilot observation), then
   run.

Every run records:
- the raw reply and the parsed decision;
- parse errors, the input SHA-256 and the instruction SHA-256;
- the served model, the stop reason, usage and latency;
- the config and the git commit.

Raw replies are archived out of git, with hashes in `results/registry.json`. No condition, item or test is
changed after its data; anything added later is labelled exploratory.
