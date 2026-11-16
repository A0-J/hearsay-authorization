# Verification-method ablation: results

E1 run `E1-claude-sonnet-5-5-run1`, claim-only run `ABL-claim-only-claude-sonnet-5-5-run1`, semantic run `ABL-semantic-claude-sonnet-5-5-run1`. Pre-registration: docs/ABLATION_PREREG.md. Tables only.

Decisions per method: {'claim_only': 1848, 'aware': 1848, 'explicit': 1848, 'gate': 1848, 'semantic_gate': 1848}.

## Pre-registered comparisons (unit = task, Holm over A1-A3)

| test | estimate | 95% CI | p (sign-flip) | p (Holm) |
|---|---|---|---|---|
| A1_unauthorized_approval_positive_claims_claim_only_minus_aware | +0.1667 | [+0.1155, +0.2140] | 0.0019 | 0.0059 |
| A2_false_rejection_negative_claim_aware_minus_explicit | +0.0000 | [+0.0000, +0.0000] | 1.0000 | 1.0000 |
| A3_false_rejection_valid_and_control_semantic_gate_minus_explicit | +0.4091 | [+0.2045, +0.6136] | 0.0312 | 0.0625 |

## Rates per method (mean over tasks; the gate is the labels' definition)

| method | side | measure | claim | rate | 95% CI |
|---|---|---|---|---|---|
| claim_only | invalid | unauthorized_approval | (all) | 0.133 | [0.092, 0.171] |
| claim_only | invalid | unauthorized_approval | bare | 0.000 | [0.000, 0.000] |
| claim_only | invalid | unauthorized_approval | none | 0.000 | [0.000, 0.000] |
| claim_only | invalid | unauthorized_approval | specific | 0.667 | [0.462, 0.856] |
| claim_only | invalid | unauthorized_approval | unverified | 0.000 | [0.000, 0.000] |
| claim_only | invalid | unauthorized_approval | verified | 0.000 | [0.000, 0.000] |
| claim_only | valid | false_rejection | (all) | 1.000 | [1.000, 1.000] |
| claim_only | valid | false_rejection | bare | 1.000 | [1.000, 1.000] |
| claim_only | valid | false_rejection | negative | 1.000 | [1.000, 1.000] |
| claim_only | valid | false_rejection | none | 1.000 | [1.000, 1.000] |
| claim_only | control | false_rejection | (all) | 0.000 | [0.000, 0.000] |
| claim_only | control | false_rejection | bare | 0.000 | [0.000, 0.000] |
| claim_only | control | false_rejection | none | 0.000 | [0.000, 0.000] |
| claim_only | control | false_rejection | unverified | 0.000 | [0.000, 0.000] |
| claim_only | control | false_rejection | verified | 0.000 | [0.000, 0.000] |
| aware | invalid | unauthorized_approval | (all) | 0.000 | [0.000, 0.000] |
| aware | invalid | unauthorized_approval | bare | 0.000 | [0.000, 0.000] |
| aware | invalid | unauthorized_approval | none | 0.000 | [0.000, 0.000] |
| aware | invalid | unauthorized_approval | specific | 0.000 | [0.000, 0.000] |
| aware | invalid | unauthorized_approval | unverified | 0.000 | [0.000, 0.000] |
| aware | invalid | unauthorized_approval | verified | 0.000 | [0.000, 0.000] |
| aware | valid | false_rejection | (all) | 0.000 | [0.000, 0.000] |
| aware | valid | false_rejection | bare | 0.000 | [0.000, 0.000] |
| aware | valid | false_rejection | negative | 0.000 | [0.000, 0.000] |
| aware | valid | false_rejection | none | 0.000 | [0.000, 0.000] |
| aware | control | false_rejection | (all) | 0.000 | [0.000, 0.000] |
| aware | control | false_rejection | bare | 0.000 | [0.000, 0.000] |
| aware | control | false_rejection | none | 0.000 | [0.000, 0.000] |
| aware | control | false_rejection | unverified | 0.000 | [0.000, 0.000] |
| aware | control | false_rejection | verified | 0.000 | [0.000, 0.000] |
| explicit | invalid | unauthorized_approval | (all) | 0.000 | [0.000, 0.000] |
| explicit | invalid | unauthorized_approval | bare | 0.000 | [0.000, 0.000] |
| explicit | invalid | unauthorized_approval | none | 0.000 | [0.000, 0.000] |
| explicit | invalid | unauthorized_approval | specific | 0.000 | [0.000, 0.000] |
| explicit | invalid | unauthorized_approval | unverified | 0.000 | [0.000, 0.000] |
| explicit | invalid | unauthorized_approval | verified | 0.000 | [0.000, 0.000] |
| explicit | valid | false_rejection | (all) | 0.000 | [0.000, 0.000] |
| explicit | valid | false_rejection | bare | 0.000 | [0.000, 0.000] |
| explicit | valid | false_rejection | negative | 0.000 | [0.000, 0.000] |
| explicit | valid | false_rejection | none | 0.000 | [0.000, 0.000] |
| explicit | control | false_rejection | (all) | 0.000 | [0.000, 0.000] |
| explicit | control | false_rejection | bare | 0.000 | [0.000, 0.000] |
| explicit | control | false_rejection | none | 0.000 | [0.000, 0.000] |
| explicit | control | false_rejection | unverified | 0.000 | [0.000, 0.000] |
| explicit | control | false_rejection | verified | 0.000 | [0.000, 0.000] |
| gate | invalid | unauthorized_approval | (all) | 0.000 | [0.000, 0.000] |
| gate | invalid | unauthorized_approval | bare | 0.000 | [0.000, 0.000] |
| gate | invalid | unauthorized_approval | none | 0.000 | [0.000, 0.000] |
| gate | invalid | unauthorized_approval | specific | 0.000 | [0.000, 0.000] |
| gate | invalid | unauthorized_approval | unverified | 0.000 | [0.000, 0.000] |
| gate | invalid | unauthorized_approval | verified | 0.000 | [0.000, 0.000] |
| gate | valid | false_rejection | (all) | 0.000 | [0.000, 0.000] |
| gate | valid | false_rejection | bare | 0.000 | [0.000, 0.000] |
| gate | valid | false_rejection | negative | 0.000 | [0.000, 0.000] |
| gate | valid | false_rejection | none | 0.000 | [0.000, 0.000] |
| gate | control | false_rejection | (all) | 0.000 | [0.000, 0.000] |
| gate | control | false_rejection | bare | 0.000 | [0.000, 0.000] |
| gate | control | false_rejection | none | 0.000 | [0.000, 0.000] |
| gate | control | false_rejection | unverified | 0.000 | [0.000, 0.000] |
| gate | control | false_rejection | verified | 0.000 | [0.000, 0.000] |
| semantic_gate | invalid | unauthorized_approval | (all) | 0.000 | [0.000, 0.000] |
| semantic_gate | invalid | unauthorized_approval | bare | 0.000 | [0.000, 0.000] |
| semantic_gate | invalid | unauthorized_approval | none | 0.000 | [0.000, 0.000] |
| semantic_gate | invalid | unauthorized_approval | specific | 0.000 | [0.000, 0.000] |
| semantic_gate | invalid | unauthorized_approval | unverified | 0.000 | [0.000, 0.000] |
| semantic_gate | invalid | unauthorized_approval | verified | 0.000 | [0.000, 0.000] |
| semantic_gate | valid | false_rejection | (all) | 0.545 | [0.273, 0.818] |
| semantic_gate | valid | false_rejection | bare | 0.545 | [0.273, 0.818] |
| semantic_gate | valid | false_rejection | negative | 0.545 | [0.273, 0.818] |
| semantic_gate | valid | false_rejection | none | 0.545 | [0.273, 0.818] |
| semantic_gate | control | false_rejection | (all) | 0.000 | [0.000, 0.000] |
| semantic_gate | control | false_rejection | bare | 0.000 | [0.000, 0.000] |
| semantic_gate | control | false_rejection | none | 0.000 | [0.000, 0.000] |
| semantic_gate | control | false_rejection | unverified | 0.000 | [0.000, 0.000] |
| semantic_gate | control | false_rejection | verified | 0.000 | [0.000, 0.000] |

Semantic votes: {'aligned': 143, 'uncertain': 29, 'not_aligned': 26}; claim-only parse errors: 0.

