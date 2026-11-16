# Verification-method ablation: results

E1 run `E1-gpt-4.1-run1`, claim-only run `ABL-claim-only-gpt-4.1-run1`, semantic run `ABL-semantic-gpt-4.1-run1`. Pre-registration: docs/ABLATION_PREREG.md. Tables only.

Decisions per method: {'claim_only': 1848, 'aware': 1848, 'explicit': 1848, 'gate': 1848, 'semantic_gate': 1848}.

## Pre-registered comparisons (unit = task, Holm over A1-A3)

| test | estimate | 95% CI | p (sign-flip) | p (Holm) |
|---|---|---|---|---|
| A1_unauthorized_approval_positive_claims_claim_only_minus_aware | +0.4015 | [+0.2850, +0.5246] | 0.0010 | 0.0029 |
| A2_false_rejection_negative_claim_aware_minus_explicit | +0.8258 | [+0.7197, +0.9318] | 0.0010 | 0.0029 |
| A3_false_rejection_valid_and_control_semantic_gate_minus_explicit | +0.7727 | [+0.5909, +0.9545] | 0.0010 | 0.0029 |

## Rates per method (mean over tasks; the gate is the labels' definition)

| method | side | measure | claim | rate | 95% CI |
|---|---|---|---|---|---|
| claim_only | invalid | unauthorized_approval | (all) | 0.327 | [0.234, 0.424] |
| claim_only | invalid | unauthorized_approval | bare | 0.182 | [0.000, 0.455] |
| claim_only | invalid | unauthorized_approval | none | 0.000 | [0.000, 0.000] |
| claim_only | invalid | unauthorized_approval | specific | 0.936 | [0.807, 1.000] |
| claim_only | invalid | unauthorized_approval | unverified | 0.000 | [0.000, 0.000] |
| claim_only | invalid | unauthorized_approval | verified | 0.515 | [0.242, 0.788] |
| claim_only | valid | false_rejection | (all) | 0.939 | [0.849, 1.000] |
| claim_only | valid | false_rejection | bare | 0.818 | [0.545, 1.000] |
| claim_only | valid | false_rejection | negative | 1.000 | [1.000, 1.000] |
| claim_only | valid | false_rejection | none | 1.000 | [1.000, 1.000] |
| claim_only | control | false_rejection | (all) | 0.000 | [0.000, 0.000] |
| claim_only | control | false_rejection | bare | 0.000 | [0.000, 0.000] |
| claim_only | control | false_rejection | none | 0.000 | [0.000, 0.000] |
| claim_only | control | false_rejection | unverified | 0.000 | [0.000, 0.000] |
| claim_only | control | false_rejection | verified | 0.000 | [0.000, 0.000] |
| aware | invalid | unauthorized_approval | (all) | 0.005 | [0.001, 0.011] |
| aware | invalid | unauthorized_approval | bare | 0.008 | [0.000, 0.019] |
| aware | invalid | unauthorized_approval | none | 0.000 | [0.000, 0.000] |
| aware | invalid | unauthorized_approval | specific | 0.015 | [0.000, 0.038] |
| aware | invalid | unauthorized_approval | unverified | 0.000 | [0.000, 0.000] |
| aware | invalid | unauthorized_approval | verified | 0.004 | [0.000, 0.011] |
| aware | valid | false_rejection | (all) | 0.275 | [0.240, 0.311] |
| aware | valid | false_rejection | bare | 0.000 | [0.000, 0.000] |
| aware | valid | false_rejection | negative | 0.826 | [0.720, 0.932] |
| aware | valid | false_rejection | none | 0.000 | [0.000, 0.000] |
| aware | control | false_rejection | (all) | 0.000 | [0.000, 0.000] |
| aware | control | false_rejection | bare | 0.000 | [0.000, 0.000] |
| aware | control | false_rejection | none | 0.000 | [0.000, 0.000] |
| aware | control | false_rejection | unverified | 0.000 | [0.000, 0.000] |
| aware | control | false_rejection | verified | 0.000 | [0.000, 0.000] |
| explicit | invalid | unauthorized_approval | (all) | 0.005 | [0.000, 0.012] |
| explicit | invalid | unauthorized_approval | bare | 0.004 | [0.000, 0.011] |
| explicit | invalid | unauthorized_approval | none | 0.011 | [0.000, 0.034] |
| explicit | invalid | unauthorized_approval | specific | 0.000 | [0.000, 0.000] |
| explicit | invalid | unauthorized_approval | unverified | 0.004 | [0.000, 0.011] |
| explicit | invalid | unauthorized_approval | verified | 0.008 | [0.000, 0.019] |
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
| semantic_gate | valid | false_rejection | (all) | 0.697 | [0.455, 0.939] |
| semantic_gate | valid | false_rejection | bare | 0.697 | [0.455, 0.939] |
| semantic_gate | valid | false_rejection | negative | 0.697 | [0.455, 0.939] |
| semantic_gate | valid | false_rejection | none | 0.697 | [0.455, 0.939] |
| semantic_gate | control | false_rejection | (all) | 1.000 | [1.000, 1.000] |
| semantic_gate | control | false_rejection | bare | 1.000 | [1.000, 1.000] |
| semantic_gate | control | false_rejection | none | 1.000 | [1.000, 1.000] |
| semantic_gate | control | false_rejection | unverified | 1.000 | [1.000, 1.000] |
| semantic_gate | control | false_rejection | verified | 1.000 | [1.000, 1.000] |

Semantic votes: {'aligned': 33, 'not_aligned': 96, 'uncertain': 69}; claim-only parse errors: 0.

