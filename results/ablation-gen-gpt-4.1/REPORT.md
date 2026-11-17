# Verification-method ablation: results

E1 run `G1-gpt-4.1-run1`, claim-only run `GAB-claim-only-gpt-4.1-run1`, semantic run `GAB-semantic-gpt-4.1-run1`. Pre-registration: docs/ABLATION_PREREG.md. Tables only.

Decisions per method: {'claim_only': 4704, 'aware': 4704, 'explicit': 4704, 'gate': 4704, 'semantic_gate': 4704}.

## Pre-registered comparisons (unit = task, Holm over A1-A3)

| test | estimate | 95% CI | p (sign-flip) | p (Holm) |
|---|---|---|---|---|
| A1_unauthorized_approval_positive_claims_claim_only_minus_aware | +0.4364 | [+0.3545, +0.5223] | 0.0000 | 0.0000 |
| A2_false_rejection_negative_claim_aware_minus_explicit | +0.7946 | [+0.7143, +0.8661] | 0.0000 | 0.0000 |
| A3_false_rejection_valid_and_control_semantic_gate_minus_explicit | +0.7820 | [+0.6682, +0.8810] | 0.0000 | 0.0000 |

## Rates per method (mean over tasks; the gate is the labels' definition)

| method | side | measure | claim | rate | 95% CI |
|---|---|---|---|---|---|
| claim_only | invalid | unauthorized_approval | (all) | 0.398 | [0.317, 0.481] |
| claim_only | invalid | unauthorized_approval | bare | 0.309 | [0.167, 0.476] |
| claim_only | invalid | unauthorized_approval | none | 0.191 | [0.083, 0.309] |
| claim_only | invalid | unauthorized_approval | specific | 0.988 | [0.964, 1.000] |
| claim_only | invalid | unauthorized_approval | unverified | 0.083 | [0.000, 0.191] |
| claim_only | invalid | unauthorized_approval | verified | 0.417 | [0.250, 0.583] |
| claim_only | valid | false_rejection | (all) | 0.833 | [0.746, 0.913] |
| claim_only | valid | false_rejection | bare | 0.691 | [0.524, 0.833] |
| claim_only | valid | false_rejection | negative | 1.000 | [1.000, 1.000] |
| claim_only | valid | false_rejection | none | 0.809 | [0.691, 0.917] |
| claim_only | control | false_rejection | (all) | 0.000 | [0.000, 0.000] |
| claim_only | control | false_rejection | bare | 0.000 | [0.000, 0.000] |
| claim_only | control | false_rejection | none | 0.000 | [0.000, 0.000] |
| claim_only | control | false_rejection | unverified | 0.000 | [0.000, 0.000] |
| claim_only | control | false_rejection | verified | 0.000 | [0.000, 0.000] |
| aware | invalid | unauthorized_approval | (all) | 0.012 | [0.006, 0.018] |
| aware | invalid | unauthorized_approval | bare | 0.009 | [0.000, 0.021] |
| aware | invalid | unauthorized_approval | none | 0.006 | [0.000, 0.016] |
| aware | invalid | unauthorized_approval | specific | 0.031 | [0.012, 0.054] |
| aware | invalid | unauthorized_approval | unverified | 0.006 | [0.000, 0.013] |
| aware | invalid | unauthorized_approval | verified | 0.006 | [0.000, 0.013] |
| aware | valid | false_rejection | (all) | 0.266 | [0.239, 0.290] |
| aware | valid | false_rejection | bare | 0.000 | [0.000, 0.000] |
| aware | valid | false_rejection | negative | 0.798 | [0.717, 0.869] |
| aware | valid | false_rejection | none | 0.000 | [0.000, 0.000] |
| aware | control | false_rejection | (all) | 0.000 | [0.000, 0.000] |
| aware | control | false_rejection | bare | 0.000 | [0.000, 0.000] |
| aware | control | false_rejection | none | 0.000 | [0.000, 0.000] |
| aware | control | false_rejection | unverified | 0.000 | [0.000, 0.000] |
| aware | control | false_rejection | verified | 0.000 | [0.000, 0.000] |
| explicit | invalid | unauthorized_approval | (all) | 0.006 | [0.001, 0.015] |
| explicit | invalid | unauthorized_approval | bare | 0.007 | [0.000, 0.018] |
| explicit | invalid | unauthorized_approval | none | 0.006 | [0.000, 0.016] |
| explicit | invalid | unauthorized_approval | specific | 0.006 | [0.000, 0.016] |
| explicit | invalid | unauthorized_approval | unverified | 0.007 | [0.000, 0.019] |
| explicit | invalid | unauthorized_approval | verified | 0.006 | [0.000, 0.016] |
| explicit | valid | false_rejection | (all) | 0.001 | [0.000, 0.003] |
| explicit | valid | false_rejection | bare | 0.000 | [0.000, 0.000] |
| explicit | valid | false_rejection | negative | 0.003 | [0.000, 0.009] |
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
| semantic_gate | valid | false_rejection | (all) | 0.726 | [0.583, 0.857] |
| semantic_gate | valid | false_rejection | bare | 0.726 | [0.583, 0.857] |
| semantic_gate | valid | false_rejection | negative | 0.726 | [0.583, 0.857] |
| semantic_gate | valid | false_rejection | none | 0.726 | [0.583, 0.857] |
| semantic_gate | control | false_rejection | (all) | 0.952 | [0.893, 1.000] |
| semantic_gate | control | false_rejection | bare | 0.952 | [0.893, 1.000] |
| semantic_gate | control | false_rejection | none | 0.952 | [0.893, 1.000] |
| semantic_gate | control | false_rejection | unverified | 0.952 | [0.893, 1.000] |
| semantic_gate | control | false_rejection | verified | 0.952 | [0.893, 1.000] |

Semantic votes: {'not_aligned': 198, 'aligned': 82, 'uncertain': 224}; claim-only parse errors: 0.

