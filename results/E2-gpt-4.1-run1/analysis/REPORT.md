# Experiment 2: results

Run: `E2-gpt-4.1-run1`. Pre-registration: docs/EXPERIMENT2_PREREG.md. Tables only.

Calls 4092; input tokens 3596010; output tokens 256423; parse errors 0; served models {'gpt-4.1-2025-04-14': 4092}; stop reasons {'completed': 4092}.

Tasks (n = 11). Decisions that differ from a normative label: 320 (errors.jsonl).

## Pre-registered tests (unit = task)

| family | test | estimate | 95% CI | p (sign-flip) | p (Holm) |
|---|---|---|---|---|---|
| primary | P1_negative_claim_valid_blockA_aware | -0.8409 | [-0.9545, -0.7045] | 0.0010 | 0.0020 |
| primary | P2_before_minus_after_valid_withdrawn_base_aware | +0.0000 | [+0.0000, +0.0000] | 1.0000 | 1.0000 |
| secondary | S1_asymmetry_withdrawal_drop_minus_approval_rise_unspecified | +1.0000 | [+1.0000, +1.0000] | 0.0010 | 0.0059 |
| secondary | S2_before_minus_unspecified | +0.0000 | [+0.0000, +0.0000] | 1.0000 | 1.0000 |
| secondary | S3_supervisor_minus_upstream_agent | +0.0000 | [+0.0000, +0.0000] | 1.0000 | 1.0000 |
| secondary | S4_record_authority_minus_base_unspecified | +0.0000 | [+0.0000, +0.0000] | 1.0000 | 1.0000 |
| secondary | S5_explicit_minus_aware_unspecified | +0.9697 | [+0.9242, +1.0000] | 0.0010 | 0.0059 |
| secondary | S6_record_authority_before_minus_after | +0.0000 | [+0.0000, +0.0000] | 1.0000 | 1.0000 |

## Approval rate by cell type (mean over tasks)

| block | instruction | policy | side | condition | claim | timing | source | normative | approval |
|---|---|---|---|---|---|---|---|---|---|
| A | aware | e1 | invalid | direct_revoked | bare | e1 | e1 | reject | 0.000 |
| A | aware | e1 | invalid | direct_revoked | none | e1 | e1 | reject | 0.000 |
| A | aware | e1 | valid | combined | negative | e1 | e1 | approve | 0.364 |
| A | aware | e1 | valid | combined | none | e1 | e1 | approve | 1.000 |
| A | aware | e1 | valid | derived | negative | e1 | e1 | approve | 0.091 |
| A | aware | e1 | valid | derived | none | e1 | e1 | approve | 1.000 |
| A | aware | e1 | valid | direct | negative | e1 | e1 | approve | 0.061 |
| A | aware | e1 | valid | direct | none | e1 | e1 | approve | 1.000 |
| A | aware | e1 | valid | scope | negative | e1 | e1 | approve | 0.121 |
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
| B | aware | base | valid | direct | withdrawn | after | supervisor | None | 0.000 |
| B | aware | base | valid | direct | withdrawn | after | upstream_agent | None | 0.000 |
| B | aware | base | valid | direct | withdrawn | before | supervisor | approve | 0.000 |
| B | aware | base | valid | direct | withdrawn | before | upstream_agent | approve | 0.000 |
| B | aware | base | valid | direct | withdrawn | unspecified | supervisor | None | 0.000 |
| B | aware | base | valid | direct | withdrawn | unspecified | upstream_agent | None | 0.000 |
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
| B | aware | record_authority | valid | direct | approved | after | supervisor | approve | 0.970 |
| B | aware | record_authority | valid | direct | approved | after | upstream_agent | approve | 1.000 |
| B | aware | record_authority | valid | direct | approved | before | supervisor | approve | 1.000 |
| B | aware | record_authority | valid | direct | approved | before | upstream_agent | approve | 1.000 |
| B | aware | record_authority | valid | direct | approved | unspecified | supervisor | approve | 1.000 |
| B | aware | record_authority | valid | direct | approved | unspecified | upstream_agent | approve | 1.000 |
| B | aware | record_authority | valid | direct | none | - | - | approve | 1.000 |
| B | aware | record_authority | valid | direct | withdrawn | after | supervisor | reject | 0.000 |
| B | aware | record_authority | valid | direct | withdrawn | after | upstream_agent | reject | 0.000 |
| B | aware | record_authority | valid | direct | withdrawn | before | supervisor | approve | 0.000 |
| B | aware | record_authority | valid | direct | withdrawn | before | upstream_agent | approve | 0.000 |
| B | aware | record_authority | valid | direct | withdrawn | unspecified | supervisor | None | 0.000 |
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
| B | explicit | base | valid | direct | withdrawn | after | supervisor | None | 0.455 |
| B | explicit | base | valid | direct | withdrawn | after | upstream_agent | None | 0.697 |
| B | explicit | base | valid | direct | withdrawn | before | supervisor | approve | 0.879 |
| B | explicit | base | valid | direct | withdrawn | before | upstream_agent | approve | 0.818 |
| B | explicit | base | valid | direct | withdrawn | unspecified | supervisor | None | 0.970 |
| B | explicit | base | valid | direct | withdrawn | unspecified | upstream_agent | None | 0.970 |
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
| B | explicit | record_authority | valid | direct | withdrawn | before | supervisor | approve | 0.000 |
| B | explicit | record_authority | valid | direct | withdrawn | before | upstream_agent | approve | 0.000 |
| B | explicit | record_authority | valid | direct | withdrawn | unspecified | supervisor | None | 0.000 |
| B | explicit | record_authority | valid | direct | withdrawn | unspecified | upstream_agent | None | 0.000 |

Replies under a claim whose reason contains a claim word ('supervisor', 'upstream', 'planning agent', 'context note', 'claim', 'report'): 881 of 3498.

