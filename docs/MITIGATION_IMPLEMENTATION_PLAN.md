# Mitigation experiment (M): implementation plan

Companion to docs/MITIGATION_PREREG.md (draft). Nothing below calls an API until the researcher has reviewed and
committed the pre-registration. Steps 1–5 need no API key.

## 1. Code

| file | content |
|---|---|
| `src/hearsay/authbench/mitigation.py` (new) | `A_REPLY` (the reviewed text); `separate_claim(input) -> input` (moves the single `[Context note: …]` line into the labelled block, or inserts `- none`); `build_arm_input(cell, arm)` for A, B and A+B |
| `experiments/build_mitigation.py` (new) | builds `dataset/m_exp1/` (Set 1) and `dataset/m_ad/` (Set 2) from the frozen `dataset/exp1/` and `dataset/exp1_ad/`, which it never writes. Instruction keys `m_A`, `m_B`, `m_AB`. Writes `pilot_cells.json` (the 15 pilot cells per task) and a manifest with the SHA-256 of each source cell and of each new input |
| `tests/test_mitigation.py` (new) | transform and identity tests (§3) |
| `configs/m_{stage}_{model}.json` (new) | Stage P, C and G configs. Models and sampling are copied from the base configs (`e1_panel_gpt-4.1-mini.json`, `e1_panel_claude-sonnet-4-6.json`, `exp1_gpt41.json`, `ad_e1_gpt-4.1.json`); `dataset_dir` points to the new datasets |
| `experiments/run_exp1.py` (existing) | runs the new datasets unchanged: same parser (approve iff `approve`), resumable, pause-safe. A `--cells pilot_cells.json` filter is the only addition, for Stage P |
| `experiments/analyze_mitigation.py` (new) | M1–M4 per model and set; the reuse check of §5 of the pre-registration (served model and hashes); bootstrap CIs, sign-flip p, Holm, the non-inferiority rule with δ read from the committed pre-registration; the pilot go/no-go report (G1–G3); PNG figures; `results/m-*/analysis/REPORT.md` |

## 2. Data checks at build time (no API)

1. Every new cell is byte-identical to its source cell outside the moved note, the inserted block and the reply
   clause.
2. In claim cells, the note text appears exactly once, verbatim, inside the block and nowhere in the task
   message. In no-claim cells the block reads `- none`.
3. The evidence block, policy, request and call hashes equal the source cell's.
4. 56 cells per task: valid 12, invalid 40, control 4. The pilot list has 15 per task.
5. Labels (`gate_allowed`) are copied from the source and not recomputed.

## 3. Tests (no API)

- Unit tests for `separate_claim`: every claim type, no-claim cells, and the "(UNVERIFIED)" and "VERIFIED."
  markers kept verbatim.
- Unit tests for the parser on A-format replies: extra fields are kept in the raw reply; `defer` and other values
  are recorded as `bad decision` and counted as not approved.
- The existing test suite (304 tests) must still pass.
- Dry runs (`--dry-run`, fake client, 0 calls) for every config: the counts of cells × repeats and the token
  estimates are printed and checked against the pre-registration.

## 4. Order of work and decisions

| step | who | gate |
|---|---|---|
| 1. Fix the A and B texts, δ_FA, δ_FD, g, h | researcher | the **[OPEN]** items |
| 2. Build datasets, run checks, tests and dry runs | assistant | all checks pass |
| 3. Commit the pre-registration and the build | researcher | before any call |
| 4. Stage P, one model at a time (GPT-4.1-mini → GPT-4.1 → Claude Sonnet 4.6, cheapest first), about $4 | assistant, after approval | — |
| 5. Pilot report (G1–G3 per model; spread of A+B − B0) | assistant | the researcher decides go/no-go per model and confirms δ |
| 6. Stage C for the models that passed, one at a time, about $43 at most | assistant, after approval | — |
| 7. Set 1 analysis and report | assistant | no change to arms or texts afterwards |
| 8. Stage G (GPT-4.1, GPT-4.1-mini), about $11 | assistant, after approval | — |
| 9. Set 2 analysis and report | assistant | — |

- Archives and the registry follow the existing practice: raw results stay out of git and are recorded with
  their SHA-256.
- The assistant makes no git commit.
