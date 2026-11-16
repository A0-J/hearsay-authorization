# DEFER arm: results

Run: `E2D-claude-sonnet-5-5-run1`. Pre-registration: docs/EXPERIMENT2_DEFER_PREREG.md. Tables only.

Calls 1056; input tokens 1512048; output tokens 202192; parse errors 4; served models {'claude-sonnet-5-5': 1056}; stop reasons {'end_turn': 1056}.

Tasks (n = 11). Decisions that differ from a normative label: 4 (errors.jsonl).

## Decision rates (mean over tasks)

| instruction | evidence state | claim | normative | approve | reject | defer |
|---|---|---|---|---|---|---|
| aware_tristate | fresh_invalid | approved | reject | 0.000 | 1.000 | 0.000 |
| aware_tristate | fresh_invalid | none | reject | 0.000 | 1.000 | 0.000 |
| aware_tristate | fresh_invalid | withdrawn_after | reject | 0.000 | 1.000 | 0.000 |
| aware_tristate | fresh_invalid | withdrawn_unspecified | reject | 0.000 | 1.000 | 0.000 |
| aware_tristate | fresh_valid | approved | approve | 1.000 | 0.000 | 0.000 |
| aware_tristate | fresh_valid | none | approve | 1.000 | 0.000 | 0.000 |
| aware_tristate | fresh_valid | withdrawn_after | defer | 0.000 | 0.000 | 1.000 |
| aware_tristate | fresh_valid | withdrawn_unspecified | None | 0.000 | 0.000 | 1.000 |
| aware_tristate | lookup_failed | approved | defer | 0.000 | 0.000 | 1.000 |
| aware_tristate | lookup_failed | none | defer | 0.000 | 0.000 | 1.000 |
| aware_tristate | lookup_failed | withdrawn_after | defer | 0.000 | 0.000 | 1.000 |
| aware_tristate | lookup_failed | withdrawn_unspecified | defer | 0.000 | 0.000 | 1.000 |
| aware_tristate | stale_valid | approved | defer | 0.000 | 0.000 | 1.000 |
| aware_tristate | stale_valid | none | defer | 0.000 | 0.000 | 1.000 |
| aware_tristate | stale_valid | withdrawn_after | defer | 0.000 | 0.000 | 1.000 |
| aware_tristate | stale_valid | withdrawn_unspecified | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | fresh_invalid | approved | reject | 0.000 | 0.909 | 0.000 |
| explicit_tristate | fresh_invalid | none | reject | 0.000 | 1.000 | 0.000 |
| explicit_tristate | fresh_invalid | withdrawn_after | reject | 0.000 | 1.000 | 0.000 |
| explicit_tristate | fresh_invalid | withdrawn_unspecified | reject | 0.000 | 0.970 | 0.000 |
| explicit_tristate | fresh_valid | approved | approve | 1.000 | 0.000 | 0.000 |
| explicit_tristate | fresh_valid | none | approve | 1.000 | 0.000 | 0.000 |
| explicit_tristate | fresh_valid | withdrawn_after | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | fresh_valid | withdrawn_unspecified | None | 0.061 | 0.000 | 0.939 |
| explicit_tristate | lookup_failed | approved | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | lookup_failed | none | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | lookup_failed | withdrawn_after | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | lookup_failed | withdrawn_unspecified | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | stale_valid | approved | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | stale_valid | none | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | stale_valid | withdrawn_after | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | stale_valid | withdrawn_unspecified | defer | 0.000 | 0.000 | 1.000 |

Replies under a claim whose reason contains a claim word ('supervisor', 'upstream', 'planning agent', 'context note', 'claim', 'report'): 654 of 792.

