# Error coding: agreement and final stages (exploratory)

Two independent coders (A, B) coded all incorrect Experiment 1 (GPT-4.1) and Experiment 2 decisions from the same blinded input and codebook. Disagreements are adjudicated in adjudication.csv. Settings are never pooled. DEFER-arm errors are classified mechanically (normative vs actual decision) in REPORT.md.

## Agreement (Cohen's kappa, raw agreement)

| scope | evidence_reading | reason_conclusion | driver | timing_misread |
|---|---|---|---|---|
| all rows (n=580) | 0.935 (0.969) | 0.994 (0.997) | 0.908 (0.94) | 0.931 (0.972) |
| E1/gpt-4.1 (n=123) | 0.908 (0.959) | 1.0 (1.0) | 1.0 (1.0) | None (1.0) |
| E2/claude-sonnet-5-5 (n=1) | None (1.0) | None (1.0) | None (1.0) | None (1.0) |
| E2/claude-sonnet-5-5-nothink (n=136) | 0.854 (0.993) | 0.985 (0.993) | 0.861 (0.904) | 0.717 (0.963) |
| E2/gpt-4.1 (n=320) | 0.929 (0.963) | 0.994 (0.997) | 0.875 (0.931) | 0.931 (0.966) |

Final stage vs the first author's manual stage (manual samples): n = 103, raw agreement 0.806, kappa 0.696. Unresolved disagreements: 0.

## Final stages

| experiment | setting | stage | n | of errors | driver |
|---|---|---|---|---|---|
| E1 | gpt-4.1 | claim_without_reading | 29 | 123 | claim: 29 |
| E1 | gpt-4.1 | evidence_misread | 7 | 123 | evidence_misread: 4, claim: 2, policy_misapplied: 1 |
| E1 | gpt-4.1 | read_correctly_decided_wrong | 83 | 123 | claim: 82, policy_misapplied: 1 |
| E1 | gpt-4.1 | reason_decision_mismatch | 4 | 123 | inconsistent: 4 |
| E2 | claude-sonnet-5-5 | reason_decision_mismatch | 1 | 1 | inconsistent: 1 |
| E2 | claude-sonnet-5-5-nothink | evidence_misread | 3 | 136 | policy_misapplied: 2, evidence_misread: 1 |
| E2 | claude-sonnet-5-5-nothink | read_correctly_decided_wrong | 85 | 136 | uncertainty: 47, policy_misapplied: 35, other: 3 |
| E2 | claude-sonnet-5-5-nothink | reason_decision_mismatch | 48 | 136 | inconsistent: 48 |
| E2 | gpt-4.1 | claim_without_reading | 43 | 320 | claim: 43 |
| E2 | gpt-4.1 | evidence_misread | 6 | 320 | claim: 4, policy_misapplied: 1, evidence_misread: 1 |
| E2 | gpt-4.1 | not_stated_other | 116 | 320 | policy_misapplied: 110, uncertainty: 6 |
| E2 | gpt-4.1 | read_correctly_decided_wrong | 155 | 320 | claim: 121, policy_misapplied: 25, uncertainty: 9 |
