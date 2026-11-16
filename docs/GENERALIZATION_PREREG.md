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

## Amendment 2 (2026-11-17, after the extraction and before any AgentDojo task was reviewed)

1. **Extraction method.** Installing and running AgentDojo was not permitted in this environment. Instead, the
   downloaded wheel was read as data:
   - Python sources were parsed with `ast` and YAML with `yaml.safe_load`; no AgentDojo code was executed.
   - Arguments that depend on the environment were resolved against the extracted environment by a
     restricted evaluator.
   - The script is `experiments/extract_agentdojo.py`. The output, the wheel's SHA-256 and each input file's
     hash are in `dataset/sources/agentdojo_v1/manifest.json`.
   - The suites hold 97 user tasks, and 60 of them have a state-changing ground-truth call.
2. **Combined tasks are excluded.** These tasks (slack 17–20; workspace 4, 19, 23 and 36–39) join the prompts
   and ground truths of two other user tasks. They repeat their components' scenarios, so they are not new
   cases.
3. **Ground truth that contradicts the task.** A task is excluded under criterion 3 if its ground-truth probe
   call contradicts the task's own `utility` check on the probe's recipient or amount. In that case no single
   intended call is defined. The extraction flagged banking 5 and banking 11; the review checks every
   selected task.
4. **Message bodies.** Where the ground truth gives a placeholder body (`<summary>`, `...`), the probe uses
   Experiment 1's neutral placeholder rule.
5. **Date (`today`).** Each suite's own date where one exists: travel and workspace, 2024-05-15. Slack has no
   date and uses 2024-05-15 too. Banking has no date and uses 2022-03-08, the day after the latest past
   transaction in its environment (its scheduled transactions fall after it).
6. **Case ids.** `A` + suite + task number: Abank03, Aslack07, Atravel00, Awork25. One user task = one case.

## Amendment 3 (2026-11-17, before any Claude generalization call and before any AgentDojo call)

These decisions were made **after** seeing results: Experiments 1 and 2 and the ablation on the 11 tasks, and
part of the GPT-4.1 generalization runs (G1 6,330 of 9,744 calls; G2E 6,138 of 10,416; the AuthorizationBench
claim-only and semantic runs complete). Their reasons are the Claude budget (about $200 on the account used) and
the semantic diagnosis below, and they are reported as result-informed reductions, not as the original plan.

1. **Claude settings on the new tasks.** Only Claude Sonnet 5.5 adaptive runs, on:
   - Experiment 1's cells, for the AuthorizationBench and AgentDojo tasks;
   - the claim-only ablation, for both sources.
   Not run: the between_tools setting on any new task, and Experiment 2's cells on the AuthorizationBench
   tasks. Experiment 2's cells on the AgentDojo tasks for Claude adaptive are decided by the researcher
   **after** the Claude Experiment 1 results on the new tasks. If they run, that decision is recorded here
   as made after those results. The secondary tests for the Claude settings are computed only for what ran.
2. **Semantic arm on the new tasks.**
   - **Not run for Claude.**
   - **GPT-4.1's AgentDojo semantic run (360 calls) is not started.** Whether it runs is the researcher's
     decision, recorded here.
   - **The GPT-4.1 AuthorizationBench semantic run** (504 calls) finished before this diagnosis. It is kept
     and reported with it.
   **Reason.** The semantic decisions so far were classified by their stated reason, by keyword. This
   classification is exploratory. Among the gated call's non-aligned decisions:
   - "context missing or insufficient" was the stated reason in 35/66 (GPT-4.1, 11 tasks), 14/54 (Claude
     adaptive), 45/72 (Claude between_tools) and 106/184 (GPT-4.1, 28 new tasks). Arguments taken from the
     environment cannot be checked against trusted context "(none)". In T0008, for example, one carnet holds
     five tickets, but nothing in the input says so.
   - On the not-required control message, GPT-4.1 judged "not aligned" or "uncertain" in 99/99 and 238/252.
     Its reasons mostly say the message "does not fulfil the request".
   So the arm's false rejection mainly reflects this configuration (no task context, plus Experiment A's
   alignment question). Repeating it on new cases would measure the same configuration again.
3. **Reporting by lineage.**
   - **New AuthorizationBench tasks in Experiment 1's cases** are new domains of an existing source scenario.
     They are reported as such and not counted as independent source cases.
   - **Independent new source cases:** 1 AuthorizationBench case (S0025) and 20 AgentDojo user tasks.
   - **AgentDojo tasks that share a probe call** are flagged in every report: slack 2, 11 and 16 (invite Dora);
     slack 9 and 10 (add Alice to External_0).
4. **AgentDojo ground-truth audit.** Before any AgentDojo call, an independent read-only audit checks each
   selected task's request, call, approver, unauthorized party and covering/narrow constraints against the
   extracted source. Its findings, and any task they change, are recorded here before the AgentDojo runs.
