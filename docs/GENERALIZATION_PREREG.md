# Generalization to new tasks: pre-registration

Fixed 2026-11-16, before any task in it was reviewed and before any call. The commit that adds this file and
`docs/screening/generalization_candidates.csv` freezes the selection rule and the analysis.

## Why

Experiment 1 made 3,828 calls per model, but the calls come from only 11 independent tasks: the cells vary
the claim, the evidence and the instruction on the same tasks. The withdrawal-claim effect was singled out
after run 1 (docs/RESEARCH_PROGRAM.md), so its confirmatory test needs new items.
- This experiment adds every eligible AuthorizationBench task it can.
- A paraphrase or a repeat of the same task does not count as a new case.
- No task is chosen or dropped because of a model's result, and no label is changed to make a task harder.

## Selection rule

- **Pool.** AuthorizationBench at the pinned commit. Two exclusions:
  - `-n` tasks: 81 of the 91 `-n` tasks that have an `-h` twin use the same request and environment.
  - the 11 Experiment 1 tasks and the 5 pilot tasks.
- **Unit of diversity.** A (case, domain) pair. Tasks of the same case in the same domain share the scenario
  and environment. At most one task per pair is selected: the first task, in ascending task id, that passes.
  A pair already represented by an Experiment 1 or pilot task is excluded.
- **Stage 0 (mechanical, already applied).** A task is excluded if its request is find/suggest-only (criterion
  1) or it has no state-changing tool (criterion 3). The result:
  `docs/screening/generalization_candidates.csv` lists 169 rows, of which 112 tasks in 74 pairs from 23 cases
  are to review.
- **Stages 1–2.** Experiment 1's criteria 1–3 (docs/EXPERIMENT1_PREREG.md), applied to each task:
  1. The request asks for the state-changing action.
  2. An approval by someone other than the requester is plausible, with a recorded basis: an organizational
     role in the fixtures, a counterparty, or an independent mandate channel for the principal's own
     payments.
  3. The requested call is a business tool call with concrete arguments taken from the fixtures, and its
     scope is expressible in the record's constraint language.
- **Review log.** Every reviewed task gets its decision and a one-line reason in
  `docs/screening/generalization_review.csv`, committed before any generalization call.
- **Construction.** As in Experiment 1 (`exp1.E1Task`): arguments by rule from the fixtures, and a neutral
  placeholder wherever a message body has to be written. The build refuses any cell whose gate verdict differs
  from its side.
- **Second source.** If AuthorizationBench yields fewer than 50 new tasks, a second source may be added. It is
  fixed in an amendment to this file before any generalization call. Its tasks are reported apart from the
  AuthorizationBench tasks.

## Cells and settings

- Each new task gets three cell sets: Experiment 1's cells (116 per task), Experiment 2's cells (124 per task)
  and the ablation cells. All are built by the same code as for the 11 tasks.
- The 3 core settings: GPT-4.1, Claude Sonnet 5.5 adaptive, Claude Sonnet 5.5 between_tools.
- 3 repeats.

## Hypotheses

Primary family (Holm). GPT-4.1, evidence-aware, new tasks only:
- **G1, confirmatory test of the post-hoc-selected effect.** The negative claim lowers approval on valid
  evidence. This is Experiment 1's H5 contrast.
- **G2.** Positive claims raise approval on invalid evidence. This is Experiment 1's H1 contrast.

Secondary:
- every other Experiment 1 test (H2–H8, Amendment 1);
- Experiment 2's P1, P2 and S1–S6;
- all computed on the new tasks;
- the same tests for the Claude settings.

## Analysis

- **Independence unit = case.** A case's value is the mean of its tasks' per-task contrasts.
  - The estimate is the mean over cases.
  - The interval is a bootstrap over cases (10,000 resamples, seed 0).
  - The p-value is a sign-flip test over cases: exact for up to 16 cases, otherwise 100,000 random sign
    vectors (seed 0).
- **Task unit.** The same quantities over tasks are reported as secondary.
- **Separate reporting.** Results are reported apart for:
  - the 11 Experiment 1 tasks;
  - new tasks in Experiment 1's cases (new domains);
  - new tasks in new cases;
  - any second source.
  They are never pooled with Experiment 1's tasks.
- **Errors.** Every cell's rate and every error is reported.
