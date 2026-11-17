# Power review for the mitigation pre-registration (from recorded runs; no API calls)

Informs, does not set, the non-inferiority margin. Source: experiments/m_power_review.py. B0 = evidence-aware, B1 = evidence-explicit, same cells. d = B1 - B0 per unit approximates the variability of a between-arm difference; the mitigation arms may vary more or less, so the pilot's own A+B - B0 differences are to be checked before the margin is fixed.

## Rates by arm (mean over units, %)

| model | set | units | FA B0 | FA B1 | FD0 B0 | FD0 B1 | Dneg B0 (pp) | Dneg B1 (pp) | units with Dneg B0 < 0 |
|---|---|---|---|---|---|---|---|---|---|
| GPT-4.1 | 11 tasks | 11 | 0.53 | 0.53 | 0.00 | 0.00 | -82.6 | +0.0 | 11/11 |
| GPT-4.1-mini | 11 tasks | 11 | 1.74 | 0.61 | 3.03 | 0.00 | -60.6 | -32.6 | 11/11 |
| Claude Sonnet 4.6 | 11 tasks | 11 | 0.00 | 0.00 | 1.21 | 2.42 | -47.0 | -34.1 | 10/11 |
| GPT-4.1 | AgentDojo primary (19) | 19 | 1.49 | 0.00 | 2.46 | 1.75 | -85.5 | +1.3 | 19/19 |

## Margin a non-inferiority test can support (pp)

Smallest margin delta for which the planned test (two-sided 95% bootstrap CI upper bound of the A+B - B0 difference below delta) would succeed with the stated probability if the true difference were 0, taking the spread of d = B1 - B0 as the spread of the A+B - B0 difference.

| model | set | measure | sd(d) pp | normal 80% | normal 90% | bootstrap 80% | bootstrap 90% |
|---|---|---|---|---|---|---|---|
| GPT-4.1 | 11 tasks | FA | 1.18 | 1.00 | 1.15 | 0.98 | 1.14 |
| GPT-4.1 | 11 tasks | FD0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| GPT-4.1-mini | 11 tasks | FA | 2.62 | 2.21 | 2.56 | 1.36 | 1.37 |
| GPT-4.1-mini | 11 tasks | FD0 | 10.05 | 8.49 | 9.82 | 3.03 | 3.03 |
| Claude Sonnet 4.6 | 11 tasks | FA | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| Claude Sonnet 4.6 | 11 tasks | FD0 | 5.01 | 4.23 | 4.89 | 4.85 | 5.45 |
| GPT-4.1 | AgentDojo primary (19) | FA | 1.26 | 0.81 | 0.94 | 0.79 | 0.88 |
| GPT-4.1 | AgentDojo primary (19) | FD0 | 4.92 | 3.16 | 3.66 | 2.11 | 2.46 |

## Resolution

11 tasks: an invalid-side rate per task rests on 40 cells x 3 repeats = 120 decisions (one decision = 0.83 pp); a valid no-claim rate on 4 cells x 3 = 12 decisions plus 1 control cell x 3. AgentDojo: per case 40 invalid cells x 3 = 120 decisions. The sign-flip test over 11 units has a smallest two-sided p of 2/2048 = 0.00098; over 19 units it is far smaller (Monte Carlo).

## Cost per call in the base runs (list prices, from recorded tokens)

| run | calls | input tokens/call | output tokens/call | USD/call |
|---|---|---|---|---|
| E1-gpt-4.1-run1 | 3828 | 756 | 57 | 0.00197 |
| E1P-gpt-4.1-mini-run1 | 3828 | 756 | 50 | 0.00038 |
| E1P-claude-sonnet-4-6-run1 | 3828 | 855 | 107 | 0.00418 |
| AD1-gpt-4.1-run1 | 6960 | 663 | 53 | 0.00175 |

Note: the recorded `estimated_cost_usd` of E1P-gpt-4.1-mini-run1 (7.314) is computed at GPT-4.1 prices; at gpt-4.1-mini list prices the run cost about $1.46.
