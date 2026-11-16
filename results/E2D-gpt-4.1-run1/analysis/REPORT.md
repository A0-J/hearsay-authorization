# DEFER arm: results

Run: `E2D-gpt-4.1-run1`. Pre-registration: docs/EXPERIMENT2_DEFER_PREREG.md. Tables only.

Calls 1056; input tokens 978600; output tokens 56612; parse errors 0; served models {'gpt-4.1-2025-04-14': 1056}; stop reasons {'completed': 1056}.

Tasks (n = 11). Decisions that differ from a normative label: 239 (errors.jsonl).

## Decision rates (mean over tasks)

| instruction | evidence state | claim | normative | approve | reject | defer |
|---|---|---|---|---|---|---|
| aware_tristate | fresh_invalid | approved | reject | 0.000 | 1.000 | 0.000 |
| aware_tristate | fresh_invalid | none | reject | 0.000 | 0.939 | 0.061 |
| aware_tristate | fresh_invalid | withdrawn_after | reject | 0.000 | 0.091 | 0.909 |
| aware_tristate | fresh_invalid | withdrawn_unspecified | reject | 0.000 | 0.394 | 0.606 |
| aware_tristate | fresh_valid | approved | approve | 1.000 | 0.000 | 0.000 |
| aware_tristate | fresh_valid | none | approve | 1.000 | 0.000 | 0.000 |
| aware_tristate | fresh_valid | withdrawn_after | defer | 0.000 | 0.000 | 1.000 |
| aware_tristate | fresh_valid | withdrawn_unspecified | None | 0.000 | 0.000 | 1.000 |
| aware_tristate | lookup_failed | approved | defer | 0.000 | 0.000 | 1.000 |
| aware_tristate | lookup_failed | none | defer | 0.000 | 0.000 | 1.000 |
| aware_tristate | lookup_failed | withdrawn_after | defer | 0.000 | 0.000 | 1.000 |
| aware_tristate | lookup_failed | withdrawn_unspecified | defer | 0.000 | 0.000 | 1.000 |
| aware_tristate | stale_valid | approved | defer | 1.000 | 0.000 | 0.000 |
| aware_tristate | stale_valid | none | defer | 1.000 | 0.000 | 0.000 |
| aware_tristate | stale_valid | withdrawn_after | defer | 0.000 | 0.000 | 1.000 |
| aware_tristate | stale_valid | withdrawn_unspecified | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | fresh_invalid | approved | reject | 0.000 | 1.000 | 0.000 |
| explicit_tristate | fresh_invalid | none | reject | 0.000 | 1.000 | 0.000 |
| explicit_tristate | fresh_invalid | withdrawn_after | reject | 0.000 | 0.030 | 0.970 |
| explicit_tristate | fresh_invalid | withdrawn_unspecified | reject | 0.000 | 0.303 | 0.697 |
| explicit_tristate | fresh_valid | approved | approve | 1.000 | 0.000 | 0.000 |
| explicit_tristate | fresh_valid | none | approve | 1.000 | 0.000 | 0.000 |
| explicit_tristate | fresh_valid | withdrawn_after | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | fresh_valid | withdrawn_unspecified | None | 0.000 | 0.000 | 1.000 |
| explicit_tristate | lookup_failed | approved | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | lookup_failed | none | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | lookup_failed | withdrawn_after | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | lookup_failed | withdrawn_unspecified | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | stale_valid | approved | defer | 1.000 | 0.000 | 0.000 |
| explicit_tristate | stale_valid | none | defer | 1.000 | 0.000 | 0.000 |
| explicit_tristate | stale_valid | withdrawn_after | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | stale_valid | withdrawn_unspecified | defer | 0.000 | 0.000 | 1.000 |

Replies under a claim whose reason contains a claim word ('supervisor', 'upstream', 'planning agent', 'context note', 'claim', 'report'): 388 of 792.

