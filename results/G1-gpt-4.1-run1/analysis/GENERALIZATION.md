# Generalization (case level): `G1-gpt-4.1-run1`

Pre-registration: docs/GENERALIZATION_PREREG.md. 28 tasks in 8 cases. Tables only.

| level | test | estimate | 95% CI | p (sign-flip) | p (Holm) | n |
|---|---|---|---|---|---|---|
| case | G1_negative_claim_valid_aware | -0.7927 | [-0.8823, -0.6750] | 0.0078 | 0.0156 | 8 cases |
| case | G2_positive_claims_invalid_aware | +0.0072 | [-0.0012, +0.0159] | 0.1875 | 0.1875 | 8 cases |
| task | G1 | -0.7976 | [-0.8690, -0.7173] | 0.0000 | | 28 tasks |
| task | G2 | +0.0071 | [-0.0015, +0.0149] | 0.1286 | | 28 tasks |
| case, e1_case_new_domain | G1 | -0.7821 | [-0.8833, -0.6429] | 0.0156 | | 7 cases |
| case, e1_case_new_domain | G2 | +0.0086 | [-0.0013, +0.0173] | 0.1875 | | 7 cases |
| case, new_case | G1 | -0.8667 | [-0.8667, -0.8667] | 1.0000 | | 1 cases |
| case, new_case | G2 | -0.0021 | [-0.0021, -0.0021] | 1.0000 | | 1 cases |
