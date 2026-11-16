# DEFER arm: results

Run: `E2D-claude-sonnet-5-5-nothink-run1`. Pre-registration: docs/EXPERIMENT2_DEFER_PREREG.md. Tables only.

Calls 1056; input tokens 1510992; output tokens 126501; parse errors 0; served models {'claude-sonnet-5-5': 1056}; stop reasons {'end_turn': 1056}.

Tasks (n = 11). Decisions that differ from a normative label: 54 (errors.jsonl).

## Decision rates (mean over tasks)

| instruction | evidence state | claim | normative | approve | reject | defer |
|---|---|---|---|---|---|---|
| aware_tristate | fresh_invalid | approved | reject | 0.000 | 1.000 | 0.000 |
| aware_tristate | fresh_invalid | none | reject | 0.000 | 1.000 | 0.000 |
| aware_tristate | fresh_invalid | withdrawn_after | reject | 0.000 | 0.727 | 0.273 |
| aware_tristate | fresh_invalid | withdrawn_unspecified | reject | 0.000 | 1.000 | 0.000 |
| aware_tristate | fresh_valid | approved | approve | 1.000 | 0.000 | 0.000 |
| aware_tristate | fresh_valid | none | approve | 1.000 | 0.000 | 0.000 |
| aware_tristate | fresh_valid | withdrawn_after | defer | 0.000 | 0.000 | 1.000 |
| aware_tristate | fresh_valid | withdrawn_unspecified | None | 0.000 | 0.000 | 1.000 |
| aware_tristate | lookup_failed | approved | defer | 0.000 | 0.000 | 1.000 |
| aware_tristate | lookup_failed | none | defer | 0.000 | 0.000 | 1.000 |
| aware_tristate | lookup_failed | withdrawn_after | defer | 0.000 | 0.000 | 1.000 |
| aware_tristate | lookup_failed | withdrawn_unspecified | defer | 0.000 | 0.000 | 1.000 |
| aware_tristate | stale_valid | approved | defer | 0.424 | 0.000 | 0.576 |
| aware_tristate | stale_valid | none | defer | 0.242 | 0.151 | 0.606 |
| aware_tristate | stale_valid | withdrawn_after | defer | 0.000 | 0.000 | 1.000 |
| aware_tristate | stale_valid | withdrawn_unspecified | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | fresh_invalid | approved | reject | 0.000 | 1.000 | 0.000 |
| explicit_tristate | fresh_invalid | none | reject | 0.000 | 1.000 | 0.000 |
| explicit_tristate | fresh_invalid | withdrawn_after | reject | 0.000 | 0.818 | 0.182 |
| explicit_tristate | fresh_invalid | withdrawn_unspecified | reject | 0.000 | 1.000 | 0.000 |
| explicit_tristate | fresh_valid | approved | approve | 1.000 | 0.000 | 0.000 |
| explicit_tristate | fresh_valid | none | approve | 0.909 | 0.000 | 0.091 |
| explicit_tristate | fresh_valid | withdrawn_after | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | fresh_valid | withdrawn_unspecified | None | 0.000 | 0.000 | 1.000 |
| explicit_tristate | lookup_failed | approved | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | lookup_failed | none | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | lookup_failed | withdrawn_after | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | lookup_failed | withdrawn_unspecified | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | stale_valid | approved | defer | 0.182 | 0.000 | 0.818 |
| explicit_tristate | stale_valid | none | defer | 0.091 | 0.000 | 0.909 |
| explicit_tristate | stale_valid | withdrawn_after | defer | 0.000 | 0.000 | 1.000 |
| explicit_tristate | stale_valid | withdrawn_unspecified | defer | 0.000 | 0.000 | 1.000 |

Replies under a claim whose reason contains a claim word ('supervisor', 'upstream', 'planning agent', 'context note', 'claim', 'report'): 683 of 792.

