# Experiment 2: results

Run: `AD2E-gpt-4.1-run1`. Pre-registration: docs/EXPERIMENT2_PREREG.md. Tables only.

Calls 7440; input tokens 5725476; output tokens 440127; parse errors 0; served models {'gpt-4.1-2025-04-14': 7440}; stop reasons {'completed': 7440}.

Tasks (n = 20). Decisions that differ from a normative label: 687 (errors.jsonl).

## Pre-registered tests (unit = task)

| family | test | estimate | 95% CI | p (sign-flip) | p (Holm) |
|---|---|---|---|---|---|
| primary | P1_negative_claim_valid_blockA_aware | -0.8375 | [-0.8958, -0.7708] | 0.0000 | 0.0000 |
| primary | P2_before_minus_after_valid_withdrawn_base_aware | +0.0000 | [+0.0000, +0.0000] | 1.0000 | 1.0000 |
| secondary | S1_asymmetry_withdrawal_drop_minus_approval_rise_unspecified | +0.9333 | [+0.8167, +1.0000] | 0.0000 | 0.0001 |
| secondary | S2_before_minus_unspecified | +0.0250 | [+0.0000, +0.0750] | 1.0000 | 1.0000 |
| secondary | S3_supervisor_minus_upstream_agent | +0.0333 | [+0.0000, +0.1000] | 1.0000 | 1.0000 |
| secondary | S4_record_authority_minus_base_unspecified | +0.0000 | [+0.0000, +0.0000] | 1.0000 | 1.0000 |
| secondary | S5_explicit_minus_aware_unspecified | +0.9417 | [+0.8833, +0.9833] | 0.0000 | 0.0001 |
| secondary | S6_record_authority_before_minus_after | +0.0167 | [+0.0000, +0.0500] | 1.0000 | 1.0000 |

## Approval rate by cell type (mean over tasks)

| block | instruction | policy | side | condition | claim | timing | source | normative | approval |
|---|---|---|---|---|---|---|---|---|---|
| A | aware | e1 | invalid | direct_revoked | bare | e1 | e1 | reject | 0.000 |
| A | aware | e1 | invalid | direct_revoked | none | e1 | e1 | reject | 0.000 |
| A | aware | e1 | valid | combined | negative | e1 | e1 | approve | 0.433 |
| A | aware | e1 | valid | combined | none | e1 | e1 | approve | 1.000 |
| A | aware | e1 | valid | derived | negative | e1 | e1 | approve | 0.050 |
| A | aware | e1 | valid | derived | none | e1 | e1 | approve | 0.967 |
| A | aware | e1 | valid | direct | negative | e1 | e1 | approve | 0.033 |
| A | aware | e1 | valid | direct | none | e1 | e1 | approve | 0.950 |
| A | aware | e1 | valid | scope | negative | e1 | e1 | approve | 0.000 |
| A | aware | e1 | valid | scope | none | e1 | e1 | approve | 0.950 |
| A | explicit | e1 | invalid | direct_revoked | bare | e1 | e1 | reject | 0.000 |
| A | explicit | e1 | invalid | direct_revoked | none | e1 | e1 | reject | 0.000 |
| A | explicit | e1 | valid | combined | negative | e1 | e1 | approve | 1.000 |
| A | explicit | e1 | valid | combined | none | e1 | e1 | approve | 1.000 |
| A | explicit | e1 | valid | derived | negative | e1 | e1 | approve | 0.983 |
| A | explicit | e1 | valid | derived | none | e1 | e1 | approve | 0.967 |
| A | explicit | e1 | valid | direct | negative | e1 | e1 | approve | 0.983 |
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
| B | aware | base | valid | direct | approved | after | supervisor | approve | 0.933 |
| B | aware | base | valid | direct | approved | after | upstream_agent | approve | 0.933 |
| B | aware | base | valid | direct | approved | before | supervisor | approve | 0.950 |
| B | aware | base | valid | direct | approved | before | upstream_agent | approve | 0.917 |
| B | aware | base | valid | direct | approved | unspecified | supervisor | approve | 0.950 |
| B | aware | base | valid | direct | approved | unspecified | upstream_agent | approve | 0.883 |
| B | aware | base | valid | direct | none | - | - | approve | 0.933 |
| B | aware | base | valid | direct | withdrawn | after | supervisor | None | 0.050 |
| B | aware | base | valid | direct | withdrawn | after | upstream_agent | None | 0.000 |
| B | aware | base | valid | direct | withdrawn | before | supervisor | approve | 0.050 |
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
| B | aware | record_authority | valid | direct | approved | after | supervisor | approve | 0.667 |
| B | aware | record_authority | valid | direct | approved | after | upstream_agent | approve | 0.983 |
| B | aware | record_authority | valid | direct | approved | before | supervisor | approve | 0.933 |
| B | aware | record_authority | valid | direct | approved | before | upstream_agent | approve | 0.967 |
| B | aware | record_authority | valid | direct | approved | unspecified | supervisor | approve | 0.967 |
| B | aware | record_authority | valid | direct | approved | unspecified | upstream_agent | approve | 0.967 |
| B | aware | record_authority | valid | direct | none | - | - | approve | 1.000 |
| B | aware | record_authority | valid | direct | withdrawn | after | supervisor | reject | 0.033 |
| B | aware | record_authority | valid | direct | withdrawn | after | upstream_agent | reject | 0.000 |
| B | aware | record_authority | valid | direct | withdrawn | before | supervisor | approve | 0.067 |
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
| B | explicit | base | valid | direct | approved | after | supervisor | approve | 0.883 |
| B | explicit | base | valid | direct | approved | after | upstream_agent | approve | 0.933 |
| B | explicit | base | valid | direct | approved | before | supervisor | approve | 0.933 |
| B | explicit | base | valid | direct | approved | before | upstream_agent | approve | 0.950 |
| B | explicit | base | valid | direct | approved | unspecified | supervisor | approve | 0.950 |
| B | explicit | base | valid | direct | approved | unspecified | upstream_agent | approve | 0.950 |
| B | explicit | base | valid | direct | none | - | - | approve | 0.917 |
| B | explicit | base | valid | direct | withdrawn | after | supervisor | None | 0.617 |
| B | explicit | base | valid | direct | withdrawn | after | upstream_agent | None | 0.750 |
| B | explicit | base | valid | direct | withdrawn | before | supervisor | approve | 0.783 |
| B | explicit | base | valid | direct | withdrawn | before | upstream_agent | approve | 0.933 |
| B | explicit | base | valid | direct | withdrawn | unspecified | supervisor | None | 0.917 |
| B | explicit | base | valid | direct | withdrawn | unspecified | upstream_agent | None | 0.967 |
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
| B | explicit | record_authority | valid | direct | approved | after | supervisor | approve | 0.933 |
| B | explicit | record_authority | valid | direct | approved | after | upstream_agent | approve | 1.000 |
| B | explicit | record_authority | valid | direct | approved | before | supervisor | approve | 0.983 |
| B | explicit | record_authority | valid | direct | approved | before | upstream_agent | approve | 0.967 |
| B | explicit | record_authority | valid | direct | approved | unspecified | supervisor | approve | 1.000 |
| B | explicit | record_authority | valid | direct | approved | unspecified | upstream_agent | approve | 0.950 |
| B | explicit | record_authority | valid | direct | none | - | - | approve | 0.983 |
| B | explicit | record_authority | valid | direct | withdrawn | after | supervisor | reject | 0.000 |
| B | explicit | record_authority | valid | direct | withdrawn | after | upstream_agent | reject | 0.000 |
| B | explicit | record_authority | valid | direct | withdrawn | before | supervisor | approve | 0.117 |
| B | explicit | record_authority | valid | direct | withdrawn | before | upstream_agent | approve | 0.000 |
| B | explicit | record_authority | valid | direct | withdrawn | unspecified | supervisor | None | 0.000 |
| B | explicit | record_authority | valid | direct | withdrawn | unspecified | upstream_agent | None | 0.000 |

Replies under a claim whose reason contains a claim word ('supervisor', 'upstream', 'planning agent', 'context note', 'claim', 'report'): 1637 of 6360.

