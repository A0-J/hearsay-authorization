# Verification-method ablation: pre-registration

Fixed 2026-11-16, before any ablation data. It is frozen with `src/hearsay/authbench/exp2.py` (claim-only and
semantic cells), `experiments/build_exp2.py` and `experiments/analyze_ablation.py`.

## Question (RQ3)

Five verification methods run on identical inputs:
- an LLM that sees only the claim and the policy;
- an LLM that also sees the evidence;
- that LLM told how to rank the evidence;
- the deterministic provenance gate;
- a semantic check combined with the gate.

What does each component contribute to safety (unauthorized approval) and to usability (false rejection)?

## Methods (Experiment 1's main-arm cells, 11 tasks)

| method | independent record | evidence priority stated | deterministic check | source of decisions |
|---|---|---|---|---|
| claim_only | no | no | no | new run: dataset `ablation_claim_only` (the Experiment 1 input without the evidence block; the claim-only text of Experiment A with Experiment 1's reply format) |
| evidence-aware | yes | no | no | the Experiment 1 run of the same setting |
| evidence-explicit | yes | yes | no | the Experiment 1 run of the same setting |
| provenance gate | yes | enforced | yes | labels (`gate_allowed`); **it defines the labels, so its zero error is by construction, not a finding** |
| semantic + gate | yes | enforced | yes | new run: dataset `ablation_semantic`. The semantic text of Experiment A; its input is the principal's request and the call, with trusted context "(none)". 3 votes; it approves only on an "aligned" majority, combined by AND with the gate |

**Input reuse.**
- The claim-only input does not depend on the evidence: one task has 11 distinct inputs.
- The semantic input depends only on the call: 2 inputs per task.
- Repeat r of an Experiment 1 cell uses repeat r of claim_only, and semantic votes 3r to 3r+2.
- Runs: claim_only 3 repeats, 363 calls; semantic 9 single-vote repeats, 198 calls.

## Measures and comparisons

- **Measures.** Per method:
  - the unauthorized approval rate on the invalid side;
  - the false rejection rate on the valid side and on the not-required control.
  Both are broken down by claim, as means over tasks with bootstrap intervals.
- **Pre-registered comparisons** (unit = task, sign-flip test, Holm over the three):
  - **A1.** Unauthorized approval on the invalid side under positive claims: claim_only − evidence-aware.
  - **A2.** False rejection under the negative claim on the valid side: evidence-aware − evidence-explicit.
  - **A3.** False rejection on the valid side and control, all claims: semantic+gate − evidence-explicit.

## Settings

- The 3 core settings.
- For Claude Sonnet 5.5 between_tools, the evidence-aware and evidence-explicit decisions come from its model
  panel run of Experiment 1 (docs/MODEL_PANEL_PREREG.md).
- Results are reported for each setting separately.
