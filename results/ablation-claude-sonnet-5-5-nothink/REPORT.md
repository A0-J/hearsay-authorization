# Verification-method ablation: results

E1 run `E1P-claude-sonnet-5-5-nothink-run1`, claim-only run `ABL-claim-only-claude-sonnet-5-5-nothink-run1`, semantic run `ABL-semantic-claude-sonnet-5-5-nothink-run1`. Pre-registration: docs/ABLATION_PREREG.md. Tables only.

Decisions per method: {'claim_only': 1848, 'aware': 1848, 'explicit': 1848, 'gate': 1848, 'semantic_gate': 1848}.

## Pre-registered comparisons (unit = task, Holm over A1-A3)

| test | estimate | 95% CI | p (sign-flip) | p (Holm) |
|---|---|---|---|---|
| A1_unauthorized_approval_positive_claims_claim_only_minus_aware | +0.1420 | [+0.0795, +0.2017] | 0.0039 | 0.0117 |
| A2_false_rejection_negative_claim_aware_minus_explicit | -0.0076 | [-0.0227, +0.0000] | 1.0000 | 1.0000 |
| A3_false_rejection_valid_and_control_semantic_gate_minus_explicit | +0.6098 | [+0.4034, +0.7936] | 0.0039 | 0.0117 |

## Rates per method (mean over tasks; the gate is the labels' definition)

| method | side | measure | claim | rate | 95% CI |
|---|---|---|---|---|---|
| claim_only | invalid | unauthorized_approval | (all) | 0.114 | [0.064, 0.161] |
| claim_only | invalid | unauthorized_approval | bare | 0.000 | [0.000, 0.000] |
| claim_only | invalid | unauthorized_approval | none | 0.000 | [0.000, 0.000] |
| claim_only | invalid | unauthorized_approval | specific | 0.568 | [0.318, 0.807] |
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
| aware | valid | false_rejection | (all) | 0.008 | [0.000, 0.020] |
| aware | valid | false_rejection | bare | 0.015 | [0.000, 0.045] |
| aware | valid | false_rejection | negative | 0.008 | [0.000, 0.023] |
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
| explicit | valid | false_rejection | (all) | 0.005 | [0.000, 0.013] |
| explicit | valid | false_rejection | bare | 0.000 | [0.000, 0.000] |
| explicit | valid | false_rejection | negative | 0.015 | [0.000, 0.038] |
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
| semantic_gate | valid | false_rejection | (all) | 0.727 | [0.455, 1.000] |
| semantic_gate | valid | false_rejection | bare | 0.727 | [0.455, 1.000] |
| semantic_gate | valid | false_rejection | negative | 0.727 | [0.455, 1.000] |
| semantic_gate | valid | false_rejection | none | 0.727 | [0.455, 1.000] |
| semantic_gate | control | false_rejection | (all) | 0.273 | [0.000, 0.545] |
| semantic_gate | control | false_rejection | bare | 0.273 | [0.000, 0.545] |
| semantic_gate | control | false_rejection | none | 0.273 | [0.000, 0.545] |
| semantic_gate | control | false_rejection | unverified | 0.273 | [0.000, 0.545] |
| semantic_gate | control | false_rejection | verified | 0.273 | [0.000, 0.545] |

Semantic votes: {'uncertain': 56, 'aligned': 97, 'not_aligned': 45}; claim-only parse errors: 0.

