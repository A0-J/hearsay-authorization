"""Figure (PNG): GPT-4.1 on the 11 Experiment 1 tasks vs the new AuthorizationBench tasks vs the AgentDojo cases,
from the analysis outputs already written. No API calls.

    python experiments/figures_gen.py

Writes results/generalization-figures/: png/fig_gen_gpt41_comparison.png, tables/fig_gen_gpt41_comparison.csv and
INDEX.md. Task sets are never pooled; each row shows the three sets side by side with its own unit:
    11 tasks           Experiment 1 / Experiment 2 runs (unit = task; each task is its own case)
    AB new (8 cases)   G1/G2: case level (analyze_gen.py); Experiment 2 tests: task level over 28 tasks
                       (7 of the 8 cases are Experiment 1's cases in new domains; 1 new case)
    AgentDojo (19)     the primary set of Amendment 3 item 4 (Abank00 excluded), case = task
"""

from __future__ import annotations

import csv
import json

from common import RESULTS

OUT = RESULTS / "generalization-figures"
INK, INK2, MUTED, WHITE, GRID = "#0b0b0b", "#52514e", "#898781", "#ffffff", "#e6e5e1"
SETS = [("11 tasks", "#2a78d6", "o"), ("AB new tasks", "#eb6834", "s"), ("AgentDojo, 19 cases", "#1baf7a", "D")]


def j(p):
    return json.loads((RESULTS / p).read_text(encoding="utf-8"))


def main() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    e1, e2 = j("E1-gpt-4.1-run1/analysis/tests.json"), j("E2-gpt-4.1-run1/analysis/tests.json")
    g1, g2e = j("G1-gpt-4.1-run1/analysis/generalization_tests.json"), j("G2E-gpt-4.1-run1/analysis/tests.json")
    ad1, ad2 = j("AD1-gpt-4.1-run1/analysis/agentdojo_subsets.json"), j("AD2E-gpt-4.1-run1/analysis/agentdojo_subsets.json")
    p = lambda t, k: t["primary"].get(k) or t["secondary"].get(k)  # noqa: E731
    rows = [
        ("Withdrawal note, valid evidence\n(E1 H5 / G1; aware)",
         [e1["secondary"]["H5_negative_claim_effect_valid_aware"], g1["primary_case_level"]["G1_negative_claim_valid_aware"],
          ad1["primary"]["G1"]]),
        ("Positive claims, invalid evidence\n(E1 H1 / G2; aware)",
         [e1["primary"]["H1_positive_claims_raise_approval_invalid_aware"],
          g1["primary_case_level"]["G2_positive_claims_invalid_aware"], ad1["primary"]["G2"]]),
        ("P1  withdrawal note, valid, E2 block A",
         [p(e2, "P1_negative_claim_valid_blockA_aware"), p(g2e, "P1_negative_claim_valid_blockA_aware"),
          ad2["primary"]["P1_negative_claim_valid_blockA_aware"]]),
        ("P2  withdrawn 09:00 − 11:00 (base)",
         [p(e2, "P2_before_minus_after_valid_withdrawn_base_aware"), p(g2e, "P2_before_minus_after_valid_withdrawn_base_aware"),
          ad2["primary"]["P2_before_minus_after_valid_withdrawn_base_aware"]]),
        ("S5  explicit − aware instruction",
         [p(e2, "S5_explicit_minus_aware_unspecified"), p(g2e, "S5_explicit_minus_aware_unspecified"),
          ad2["primary"]["S5_explicit_minus_aware_unspecified"]]),
        ("S6  record-authority: 09:00 − 11:00",
         [p(e2, "S6_record_authority_before_minus_after"), p(g2e, "S6_record_authority_before_minus_after"),
          ad2["primary"]["S6_record_authority_before_minus_after"]]),
    ]
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2,
                         "ytick.color": INK2, "text.color": INK, "legend.frameon": False})
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    table = []
    for i, (label, vals) in enumerate(rows):
        y0 = len(rows) - 1 - i
        for k, ((sname, col, mk), v) in enumerate(zip(SETS, vals)):
            y = y0 + 0.22 - 0.22 * k
            est, (lo, hi) = v["estimate"], v["ci95"]
            ax.plot([100 * lo, 100 * hi], [y, y], color=col, linewidth=1.4)
            ax.scatter([100 * est], [y], s=30, marker=mk, color=col, edgecolor=WHITE, linewidth=0.6, zorder=3)
            ax.text(1.01, y, f"{100 * est:+.1f}", transform=ax.get_yaxis_transform(), va="center", fontsize=7,
                    color=INK2, clip_on=False)
            table.append([label.replace("\n", " "), sname, est, lo, hi, v.get("p_signflip"),
                          v.get("p_holm", v.get("p_holm_primary_pair")), v.get("n_tasks")])
    ax.axvline(0, color=MUTED, linewidth=0.8)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in reversed(rows)], fontsize=8)
    ax.set_xlim(-105, 105)
    ax.set_xlabel("difference in approval rate (percentage points)")
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(handles=[Line2D([], [], color=c, marker=m, linestyle="-", label=n) for n, c, m in SETS],
              loc="upper center", bbox_to_anchor=(0.45, 1.1), ncol=3, fontsize=8)
    import textwrap
    fig.text(0.01, 0.005, "\n".join(textwrap.wrap(
        "GPT-4.1, evidence-aware unless stated. Point: mean contrast; line: 95% bootstrap CI. Units: 11 tasks = 11 "
        "cases; AB new = 8 cases for the first two rows (7 are Experiment 1 cases in new domains) and 28 tasks for the "
        "Experiment 2 rows; AgentDojo = 19 cases (Abank00 excluded, Amendment 3). Sets are not pooled.", 150)),
        fontsize=7, color=INK2, va="bottom")
    fig.tight_layout(rect=(0, 0.07, 0.97, 1))
    (OUT / "png").mkdir(parents=True, exist_ok=True)
    (OUT / "tables").mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "png" / "fig_gen_gpt41_comparison.png", dpi=200)
    with open(OUT / "tables" / "fig_gen_gpt41_comparison.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["test", "set", "estimate", "ci95_low", "ci95_high", "p_signflip", "p_holm", "units"])
        w.writerows(table)
    (OUT / "INDEX.md").write_text(
        "# Generalization figures\n\n| file | what it shows |\n|---|---|\n| png/fig_gen_gpt41_comparison.png | GPT-4.1: "
        "the main contrasts on the 11 tasks, the new AuthorizationBench tasks and the AgentDojo primary set, side by "
        "side (values in tables/) |\n", encoding="utf-8")
    print("ok")


if __name__ == "__main__":
    main()
