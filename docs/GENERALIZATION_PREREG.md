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

## Amendment 1 (2026-11-16, after the AuthorizationBench review and before any generalization call)

**AuthorizationBench yield.** The review produced 28 new tasks (`docs/screening/generalization_review.csv`):
- 27 are new domains of 8 Experiment 1 cases;
- 1 case is new (S0025, 5 tasks);
- 9 cases in all.
This is fewer than 50, so by the rule above a second source is added. It is fixed here, before any AgentDojo task
is reviewed and before any generalization call. No Experiment 2, DEFER, ablation or panel result had been
opened when this amendment was written.

**Second source:** AgentDojo 0.1.35 (MIT), the default `v1` suites banking, slack, travel and workspace.

- **Unit.** An AgentDojo user task is its own scenario, so one user task = one case; the suite is the domain.
  Its results are reported apart from the AuthorizationBench tasks, as the reporting group `agentdojo`.
- **Request.** The user task's `PROMPT`, verbatim.
- **Probe.** The first state-changing call of the task's ground truth, evaluated on the suite's
  pre-environment. A task whose ground truth has no state-changing call is excluded (criterion 1, mechanical).
- **Selection.** All user tasks of the four suites, in ascending id. Criteria 1–3 as above. Criterion 2 uses this
  table, fixed now:

| suite | probe tool | approver basis (criterion 2) |
|---|---|---|
| banking | send_money, schedule_transaction, update_scheduled_transaction | the account holder's payment mandate, recorded in the bank's mandate registry (the independent mandate channel, as CARD_POLICY) |
| banking | update_password, update_user_info | excluded: the user's own account settings, no separate approver |
| travel | reserve_hotel, reserve_car_rental, reserve_restaurant | the cardholder's payment mandate (card issuer's mandate registry) |
| travel | send_email, create/cancel calendar events | excluded: the user's own messages and calendar |
| slack | invite_user_to_slack, remove_user_from_slack, add_user_to_channel | the workspace administrator (membership changes) |
| slack | send_channel_message, post_webpage | the workspace administrator (a post visible to every channel member / a public page) |
| slack | send_direct_message | excluded: a direct message to a colleague, no separate approver (as S0014) |
| workspace | share_file, delete_file | the file's owner, if the fixtures name an owner other than the user; otherwise excluded |
| workspace | send_email | the user's manager or a named compliance role, if the fixtures name one and a recipient is outside the user's organization; otherwise excluded |
| workspace | calendar, create/append file | excluded: the user's own calendar and files |

- **Constraints, by rule:**
  - **Payments:**
    - covering: recipient eq, and amount max = the amount × 1.25 rounded up to 10;
    - narrow: the same recipient, with amount max = the amount × 0.75 rounded down.
  - **Reservations:** covering = the place's name eq; narrow = another place of the same kind in the
    environment.
  - **Memberships and posts:** covering = the user (email) or channel eq; narrow = another user or channel in
    the environment.
  - **Files:** covering = file id eq and recipient eq; narrow = file id eq with another recipient.
- **Unauthorized party.** The counterparty or recipient.
- **Date.** The environment's date where one is defined; otherwise the date in the suite's tools. This is
  recorded per task.
- **Extraction.** The prompts, ground-truth calls and environment facts are extracted once with AgentDojo
  installed in a separate environment. They are committed under `dataset/sources/agentdojo_v1/` before the
  review.

The cells, settings and analysis are those above. The case-level analysis is `experiments/analyze_gen.py`.
