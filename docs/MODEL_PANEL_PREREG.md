# Experiment 1 model panel: pre-registration

Fixed 2026-11-16, before any panel data. Inputs, instructions and analysis are Experiment 1's, frozen
(docs/EXPERIMENT1_PREREG.md, dataset v1.0.0-exp1, `experiments/analyze_exp1.py`). Each setting is a separate run,
reported on its own, never pooled.

## Question (RQ1)

Is Experiment 1's pattern specific to GPT-4.1? The pattern is a large drop from a withdrawal claim on valid
evidence under evidence-aware, and none under evidence-explicit. A second question: is the Claude Sonnet 5.5
result (no errors) a property of the model family, or of its default reasoning?

## Settings (chosen for what each one separates)

| setting | request | what it separates |
|---|---|---|
| gpt-4.1-mini | temperature 1, top_p 1 | a smaller model of the same family as GPT-4.1 |
| gpt-4o | temperature 1, top_p 1 | an earlier OpenAI non-reasoning model |
| gpt-5.5 | provider default (no sampling parameters) | an OpenAI reasoning model |
| claude-sonnet-5-5, between_tools | temperature 1, `thinking: {"type": "between_tools"}` | the same model as the Claude run, without thinking before the reply |
| claude-haiku-5-5 | temperature 1, no thinking field (model default) | a smaller current Claude model |
| claude-sonnet-4-6 | temperature 1, no thinking field (no thinking by default) | an earlier Claude model without thinking |

All Claude runs use `max_output_tokens` 4096, so thinking cannot truncate a reply. The existing Claude Sonnet 5.5
run used 1,024; its largest output was 480 tokens. Every call records the stop reason.

## Analysis

- Per run: `experiments/analyze_exp1.py`, unchanged. This gives every pre-registered test of Experiment 1
  (H1–H8, Amendment 1) and every cell rate.
- Across runs: a side-by-side table of the H1 and H5 contrasts (aware and explicit) and the error counts,
  per setting. It is descriptive, with each setting's own interval; no pooled test.
