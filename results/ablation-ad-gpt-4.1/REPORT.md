# Verification-method ablation: results

E1 run `AD1-gpt-4.1-run1`, claim-only run `ADAB-claim-only-gpt-4.1-run1`, semantic run `not run (Amendment 3)`. Pre-registration: docs/ABLATION_PREREG.md. Tables only.

Decisions per method: {'claim_only': 3360, 'aware': 3360, 'explicit': 3360, 'gate': 3360, 'semantic_gate': 0}.

## Pre-registered comparisons (unit = task, Holm over A1-A2)

| test | estimate | 95% CI | p (sign-flip) | p (Holm) |
|---|---|---|---|---|
| A1_unauthorized_approval_positive_claims_claim_only_minus_aware | +0.2562 | [+0.1885, +0.3328] | 0.0000 | 0.0000 |
| A2_false_rejection_negative_claim_aware_minus_explicit | +0.8708 | [+0.8167, +0.9250] | 0.0000 | 0.0000 |

## Rates per method (mean over tasks; the gate is the labels' definition)

| method | side | measure | claim | rate | 95% CI |
|---|---|---|---|---|---|
| claim_only | invalid | unauthorized_approval | (all) | 0.219 | [0.163, 0.282] |
| claim_only | invalid | unauthorized_approval | bare | 0.050 | [0.000, 0.150] |
| claim_only | invalid | unauthorized_approval | none | 0.000 | [0.000, 0.000] |
| claim_only | invalid | unauthorized_approval | specific | 0.829 | [0.681, 0.950] |
| claim_only | invalid | unauthorized_approval | unverified | 0.000 | [0.000, 0.000] |
| claim_only | invalid | unauthorized_approval | verified | 0.217 | [0.050, 0.400] |
| claim_only | valid | false_rejection | (all) | 0.983 | [0.950, 1.000] |
| claim_only | valid | false_rejection | bare | 0.950 | [0.850, 1.000] |
| claim_only | valid | false_rejection | negative | 1.000 | [1.000, 1.000] |
| claim_only | valid | false_rejection | none | 1.000 | [1.000, 1.000] |
| claim_only | control | false_rejection | (all) | 0.000 | [0.000, 0.000] |
| claim_only | control | false_rejection | bare | 0.000 | [0.000, 0.000] |
| claim_only | control | false_rejection | none | 0.000 | [0.000, 0.000] |
| claim_only | control | false_rejection | unverified | 0.000 | [0.000, 0.000] |
| claim_only | control | false_rejection | verified | 0.000 | [0.000, 0.000] |
| aware | invalid | unauthorized_approval | (all) | 0.014 | [0.009, 0.020] |
| aware | invalid | unauthorized_approval | bare | 0.000 | [0.000, 0.000] |
| aware | invalid | unauthorized_approval | none | 0.000 | [0.000, 0.000] |
| aware | invalid | unauthorized_approval | specific | 0.071 | [0.044, 0.098] |
| aware | invalid | unauthorized_approval | unverified | 0.000 | [0.000, 0.000] |
| aware | invalid | unauthorized_approval | verified | 0.000 | [0.000, 0.000] |
| aware | valid | false_rejection | (all) | 0.311 | [0.290, 0.333] |
| aware | valid | false_rejection | bare | 0.025 | [0.000, 0.062] |
| aware | valid | false_rejection | negative | 0.879 | [0.825, 0.929] |
| aware | valid | false_rejection | none | 0.029 | [0.000, 0.079] |
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
| explicit | valid | false_rejection | (all) | 0.014 | [0.000, 0.035] |
| explicit | valid | false_rejection | bare | 0.013 | [0.000, 0.033] |
| explicit | valid | false_rejection | negative | 0.008 | [0.000, 0.025] |
| explicit | valid | false_rejection | none | 0.021 | [0.000, 0.054] |
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

Semantic votes: {}; claim-only parse errors: 0.

