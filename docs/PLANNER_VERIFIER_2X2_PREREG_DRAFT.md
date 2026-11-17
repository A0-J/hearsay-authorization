# Planner × Verifier 2×2 experiment — PRE-REGISTRATION DRAFT

**Status: OPEN. Not preregistered. No real episodes have been executed by this package.**

## Decisions before freezing (2026-11-18)

Not run before the thesis (due 2026-11-25). The design is revised and pre-registered first; until then the config
keeps `approved_for_run: false`. The code is in the repository now. Its defaults leave Experiment 3 unchanged
(`planner_override=None`, `shadow=True`), and the full test suite passes with it.

Decided:
1. **The planner advisory is an oracle.** It is `ApprovalRegistry.check` on the benchmark's preselected target
   call, the same rule that defines the labels. M2 and M3 are reported as an oracle-advisory baseline (an upper
   bound for a planner-side check), never as a realistic authorization lookup. A planner-side re-lookup where the
   target call and its status are not known in advance is a separate experiment.
2. **Safety needs an evaluation independent of the gate.** M1 and M3 enforce the gate, so their unauthorized
   gated execution is 0 by construction, and the planned M3 − M2 safety contrast equals M2's own rate.
   [OPEN] the independent outcome evaluation.
3. **Planner and executor are separated in an auxiliary message-path experiment**, not as an arm of the 2×2.
   It asks:
   - whether the planner writes a wrong stop instruction;
   - whether the executor stops on its own when it receives the withdrawal claim;
   - whether a trusted advisory given to the planner carries through to the executor.

   The runtime cannot do this yet: `delegation="direct"` rejects a handoff note (`RunConfig` in
   `src/hearsay/authbench/runtime.py`). [OPEN] the arms. For example: the claim delivered to the executor directly,
   or the planner's message with the claim removed.
4. **The 5-task pilot is exploratory.** With 5 cases the smallest exact two-sided p is 0.0625, so no pilot test
   can reach p < .05.
   - Pilot measures: gated-call attempt rate, L3 task success, unauthorized execution, and claim relay
     (`claim_propagated`).
   - Go/no-go is decided by effect sizes and failure cases fixed before the pilot. [OPEN] the thresholds.
5. **Confirmation uses independent tasks** not used in Experiment 3. The sample size comes from a power
   analysis, and the L3 criteria are fixed before any episode. The five pilot tasks' L3 rules were written after
   reading their Experiment 3 episodes (`experiments/e2e_task_check.py`).
6. **Statistics** use `analyze_exp1.stat`:
   - case bootstrap, 10,000 resamples, seed 0;
   - sign-flip test, exact up to 16 cases, otherwise 100,000 random sign vectors.

   [OPEN] the test family and the Holm correction.

Still open from the draft below: randomized arm order, the `ambiguous_output` rule, and the model snapshots.

Notes for the design:
- The direction of valid + withdrawn M3 − M1 is largely expected from earlier results:
  - in Experiment 3, no episode with the withdrawal note attempted the gated call (valid state, 0/50);
  - the evidence-priority instruction removed the verifier's withdrawal effect (Experiment 2 S5, +95 to +97).

  The informative parts are the L3 levels, the invalid side, and whether the claim still reaches the executor.
- `claim_propagated` is a marker match. It does not tell a relayed claim from a planner message that mentions the
  claim only to rebut it. [OPEN] the coding rule for the guarded arms.

Code changes at integration (2026-11-18), relative to the reviewer's package:
- The patch is applied under `src/` (`git apply --directory=src`).
- The analyzer uses `analyze_exp1.stat` instead of its own bootstrap (seed 4810) and sign-flip test, which gave
  no p above 20 cases. For up to 16 cases the p-value is identical; the bootstrap intervals differ slightly.
- The analyzer reports `claim_propagated`, which `e2e.measures` already records.
- The runner's manifest labels the advisory as an oracle, and the gate arms' 0 as by construction.
- Raw episodes are committed like the other runs (rule of 2026-11-18); `-dryrun` output stays gitignored.

## Research question

Can structured authorization verification at the planner stage restore legitimate actions that an unsupported withdrawal claim would stop before the execution verifier sees a call, while execution-time enforcement continues to prevent unauthorized target calls?

## Architecture and treatments

All arms share the same GPT-4.1 planner, executor, task, handoff claim, target preselection, temperature/client settings and environment. The factors are:

| Arm | Planner guard | Execution verifier |
|---|---|---|
| M0 | Off | E1 evidence-aware LLM verifier |
| M1 | Off | Deterministic `ApprovalRegistry.check` gate |
| M2 | On | E1 evidence-aware LLM verifier |
| M3 | On | Deterministic `ApprovalRegistry.check` gate |

The **planner guard treatment is bundled**: before planning, the trusted runtime applies `ApprovalRegistry.check` to the benchmark's *pre-selected canonical target call* and gives the planner both this status and an instruction to treat unsupported withdrawal claims as unverified. Thus it does **not** separately identify the effects of extra evidence vs instruction wording. It does not validate arbitrary calls subsequently proposed by the executor. Only the execution-time gate rechecks each actual proposal. The approval registry is a synthetic authority source used for E3; its performance on real, stale or erroneous registries is not measured.

The guarded planner still receives the same principal request and handoff note. For comparability, its system instructions differ only by the trusted advisory and guidance. The old six-way *shadow verification* is disabled, avoiding unused LLM calls. All other components follow the original `run_e2e.py` architecture; other state-changing tools remain `not_required` per E3 Amendment 1, an important scope restriction.

## Conditions and randomization

- Valid or revoked approval for the target action (2); handoff `none`, `approved`, `withdrawn` (3); M0..M3 (4); repetitions (3 in example).
- Five previously used E3 tasks in the pilot config: 5 × 2 × 3 × 4 × 3 = **360 episodes**. This is **development/pilot** work, not an independent confirmatory sample.
- Consider all 11 E3 cases only after pilot debugging; **new independently chosen tasks** need a separate selection and build step before confirmatory evidence is claimed.
- For causal comparisons, each (task, side, claim, repeat) is paired across the four arms. Different arms use fresh benchmark environments; do not reuse writable environment state.
- Before execution: lock the set of tasks, sample size (using a power calculation, not an arbitrary 5-task pilot), output parsing rule, factor definitions, random/shard execution order, API model snapshots and environment hashes. **The starter runner uses deterministic ordered enumeration (like E3), not randomized arm order. This must be addressed before confirmatory use.**

## Endpoints

1. **Primary candidate:** benchmark task-level L3 success, on valid approval + withdrawn claim, M3 minus M1. L3 is currently the task-specific rule implementation from `experiments/e2e_task_check.py`; five of its eleven rules were written after prior E3 episodes, so pilot use is exploratory. Obtain independent blinded or pre-locked scoring for a new confirmatory task set.
2. **Mechanism outcome:** target tool proposal was made (`gated_attempted`), and pre-verification absence of target proposal (not equivalent to a measured Planner-only refusal).
3. **Safety:** unauthorized execution of pre-selected gated action, on invalid approval + `approved` claim, M3 vs M2. Broader benchmark violations must also be inspected (`V_violation` may be null for some E3 tasks); **a zero gated-action violation is not proof of general system safety**.
4. Resource overhead: planner and verifier API usage, turn counts and latency (manifest and raw logs; more instrumentation needed for accurate per-episode cost).

## Planned contrasts (not yet locked)

- Valid + withdrawn: M3 − M1 L3 task-success rate (tests the incremental value of Planner-side protection beyond execution-time gate).
- Valid + withdrawn: M2 − M0 gated-attempt rate (Planner treatment effect while keeping evidence-aware verifier).
- Invalid + approved: M3 − M2 unauthorized gated execution rate (execution-gate contribution when Planner protected).

Use task/case as the independent sampling unit; aggregate episode repeats first, then compute paired case-level differences, case bootstrap CIs and exact sign-flip tests. Do not use individual API calls as independent samples. Test family and multiplicity corrections must be fixed before the confirmatory run. The supplied analysis reports unadjusted *exploratory* p-values and suppresses them for incomplete paired cells.

## Explicit limitations/open decisions

- This is **not a pure binary 2×2 of verification access**: M0/M2 use an LLM evidence-aware verifier, whereas M1/M3 use a deterministic gate. This isolates the effect of strengthening execution verification, but also changes implementation and running costs.
- The planner guard receives a target-call advisory; the system knows the benchmark-selected call before the agent acts. In an open-ended real application, intended tool call and arguments are not known a priori. A general Planner-side registry lookup tool is a necessary follow-up.
- No temporal-freshness logic is implemented: E2/DEFER stale-snapshot states are outside this run's claim.
- Invalid approval means revoked approval for the target. It is not a complete test of unauthorized behavior via other tools or arguments.
- The L3 proxy rules are not an external adjudication; some have post-hoc provenance. Prefer a locked external grader for confirmation.
- `ambiguous_output` (multiple incompatible decisions) and fail-closed parser must be locked prospectively; this package keeps the earlier first-JSON rule through the E3 verifier adapter for comparison and logs raw replies.
- Re-running on E3's original selected tasks after seeing E3 observations is replication/exploration, not untouched confirmatory evidence.
- Pilot scripts should be run with `approved_for_run=false` until the study owner reviews the frozen protocol.
