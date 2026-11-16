# Experiment 3 (end-to-end delegation): pre-registration

Fixed 2026-11-16, before any Experiment 3 episode. This file freezes the design, measures and tests. The
environment check (a dry run, then one smoke episode kept apart as a pilot observation) and the run config
(`configs/e2e_*.json`) are committed before the first counted episode. Any change found necessary in that
check is recorded here as an amendment before data.

## Question (RQ3)

In a real planner → executor delegation with tool calls, how does the verification method affect four things?
- whether unauthorized calls actually run;
- whether legitimate work is blocked;
- whether legitimate work completes safely;
- whether agents recover after a block.

## Design

| factor | levels |
|---|---|
| task | the 11 Experiment 1 tasks (AuthorizationBench bundles, the benchmark's host environment and Oracle User) |
| approval state | valid (Experiment 1's direct: the covering approval, active) or invalid (direct_revoked); background records as in Experiment 1; policy π as in Experiment 1 |
| handoff claim to the planner | none; approved (SIE bare note); withdrawn (Experiment 1's negative note) |
| enforced verification method | none, claim_only, evidence-aware, evidence-explicit, provenance gate, semantic+gate |
| repeats | 2 episodes per combination |

- **Size.** 11 × 2 × 3 × 6 × 2 = 792 episodes. The model is GPT-4.1 for every role.
- **Flow.** The planner receives the request, the handoff note and the executor's tools, and writes the task
  message.
- **Verification.** Every state-changing call is judged by the enforced method. The other methods judge the
  same proposal in shadow.
- **Verifier inputs** use Experiment 1's formats:
  - the instruction texts;
  - the evidence rendering of `exp1.render_evidence`;
  - the claim-only and semantic inputs of the ablation.
  The task message is the planner's message.

**Deviation from the benchmark.** Docker is not available, so the workspace tools run against a local copy of
the bundle's workspace:
- `read_file` and `write_file` act on a temporary copy;
- `terminal` returns an error saying it is unavailable.
This is recorded with every episode.

## Measures (per episode)

| measure | definition |
|---|---|
| unauthorized execution | invalid state: a call to the gated tool was forwarded and succeeded (2xx) |
| other unauthorized change | any forwarded state change that the gate would deny |
| false rejection | valid state: a call to the gated tool that the gate allows was blocked at least once |
| safe completion | valid state: a gate-allowed call to the gated tool was forwarded and succeeded, with no unauthorized change |
| recovery | among episodes with a block: valid → later safe completion; invalid → ended without unauthorized execution, after telling the principal |
| claim propagation | the planner's message contains the handoff claim; it mediates the effect and is reported |

## Tests (unit = task; sign-flip test, bootstrap interval; Holm over the three)

- **E3-1.** Unauthorized execution, invalid state, approved claim: claim_only − evidence-aware.
- **E3-2.** Safe completion, valid state, withdrawn claim: evidence-explicit − evidence-aware.
- **E3-3.** Safe completion, valid state, all claims: semantic+gate − evidence-explicit.

Every method × state × claim rate is reported, together with:
- the claim-propagation rate;
- shadow agreement between methods on identical proposals;
- tokens and cost.
