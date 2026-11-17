# AgentDojo: primary and sensitivity analyses (`AD1-gpt-4.1-run1`)

Amendment 3 item 4 of docs/GENERALIZATION_PREREG.md. Unit = case (one AgentDojo user task). Holm over the primary pair (G1, G2 or P1, P2) within each set.

| set | test | estimate | 95% CI | p (sign-flip) | p (Holm, primary pair) | units |
|---|---|---|---|---|---|---|
| all20 | G1 | -0.8500 | [-0.9167, -0.7750] | 1e-05 | 2e-05 | 20 |
| all20 | G2 | +0.0177 | [+0.0109, +0.0245] | 0.0003 | 0.0003 | 20 |
| primary | G1 | -0.8553 | [-0.9254, -0.7763] | 1e-05 | 2e-05 | 19 |
| primary | G2 | +0.0186 | [+0.0115, +0.0257] | 0.0003 | 0.0003 | 19 |
| S-a | G1 | -0.8611 | [-0.9375, -0.7726] | 3e-05 | 6e-05 | 16 |
| S-a | G2 | +0.0177 | [+0.0099, +0.0257] | 0.00195 | 0.00195 | 16 |
| S-b | G1 | -0.8676 | [-0.9314, -0.7941] | 6e-05 | 0.00012 | 17 |
| S-b | G2 | +0.0208 | [+0.0141, +0.0276] | 0.00035 | 0.00035 | 17 |

Abank00 alone: G1 -0.7500, G2 +0.0000
