# Experiment 1 dataset (v1.0.0-exp1)

Verifier-only test items for Experiment 1 run 1. The conditions, selection rule, hypotheses and analysis
were pre-registered in `docs/EXPERIMENT1_PREREG.md` (commit `e5fb9fd`) before this dataset was built.
This dataset is separate from the pilot dataset (`dataset/tasks/`, v0.2.0-pilot), which is unchanged.

## Contents

| file | content | who reads it |
|---|---|---|
| `manifest.json` | version, pre-registration commit, AuthorizationBench commit, task list, counts, hashes | documentation |
| `instructions.json` | the three verifier instructions used (texts and SHA-256) | the runner |
| `tasks/<id>/spec.json` | the original request, the intent-aligned call, the control call, the policy, the approver and the unauthorized issuer, the covering and narrow constraints, and how the call was built | documentation |
| `tasks/<id>/cells.jsonl` | every cell's full verifier input (116 per task) | the runner |
| `tasks/<id>/labels.jsonl` | the expected decision and the deterministic gate's verdict per cell | analysis only |

## Items

There are 11 tasks from 11 independent AuthorizationBench source cases. They were chosen by the
pre-registered review of all 40 candidate cases (`docs/screening/seed_review.md`). The pilot's cases
S0007 and S0010 are excluded.

- Task types: payment 5, external communication 3, external disclosure 1, broadcast disclosure 1,
  personal-data sharing 1.
- Each task has one intent-aligned call (the action the principal asked for). Its arguments come from
  the original fixtures by rule; `spec.json/construction` records how.
- Where a message body had to be written (S0016, S0028, S0032, S0041), it is a neutral placeholder. It
  makes no claim beyond the request, because the experiment is about authorization, not content.

## Cells

Per task and instruction (evidence-aware, evidence-explicit):

| side | evidence conditions | claims |
|---|---|---|
| invalid (correct decision: reject) | abs_list, abs_complete, direct_revoked, direct_expired, derived_revoked, derived_expired, scope, combined | none, unverified, bare, verified, specific |
| valid (correct decision: approve) | direct, derived, scope, combined | none, bare, negative |
| control: `message_user`, no approval needed (correct decision: approve) | not_required | none, unverified, bare, verified |

Each task also has four cells in the pilot's exact format. They cover abs_list and direct_revoked, each
with no claim and with a specific claim.

- **Claim texts.** The unverified, bare and verified notes are the *Silence Is Endorsement* Appendix C
  templates, verbatim. Notes are placed before the request.
- **Evidence.** Within a task, the evidence never depends on the claim (tested). The policy is identical
  in every cell of a task.

The definitions of every condition are in the pre-registration.

## Rebuild and check

```bash
python experiments/build_exp1.py               # needs the pinned AuthorizationBench checkout
python -m pytest tests/test_exp1.py            # gate verdicts, claim invariance, texts, no labels in inputs
```
