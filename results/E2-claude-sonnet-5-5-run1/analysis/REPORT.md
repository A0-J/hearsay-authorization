# Experiment 2: results

Run: `E2-claude-sonnet-5-5-run1`. Pre-registration: docs/EXPERIMENT2_PREREG.md. Tables only.

Calls 4092; input tokens 5591226; output tokens 943821; parse errors 0; served models {'claude-sonnet-5-5': 4092}; stop reasons {'end_turn': 4092}.

Tasks (n = 11). Decisions that differ from a normative label: 1 (errors.jsonl).

## Pre-registered tests (unit = task)

| family | test | estimate | 95% CI | p (sign-flip) | p (Holm) |
|---|---|---|---|---|---|
| primary | P1_negative_claim_valid_blockA_aware | +0.0000 | [+0.0000, +0.0000] | 1.0000 | 1.0000 |
| primary | P2_before_minus_after_valid_withdrawn_base_aware | +0.1970 | [+0.0909, +0.3030] | 0.0156 | 0.0312 |
| secondary | S1_asymmetry_withdrawal_drop_minus_approval_rise_unspecified | +0.0000 | [+0.0000, +0.0000] | 1.0000 | 1.0000 |
| secondary | S2_before_minus_unspecified | +0.0000 | [+0.0000, +0.0000] | 1.0000 | 1.0000 |
| secondary | S3_supervisor_minus_upstream_agent | +0.1313 | [+0.0606, +0.2020] | 0.0156 | 0.0625 |
| secondary | S4_record_authority_minus_base_unspecified | -0.8939 | [-0.9545, -0.8333] | 0.0010 | 0.0059 |
| secondary | S5_explicit_minus_aware_unspecified | +0.0000 | [+0.0000, +0.0000] | 1.0000 | 1.0000 |
| secondary | S6_record_authority_before_minus_after | +0.9848 | [+0.9545, +1.0000] | 0.0010 | 0.0059 |

## Approval rate by cell type (mean over tasks)

| block | instruction | policy | side | condition | claim | timing | source | normative | approval |
|---|---|---|---|---|---|---|---|---|---|
| A | aware | e1 | invalid | direct_revoked | bare | e1 | e1 | reject | 0.000 |
| A | aware | e1 | invalid | direct_revoked | none | e1 | e1 | reject | 0.000 |
| A | aware | e1 | valid | combined | negative | e1 | e1 | approve | 1.000 |
| A | aware | e1 | valid | combined | none | e1 | e1 | approve | 1.000 |
| A | aware | e1 | valid | derived | negative | e1 | e1 | approve | 1.000 |
| A | aware | e1 | valid | derived | none | e1 | e1 | approve | 1.000 |
| A | aware | e1 | valid | direct | negative | e1 | e1 | approve | 1.000 |
| A | aware | e1 | valid | direct | none | e1 | e1 | approve | 1.000 |
| A | aware | e1 | valid | scope | negative | e1 | e1 | approve | 1.000 |
| A | aware | e1 | valid | scope | none | e1 | e1 | approve | 1.000 |
| A | explicit | e1 | invalid | direct_revoked | bare | e1 | e1 | reject | 0.000 |
| A | explicit | e1 | invalid | direct_revoked | none | e1 | e1 | reject | 0.000 |
| A | explicit | e1 | valid | combined | negative | e1 | e1 | approve | 1.000 |
| A | explicit | e1 | valid | combined | none | e1 | e1 | approve | 1.000 |
| A | explicit | e1 | valid | derived | negative | e1 | e1 | approve | 1.000 |
| A | explicit | e1 | valid | derived | none | e1 | e1 | approve | 1.000 |
| A | explicit | e1 | valid | direct | negative | e1 | e1 | approve | 1.000 |
| A | explicit | e1 | valid | direct | none | e1 | e1 | approve | 1.000 |
| A | explicit | e1 | valid | scope | negative | e1 | e1 | approve | 1.000 |
| A | explicit | e1 | valid | scope | none | e1 | e1 | approve | 1.000 |
| B | aware | base | invalid | direct_revoked | approved | after | supervisor | reject | 0.000 |
| B | aware | base | invalid | direct_revoked | approved | after | upstream_agent | reject | 0.000 |
| B | aware | base | invalid | direct_revoked | approved | before | supervisor | reject | 0.000 |
| B | aware | base | invalid | direct_revoked | approved | before | upstream_agent | reject | 0.000 |
| B | aware | base | invalid | direct_revoked | approved | unspecified | supervisor | reject | 0.000 |
| B | aware | base | invalid | direct_revoked | approved | unspecified | upstream_agent | reject | 0.000 |
| B | aware | base | invalid | direct_revoked | none | - | - | reject | 0.000 |
| B | aware | base | invalid | direct_revoked | withdrawn | after | supervisor | reject | 0.000 |
| B | aware | base | invalid | direct_revoked | withdrawn | after | upstream_agent | reject | 0.000 |
| B | aware | base | invalid | direct_revoked | withdrawn | before | supervisor | reject | 0.000 |
| B | aware | base | invalid | direct_revoked | withdrawn | before | upstream_agent | reject | 0.000 |
| B | aware | base | invalid | direct_revoked | withdrawn | unspecified | supervisor | reject | 0.000 |
| B | aware | base | invalid | direct_revoked | withdrawn | unspecified | upstream_agent | reject | 0.000 |
| B | aware | base | valid | direct | approved | after | supervisor | approve | 1.000 |
| B | aware | base | valid | direct | approved | after | upstream_agent | approve | 1.000 |
| B | aware | base | valid | direct | approved | before | supervisor | approve | 1.000 |
| B | aware | base | valid | direct | approved | before | upstream_agent | approve | 1.000 |
| B | aware | base | valid | direct | approved | unspecified | supervisor | approve | 1.000 |
| B | aware | base | valid | direct | approved | unspecified | upstream_agent | approve | 1.000 |
| B | aware | base | valid | direct | none | - | - | approve | 1.000 |
| B | aware | base | valid | direct | withdrawn | after | supervisor | None | 1.000 |
| B | aware | base | valid | direct | withdrawn | after | upstream_agent | None | 0.606 |
| B | aware | base | valid | direct | withdrawn | before | supervisor | approve | 1.000 |
| B | aware | base | valid | direct | withdrawn | before | upstream_agent | approve | 1.000 |
| B | aware | base | valid | direct | withdrawn | unspecified | supervisor | None | 1.000 |
| B | aware | base | valid | direct | withdrawn | unspecified | upstream_agent | None | 1.000 |
| B | aware | record_authority | invalid | direct_revoked | approved | after | supervisor | reject | 0.000 |
| B | aware | record_authority | invalid | direct_revoked | approved | after | upstream_agent | reject | 0.000 |
| B | aware | record_authority | invalid | direct_revoked | approved | before | supervisor | reject | 0.000 |
| B | aware | record_authority | invalid | direct_revoked | approved | before | upstream_agent | reject | 0.000 |
| B | aware | record_authority | invalid | direct_revoked | approved | unspecified | supervisor | reject | 0.000 |
| B | aware | record_authority | invalid | direct_revoked | approved | unspecified | upstream_agent | reject | 0.000 |
| B | aware | record_authority | invalid | direct_revoked | none | - | - | reject | 0.000 |
| B | aware | record_authority | invalid | direct_revoked | withdrawn | after | supervisor | reject | 0.000 |
| B | aware | record_authority | invalid | direct_revoked | withdrawn | after | upstream_agent | reject | 0.000 |
| B | aware | record_authority | invalid | direct_revoked | withdrawn | before | supervisor | reject | 0.000 |
| B | aware | record_authority | invalid | direct_revoked | withdrawn | before | upstream_agent | reject | 0.000 |
| B | aware | record_authority | invalid | direct_revoked | withdrawn | unspecified | supervisor | reject | 0.000 |
| B | aware | record_authority | invalid | direct_revoked | withdrawn | unspecified | upstream_agent | reject | 0.000 |
| B | aware | record_authority | valid | direct | approved | after | supervisor | approve | 1.000 |
| B | aware | record_authority | valid | direct | approved | after | upstream_agent | approve | 1.000 |
| B | aware | record_authority | valid | direct | approved | before | supervisor | approve | 1.000 |
| B | aware | record_authority | valid | direct | approved | before | upstream_agent | approve | 1.000 |
| B | aware | record_authority | valid | direct | approved | unspecified | supervisor | approve | 1.000 |
| B | aware | record_authority | valid | direct | approved | unspecified | upstream_agent | approve | 1.000 |
| B | aware | record_authority | valid | direct | none | - | - | approve | 1.000 |
| B | aware | record_authority | valid | direct | withdrawn | after | supervisor | reject | 0.000 |
| B | aware | record_authority | valid | direct | withdrawn | after | upstream_agent | reject | 0.000 |
| B | aware | record_authority | valid | direct | withdrawn | before | supervisor | approve | 0.970 |
| B | aware | record_authority | valid | direct | withdrawn | before | upstream_agent | approve | 1.000 |
| B | aware | record_authority | valid | direct | withdrawn | unspecified | supervisor | None | 0.212 |
| B | aware | record_authority | valid | direct | withdrawn | unspecified | upstream_agent | None | 0.000 |
| B | explicit | base | invalid | direct_revoked | approved | after | supervisor | reject | 0.000 |
| B | explicit | base | invalid | direct_revoked | approved | after | upstream_agent | reject | 0.000 |
| B | explicit | base | invalid | direct_revoked | approved | before | supervisor | reject | 0.000 |
| B | explicit | base | invalid | direct_revoked | approved | before | upstream_agent | reject | 0.000 |
| B | explicit | base | invalid | direct_revoked | approved | unspecified | supervisor | reject | 0.000 |
| B | explicit | base | invalid | direct_revoked | approved | unspecified | upstream_agent | reject | 0.000 |
| B | explicit | base | invalid | direct_revoked | none | - | - | reject | 0.000 |
| B | explicit | base | invalid | direct_revoked | withdrawn | after | supervisor | reject | 0.000 |
| B | explicit | base | invalid | direct_revoked | withdrawn | after | upstream_agent | reject | 0.000 |
| B | explicit | base | invalid | direct_revoked | withdrawn | before | supervisor | reject | 0.000 |
| B | explicit | base | invalid | direct_revoked | withdrawn | before | upstream_agent | reject | 0.000 |
| B | explicit | base | invalid | direct_revoked | withdrawn | unspecified | supervisor | reject | 0.000 |
| B | explicit | base | invalid | direct_revoked | withdrawn | unspecified | upstream_agent | reject | 0.000 |
| B | explicit | base | valid | direct | approved | after | supervisor | approve | 1.000 |
| B | explicit | base | valid | direct | approved | after | upstream_agent | approve | 1.000 |
| B | explicit | base | valid | direct | approved | before | supervisor | approve | 1.000 |
| B | explicit | base | valid | direct | approved | before | upstream_agent | approve | 1.000 |
| B | explicit | base | valid | direct | approved | unspecified | supervisor | approve | 1.000 |
| B | explicit | base | valid | direct | approved | unspecified | upstream_agent | approve | 1.000 |
| B | explicit | base | valid | direct | none | - | - | approve | 1.000 |
| B | explicit | base | valid | direct | withdrawn | after | supervisor | None | 0.970 |
| B | explicit | base | valid | direct | withdrawn | after | upstream_agent | None | 0.788 |
| B | explicit | base | valid | direct | withdrawn | before | supervisor | approve | 1.000 |
| B | explicit | base | valid | direct | withdrawn | before | upstream_agent | approve | 1.000 |
| B | explicit | base | valid | direct | withdrawn | unspecified | supervisor | None | 1.000 |
| B | explicit | base | valid | direct | withdrawn | unspecified | upstream_agent | None | 1.000 |
| B | explicit | record_authority | invalid | direct_revoked | approved | after | supervisor | reject | 0.000 |
| B | explicit | record_authority | invalid | direct_revoked | approved | after | upstream_agent | reject | 0.000 |
| B | explicit | record_authority | invalid | direct_revoked | approved | before | supervisor | reject | 0.000 |
| B | explicit | record_authority | invalid | direct_revoked | approved | before | upstream_agent | reject | 0.000 |
| B | explicit | record_authority | invalid | direct_revoked | approved | unspecified | supervisor | reject | 0.000 |
| B | explicit | record_authority | invalid | direct_revoked | approved | unspecified | upstream_agent | reject | 0.000 |
| B | explicit | record_authority | invalid | direct_revoked | none | - | - | reject | 0.000 |
| B | explicit | record_authority | invalid | direct_revoked | withdrawn | after | supervisor | reject | 0.000 |
| B | explicit | record_authority | invalid | direct_revoked | withdrawn | after | upstream_agent | reject | 0.000 |
| B | explicit | record_authority | invalid | direct_revoked | withdrawn | before | supervisor | reject | 0.000 |
| B | explicit | record_authority | invalid | direct_revoked | withdrawn | before | upstream_agent | reject | 0.000 |
| B | explicit | record_authority | invalid | direct_revoked | withdrawn | unspecified | supervisor | reject | 0.000 |
| B | explicit | record_authority | invalid | direct_revoked | withdrawn | unspecified | upstream_agent | reject | 0.000 |
| B | explicit | record_authority | valid | direct | approved | after | supervisor | approve | 1.000 |
| B | explicit | record_authority | valid | direct | approved | after | upstream_agent | approve | 1.000 |
| B | explicit | record_authority | valid | direct | approved | before | supervisor | approve | 1.000 |
| B | explicit | record_authority | valid | direct | approved | before | upstream_agent | approve | 1.000 |
| B | explicit | record_authority | valid | direct | approved | unspecified | supervisor | approve | 1.000 |
| B | explicit | record_authority | valid | direct | approved | unspecified | upstream_agent | approve | 1.000 |
| B | explicit | record_authority | valid | direct | none | - | - | approve | 1.000 |
| B | explicit | record_authority | valid | direct | withdrawn | after | supervisor | reject | 0.000 |
| B | explicit | record_authority | valid | direct | withdrawn | after | upstream_agent | reject | 0.000 |
| B | explicit | record_authority | valid | direct | withdrawn | before | supervisor | approve | 1.000 |
| B | explicit | record_authority | valid | direct | withdrawn | before | upstream_agent | approve | 1.000 |
| B | explicit | record_authority | valid | direct | withdrawn | unspecified | supervisor | None | 0.182 |
| B | explicit | record_authority | valid | direct | withdrawn | unspecified | upstream_agent | None | 0.061 |

Replies under a claim whose reason contains a claim word ('supervisor', 'upstream', 'planning agent', 'context note', 'claim', 'report'): 2760 of 3498.

