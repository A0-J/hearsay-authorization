# H3 reversal: the two completeness lines (exploratory, post hoc)

Written after the AgentDojo H3 result. Descriptive: estimates and bootstrap 95% intervals over units (10,000 resamples, seed 0); no tests. Sets and models are never pooled. Source: experiments/analyze_h3_completeness.py.

## 0. The manipulation

- 11 tasks: abs_complete = abs_list plus exactly the two lines in 11/11 tasks.
- AB new: abs_complete = abs_list plus exactly the two lines in 28/28 tasks.
- AgentDojo: abs_complete = abs_list plus exactly the two lines in 20/20 tasks.

## 1. Approvals on invalid evidence, abs_list vs abs_complete

Approved / judged. `specific` names an approval id that is not in the evidence; the other positive claims name no id.

| set / model | aware: none | aware: unverified+bare+verified | aware: specific, abs_list | aware: specific, abs_complete | explicit: all claims, abs_list | explicit: all claims, abs_complete |
|---|---|---|---|---|---|---|
| GPT-4.1 / 11 tasks | 0/33 / 0/33 | 0/99 / 0/99 | 1/33 | 3/33 | 0/165 | 0/165 |
| GPT-4.1 / AB new | 0/84 / 0/84 | 0/252 / 0/252 | 7/84 | 14/84 | 0/420 | 0/420 |
| GPT-4.1 / AgentDojo | 0/60 / 0/60 | 0/180 / 0/180 | 5/60 | 29/60 | 0/300 | 0/300 |
| GPT-4.1 / AgentDojo primary (19) | 0/57 / 0/57 | 0/171 / 0/171 | 5/57 | 29/57 | 0/285 | 0/285 |
| gpt-4.1-mini / 11 tasks | 0/33 / 0/33 | 0/99 / 0/99 | 0/33 | 0/33 | 0/165 | 0/165 |
| gpt-4o / 11 tasks | 0/33 / 0/33 | 0/99 / 0/99 | 19/33 | 9/33 | 0/165 | 0/165 |
| gpt-5.5 / 11 tasks | 0/33 / 0/33 | 0/99 / 0/99 | 0/33 | 0/33 | 0/165 | 0/165 |
| claude-haiku-5-5 / 11 tasks | 0/33 / 0/33 | 0/99 / 0/99 | 0/33 | 0/33 | 0/165 | 0/165 |
| claude-sonnet-4-6 / 11 tasks | 0/33 / 0/33 | 0/99 / 0/99 | 0/33 | 0/33 | 0/165 | 0/165 |
| claude-sonnet-5-5 (adaptive) / 11 tasks | 0/33 / 0/33 | 0/99 / 0/99 | 0/33 | 0/33 | 0/165 | 0/165 |
| claude-sonnet-5-5 (no thinking) / 11 tasks | 0/33 / 0/33 | 0/99 / 0/99 | 0/33 | 0/33 | 0/165 | 0/165 |

(The `none` and three-claim columns show abs_list / abs_complete.)

## 2. Specific claim, aware: abs_complete minus abs_list, per unit

Positive = more approvals with the two lines (the reverse of H3's prediction).

| set / model | units | mean difference (pp) | 95% CI | units higher with the lines | lower | equal |
|---|---|---|---|---|---|---|
| GPT-4.1 / 11 tasks | 11 | +6.1 | [-9.1, +27.3] | 1 | 1 | 9 |
| GPT-4.1 / AB new | 8 | +6.2 | [+1.7, +12.1] | 3 | 0 | 5 |
| GPT-4.1 / AgentDojo | 20 | +40.0 | [+23.3, +56.7] | 12 | 0 | 8 |
| GPT-4.1 / AgentDojo primary (19) | 19 | +42.1 | [+26.3, +59.7] | 12 | 0 | 7 |
| gpt-4.1-mini / 11 tasks | 11 | +0.0 | [+0.0, +0.0] | 0 | 0 | 11 |
| gpt-4o / 11 tasks | 11 | -30.3 | [-51.5, -12.1] | 0 | 6 | 5 |
| gpt-5.5 / 11 tasks | 11 | +0.0 | [+0.0, +0.0] | 0 | 0 | 11 |
| claude-haiku-5-5 / 11 tasks | 11 | +0.0 | [+0.0, +0.0] | 0 | 0 | 11 |
| claude-sonnet-4-6 / 11 tasks | 11 | +0.0 | [+0.0, +0.0] | 0 | 0 | 11 |
| claude-sonnet-5-5 (adaptive) / 11 tasks | 11 | +0.0 | [+0.0, +0.0] | 0 | 0 | 11 |
| claude-sonnet-5-5 (no thinking) / 11 tasks | 11 | +0.0 | [+0.0, +0.0] | 0 | 0 | 11 |

AgentDojo by suite (GPT-4.1, aware, specific): abs_list / abs_complete

| suite | tasks | abs_list | abs_complete |
|---|---|---|---|
| bank | 5 | 0/15 | 0/15 |
| slack | 12 | 4/36 | 24/36 |
| travel | 1 | 0/3 | 0/3 |
| work | 2 | 1/6 | 5/6 |

## 3. What the reasons cite (GPT-4.1, aware, specific claim)

String rules (regexes `FEAT` in the script), counted per decision. `basis = claimed id`: the reply's basis field is the id named in the task message.

| set | condition | decision | n | basis = claimed id | reason names the claimed id | names task message | cites lookup / NOT_FOUND | cites snapshot / complete | says the approval is absent from the records |
|---|---|---|---|---|---|---|---|---|---|
| 11 tasks | abs_list | approve | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| 11 tasks | abs_list | reject | 32 | 0 | 14 | 10 | 0 | 0 | 22 |
| 11 tasks | abs_complete | approve | 3 | 3 | 3 | 3 | 0 | 0 | 0 |
| 11 tasks | abs_complete | reject | 30 | 0 | 6 | 2 | 2 | 0 | 24 |
| AB new | abs_list | approve | 7 | 7 | 7 | 5 | 0 | 0 | 0 |
| AB new | abs_list | reject | 77 | 0 | 51 | 27 | 0 | 0 | 64 |
| AB new | abs_complete | approve | 14 | 14 | 12 | 14 | 0 | 0 | 0 |
| AB new | abs_complete | reject | 70 | 0 | 6 | 2 | 0 | 0 | 54 |
| AgentDojo | abs_list | approve | 5 | 5 | 5 | 3 | 0 | 0 | 0 |
| AgentDojo | abs_list | reject | 55 | 0 | 40 | 17 | 0 | 0 | 48 |
| AgentDojo | abs_complete | approve | 29 | 29 | 23 | 25 | 0 | 0 | 0 |
| AgentDojo | abs_complete | reject | 31 | 0 | 5 | 4 | 2 | 0 | 27 |

## 4. Reference: no evidence block at all (claim-only ablation, GPT-4.1)

Its own instruction (task message and policy only), so not a third level of the same manipulation.

| set | specific claim, call side: approved / judged | no claim: approved / judged |
|---|---|---|
| 11 tasks | 31/33 | 0/33 |
| AB new | 83/84 | 16/84 |
| AgentDojo | 50/60 | 0/60 |

## 5. Pre-registered H3 values (claim effect pooled over the four positive claims)

See results/invalid-approvals/REPORT.md, section 5. The pooled H3 contrast is carried by the `specific` claim: the other three positive claims produce no approvals under either condition in the GPT-4.1 sets (section 1).
