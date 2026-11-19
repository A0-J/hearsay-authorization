# Experiment index

One entry per experiment. Each entry gives the question, the pre-registration, the dataset, the runs and
their status, where the outputs are, and the headline results. Status as of 2026-11-18.

## Run-ID legend

| prefix | experiment | dataset | pre-registration |
|---|---|---|---|
| `A-*` | Experiment A, pilot (verifier-only, 5 tasks) | built in code | none (pilot) |
| `E1-*` | Experiment 1: claims × evidence states, 11 tasks | `exp1` | EXPERIMENT1_PREREG.md |
| `E1P-*` | Experiment 1 model panel (same cells, other models) | `exp1` | MODEL_PANEL_PREREG.md |
| `E2-*` | Experiment 2: mechanism (timing, source, record policy, instruction) | `exp2` | EXPERIMENT2_PREREG.md |
| `E2D-*` | Experiment 2 DEFER arm: approve / reject / defer | `exp2_defer` | EXPERIMENT2_DEFER_PREREG.md |
| `ABL-*` | verification-method ablation, 11 tasks (claim-only, semantic) | `ablation_*` | ABLATION_PREREG.md |
| `G1-*`, `G2E-*` | generalization: new AuthorizationBench tasks (E1 cells, E2 cells) | `exp1_gen`, `exp2_gen` | GENERALIZATION_PREREG.md |
| `GAB-*` | ablation on the new AuthorizationBench tasks | `ablation_*_gen` | GENERALIZATION_PREREG.md |
| `AD1-*`, `AD2E-*` | generalization: AgentDojo tasks (E1 cells, E2 cells) | `exp1_ad`, `exp2_ad` | GENERALIZATION_PREREG.md |
| `ADAB-*` | ablation on the AgentDojo tasks | `ablation_*_ad` | GENERALIZATION_PREREG.md |
| `E3-*` | Experiment 3: end-to-end delegation with real tool calls | built at run time | EXPERIMENT3_E2E_PREREG.md |
| `PV2X2-*` | planner × verifier 2×2 on the Experiment 3 runtime (coded, not run) | built at run time | PLANNER_VERIFIER_2X2_PREREG_DRAFT.md (draft) |
| `SIG-*` | signed-state experiment: plain vs signed-and-verified approval state vs the same plus PCM's claim verdict (with and without its reason); Observer arm (`SIG-obs1-*`, `SIG-obs2-*`); `SIG-pilot-*` is a pilot, never data | `sig`, `sig_obs1`, `sig_obs2` | SIGNED_STATE_PREREG.md (fixed r3, 2026-11-18) |
| `SIGX-*` | escalation follow-up, exploratory: no covering record + forged approval id, gpt-4o, the four SIG presentations; `SIGX-pilot-*` is a pilot, never data | `sigx` | SIGX_ESCALATION_PREREG_DRAFT.md (draft, exploratory) |
| `*-dryrun`, `*-smoke*` | fake-client or environment checks; never data | — | — |

Model suffixes:
- `gpt-4.1`, `gpt-4.1-mini`, `gpt-4o`, `gpt-5.5`;
- `claude-sonnet-5-5`: adaptive thinking, the model default;
- `claude-sonnet-5-5-nothink`: thinking off;
- `claude-sonnet-4-6`, `claude-haiku-5-5`.

## Experiments

### Experiment A: pilot (exploratory)

- **Question:** do claims raise approval in a verifier-only setting?
- **Runs:** `A-pilot-v2` (891 calls, complete), `A-smoke-v2`.
- **Result:** fabricated approvals were accepted 45% with a claim and 0% without (meeting tasks only).
  Experiment 1's pilot-format arm reproduced only +6.1 pp (H8). The pilot is a motivation, not an effect size.

### Experiment 1: claims × evidence states (11 tasks)

- **Pre-registration:** EXPERIMENT1_PREREG.md.
- **Cells:** 1,276 = 11 tasks × 116 cells. Repeats: 3.
- **Runs:**
  - `E1-gpt-4.1-run1` (3,828, complete);
  - `E1-claude-sonnet-5-5-run1` (3,828, complete).
- **Primary hypotheses, not supported (GPT-4.1):**
  - H1, positive claims on invalid evidence: +0.7, Holm p 0.375;
  - H2: +0.6, Holm p 1.0;
  - H3: −1.5, Holm p 1.0.
- **Secondary:** H5, the withdrawal claim on valid evidence: GPT-4.1 −82.6 [−93.2, −72.0], 11/11 tasks
  negative. Evidence-explicit: 0. Claude Sonnet 5.5: 0.
- **Outputs:** `results/E1-*/analysis/`, `results/E1-figures/` (condition and per-task figures, error-cause table).

### Model panel (11 tasks, same cells)

- **Pre-registration:** MODEL_PANEL_PREREG.md.
- **Runs** (all complete, 3,828 each): `E1P-gpt-4.1-mini`, `E1P-gpt-4o`, `E1P-gpt-5.5`, `E1P-claude-haiku-5-5`,
  `E1P-claude-sonnet-4-6`, `E1P-claude-sonnet-5-5-nothink`.
- **H5 (aware / explicit):**

  | model | aware | explicit |
  |---|---|---|
  | gpt-4o | −75.0 | −7.6 |
  | gpt-4.1-mini | −60.6 | −32.6 |
  | Claude Sonnet 4.6 | −47.0 | −34.1 |
  | gpt-5.5 | 0 | 0 |
  | Claude Haiku 5.5 | 0 | 0 |
  | Claude Sonnet 5.5, thinking off | −0.8 | −1.5 |

### Experiment 2: mechanism (11 tasks)

- **Pre-registration:** EXPERIMENT2_PREREG.md.
- **Cells:** 1,364 cells; block A = the Experiment 1 anchor; block B = timed evidence × claim × timing × source
  × policy × instruction.
- **Runs:** `E2-gpt-4.1-run1`, `E2-claude-sonnet-5-5-run1`, `E2-claude-sonnet-5-5-nothink-run1` (4,092 each,
  complete).
- **GPT-4.1:**
  - P1 −84.1 (withdrawal on valid evidence, confirmed as a primary test);
  - P2 0 (claim before vs after the snapshot);
  - S1 +100 (asymmetry);
  - S3 0 (source);
  - S4 0 (record-authority policy);
  - S5 +97 (explicit instruction);
  - S6 0.
- **Claude Sonnet 5.5:** adaptive P1 0. Thinking off: P1 −1.5, P2 +18.2, S4 −98.5, a different pattern.
- **Outputs:** `results/E2-*/analysis/`, `results/E2-figures/` (approval by claim × time × policy; forest plot
  of P1–P2 and S1–S6).

### Experiment 2, DEFER arm (exploratory, descriptive)

- **Pre-registration:** EXPERIMENT2_DEFER_PREREG.md.
- **Cells:** 4 evidence states (fresh valid, fresh invalid, stale valid, lookup failed) × 4 claims ×
  2 instructions.
- **Runs:** `E2D-gpt-4.1-run1`, `E2D-claude-sonnet-5-5-run1`, `E2D-claude-sonnet-5-5-nothink-run1` (1,056 each,
  complete).
- **GPT-4.1:**
  - fresh valid + withdrawal claim → defer 100%;
  - stale valid without a claim → approve 100% (normative: defer);
  - lookup failed → defer 100%.
- **Outputs:** `results/E2D-*/analysis/`, `results/E2-figures/png/fig_defer_*`.

### Verification-method ablation (11 tasks)

- **Pre-registration:** ABLATION_PREREG.md.
- **Methods:** claim-only, evidence-aware, evidence-explicit, provenance gate (the label definition),
  semantic + gate.
- **Runs:** `ABL-claim-only-*` and `ABL-semantic-*` for GPT-4.1, Claude Sonnet 5.5 and Claude Sonnet 5.5 with
  thinking off (all complete).
- **Comparisons:**
  - A1: claim-only − aware, unauthorized approval with positive claims;
  - A2: aware − explicit, false rejection under the withdrawal claim;
  - A3: semantic+gate − explicit, false rejection on valid and control cells.

  | setting | A1 | A2 | A3 |
  |---|---|---|---|
  | GPT-4.1 | +40.2 | +82.6 | +77.3 |
  | Claude Sonnet 5.5 | +16.7 | 0 | +40.9 |
  | Claude Sonnet 5.5, thinking off | +14.2 | −0.8 | +61.0 |

  A3 is attributed to the semantic check's configuration: no trusted context, and alignment framing. It is
  not repeated on new cases.
- **Outputs:** `results/ablation-gpt-4.1/`, `results/ablation-claude-sonnet-5-5*/`,
  `results/E2-figures/png/fig_ablation_methods.png`, `fig_semantic_decisions.png`.

### Generalization (GPT-4.1 complete; Claude paused)

- **Pre-registration:** GENERALIZATION_PREREG.md (Amendments 1–3).
- **Units:** cases, not tasks.
- **Task sets:**
  - **New AuthorizationBench tasks:** 28 tasks in 8 cases. 7 of the cases are Experiment 1 cases in new domains,
    and 1 is new.
  - **AgentDojo:** 20 tasks. The primary set has 19 (Abank00 excluded, Amendment 3 item 4). Sensitivity sets:
    S-a (16 units) and S-b (17 cases).
- **Runs:**

  | run | calls | status |
  |---|---|---|
  | `G1-gpt-4.1-run1` | 9,744 | complete |
  | `G2E-gpt-4.1-run1` | 10,416 | complete |
  | `AD1-gpt-4.1-run1` | 6,960 | complete |
  | `AD2E-gpt-4.1-run1` | 7,440 | complete |
  | `GAB-claim-only-gpt-4.1-run1`, `GAB-semantic-gpt-4.1-run1`, `ADAB-claim-only-gpt-4.1-run1` | — | complete |
  | `GAB-claim-only-claude-sonnet-5-5-run1`, `ADAB-claim-only-claude-sonnet-5-5-run1` | — | complete |
  | `G1-claude-sonnet-5-5-run1` | 2,104 / 9,744 | **paused** (STOP file) |
  | `AD1-claude-sonnet-5-5-run1` | 1,276 / 6,960 | **paused** (STOP file) |
  | `ADAB-semantic-gpt-4.1-run1` | 0 | not run, by decision (Amendment 3) |

- **GPT-4.1 results:**

  | test | AB new tasks | AgentDojo |
  |---|---|---|
  | G1 (withdrawal on valid evidence) | −79.3 [−88.2, −67.5], Holm 0.016 | −85.5 [−92.5, −77.6], Holm < 0.001 |
  | G2 (positive claims on invalid evidence) | +0.7 | +1.9 [+1.2, +2.6] |
  | P1 (Experiment 2 cells) | −82.1 | −83.8 |
  | S5 (explicit instruction) | +95.2 | +94.2 |
  | ablation A1 | +43.6 | +25.6 |
  | ablation A2 | +79.5 | +87.1 |
  | ablation A3 | +78.2 | not run |

- **Outputs:**
  - `results/G1-*/analysis/GENERALIZATION.md`;
  - `results/AD1-gpt-4.1-run1/analysis/AGENTDOJO_SUBSETS.md`;
  - `results/ablation-gen-gpt-4.1/`, `results/ablation-ad-gpt-4.1/`;
  - `results/generalization-figures/`.

### Experiment 3: end-to-end delegation (paused)

- **Pre-registration:** EXPERIMENT3_E2E_PREREG.md.
  - Amendment 1 is in force.
  - Amendment 2 (task-success and violation measures for the six tasks without episodes) is **proposed and not
    committed**.
- **Design:** 11 tasks × 2 states × 3 claims × 6 methods × 2 repeats = 792 episodes. GPT-4.1 plays every role.
- **Run:** `E3-gpt-4.1-run1`: 301 finished plus 4 errored episodes (5 tasks), **paused** (STOP file).
  `E3-smoke*` and `E3-gpt-4.1-run1-dryrun` are environment checks, not data.
- **Checks, no API** (`results/E3-checks/`):
  - task success separated into L1 (tool call succeeded), L2 (state changed), L3 (user's task done) and
    benchmark violations V;
  - T0016: safe completion 12/36 but task success 3/36;
  - design audit: in 7 of 11 tasks no benchmark violation can register in the pre-registered measures.

### Planner × verifier 2×2 (draft, no runs; after the thesis)

- **Draft:** PLANNER_VERIFIER_2X2_PREREG_DRAFT.md. The decisions of 2026-11-18 are at its top.
- **Arms:**
  - M0: no planner advisory, evidence-aware verifier;
  - M1: no planner advisory, gate;
  - M2: planner advisory, evidence-aware verifier;
  - M3: planner advisory, gate.

  The planner advisory is an oracle: the gate's verdict on the benchmark's preselected target call. In M1 and M3,
  unauthorized gated execution is 0 by construction.
- **Code (0 API calls until approved):**
  - `experiments/run_planner_verifier_2x2.py`, `experiments/analyze_planner_verifier_2x2.py`,
    `src/hearsay/authbench/planner_guard.py`;
  - `configs/planner_verifier_2x2_template.json`: 5 Experiment 3 tasks, 360 episodes,
    `approved_for_run: false`;
  - `tests/test_planner_verifier_2x2.py`.

  The Experiment 3 runtime gained two hooks that are off by default (`planner_override`, `shadow`).
- **Open:**
  - the message-path experiment that separates planner and executor;
  - a safety evaluation independent of the gate;
  - independent tasks for confirmation;
  - the pilot go/no-go thresholds.

### Mitigation (draft, no runs)

- **Draft:** MITIGATION_PREREG.md, plan in MITIGATION_IMPLEMENTATION_PLAN.md.
- **Arms:** B0 aware and B1 explicit (existing runs) vs A (structured evidence-first reply), B (source
  separation) and A+B, as a 2 × 2 decomposition.
- **Models:** GPT-4.1, gpt-4.1-mini, Claude Sonnet 4.6. **Task sets:** 11 tasks for confirmation; AgentDojo as the
  independent test.
- **Order:** pilot first, with a go/no-go rule decided per model.
- **Open items:** the A and B texts, the non-inferiority margins and the pilot thresholds.
- **Power review:** `results/m-design/POWER_REVIEW.md`.

## Analyses on recorded data (no API calls)

| folder | what | note |
|---|---|---|
| `results/synthesis/` | **start here**: risk map, comparisons across task sets, models, policies and methods, four figures, five rule-selected cases (`experiments/synthesis.py`); EVIDENCE_MAP.md links each finding to its tests, numbers, limits, figures and sources (`experiments/evidence_map.py`) | mixes pre-registered and post-hoc results; each is tagged P, S, D or H |
| `results/error-stages/` | causes of incorrect decisions: two coders, kappa, adjudication | coders and adjudicator are Claude instances; consistency, not validity |
| `results/error-stages/human-check/` | blinded sheets for a person: 60 errors + 34 AgentDojo approvals | **not yet coded** |
| `results/invalid-approvals/` | where unauthorized approvals occur and what the reason cites | post hoc |
| `results/h3-completeness/` | why H3 reversed: the two completeness lines, by model and suite | post hoc |
| `results/E3-checks/` | E2E task success, violations, design audit | exploratory |
| `results/m-design/` | power review for the mitigation pre-registration | — |

## Built but not run

These datasets have no runs:
- `dataset/exp2_defer_gen`;
- `dataset/exp2_defer_ad`;
- `dataset/ablation_semantic_ad` (the AgentDojo semantic arm, which was not run by decision).
