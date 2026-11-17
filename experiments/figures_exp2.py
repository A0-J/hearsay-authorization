"""Figures (PNG) for Experiment 2, the DEFER arm, the ablation and the semantic check, regenerated from recorded
verdicts and analysis outputs. No API calls.

    python experiments/figures_exp2.py

Writes results/E2-figures/: png/*.png, tables/*.csv (the values behind each figure) and INDEX.md. Settings are
never pooled: one panel per setting. Conventions follow analyze_exp1: a cell's rate is averaged over its repeats
(and, where stated, over pooled factors) per task; the task is the unit; a rate is the mean over tasks; its 95%
interval is a bootstrap over tasks (10,000 resamples, seed 0; analyze_exp1.stat).
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

from common import ROOT

from analyze_exp1 import CLAIM_COLOR, INK, INK2, MUTED, stat

OUT = ROOT / "results" / "E2-figures"
WHITE, GRID = "#ffffff", "#e6e5e1"
SETTINGS = [("gpt-4.1", "GPT-4.1"), ("claude-sonnet-5-5", "Claude Sonnet 5.5 (adaptive)"),
            ("claude-sonnet-5-5-nothink", "Claude Sonnet 5.5 (between_tools)")]
# colour follows the entity: claims keep Experiment 1's slots (approved = positive 'bare' slot, withdrawn = the
# negative slot); decisions use slots not used for any claim in these figures (violet, yellow) plus neutral grey
COL = {"none": CLAIM_COLOR["none"], "approved": CLAIM_COLOR["bare"], "withdrawn": CLAIM_COLOR["negative"]}
DEC = {"approve": "#6250d6", "defer": "#eda100", "reject": "#b4b2ac"}
SEM = {"aligned": DEC["approve"], "uncertain": DEC["defer"], "not_aligned": DEC["reject"]}


def jl(p: Path):
    return [json.loads(x) for x in open(p, encoding="utf-8")]


def labels(dataset: str) -> dict:
    out = {}
    for p in (ROOT / "dataset" / dataset / "tasks").glob("*/labels.jsonl"):
        for r in jl(p):
            out[r["cell_id"]] = r
    return out


def style(plt):
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2,
                         "ytick.color": INK2, "text.color": INK, "figure.facecolor": WHITE, "axes.facecolor": WHITE,
                         "savefig.facecolor": WHITE, "hatch.linewidth": 0.8, "legend.frameon": False})


def clean(ax, grid="y"):
    ax.grid(axis=grid, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def caption(fig, text: str, width: int = 175):
    import textwrap
    fig.text(0.01, 0.005, "\n".join(textwrap.wrap(text, width)), fontsize=7, color=INK2, va="bottom")


def task_rates(rows, key, value):
    """{group: {task: mean(value)}}"""
    acc = defaultdict(lambda: defaultdict(list))
    for r in rows:
        k = key(r)
        if k is not None:
            acc[k][r["task_id"]].append(value(r))
    return {k: {t: mean(v) for t, v in d.items()} for k, d in acc.items()}


def write_csv(path: Path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


# --- Fig 1: Experiment 2 block B, valid evidence: approval by claim x timing x policy ---------------------------

TIMING = [("unspecified", "claim:\nno time"), ("before", "claim at\n09:00"), ("after", "claim at\n11:00")]


def fig_exp2_valid(plt, instruction: str, index: list):
    lab = labels("exp2")
    fig, axes = plt.subplots(2, 3, figsize=(11.5, 6.4), sharey=True)
    table = []
    for j, (s, name) in enumerate(SETTINGS):
        rows = [r for r in jl(ROOT / "results" / f"E2-{s}-run1" / "verdicts.jsonl")
                if r["block"] == "B" and r["side"] == "valid" and r["instruction"] == instruction]
        tr = task_rates(rows, lambda r: (r["policy"], r["claim"], r["timing"]), lambda r: float(r.get("approve") is True))
        norm = {}
        for r in rows:
            norm[(r["policy"], r["claim"], r["timing"])] = lab[r["cell_id"]]["normative"]
        for i, pol in enumerate(("base", "record_authority")):
            ax = axes[i][j]
            xs, ticks = [], []
            x = 0.0
            groups = [("none", [("none", None)])] + [(t, [("approved", t), ("withdrawn", t)]) for t, _ in TIMING]
            for gname, bars in groups:
                start = x
                for claim, timing in bars:
                    k = (pol, claim, timing if timing else next(iter({kk[2] for kk in tr if kk[:2] == (pol, "none")}), "-"))
                    if k not in tr:
                        x += 0.8
                        continue
                    st = stat(list(tr[k].values()))
                    est, (lo, hi) = st["estimate"], st["ci95"]
                    ax.bar(x, 100 * est, width=0.72, color=COL[claim], edgecolor=WHITE, linewidth=1.5)
                    ax.errorbar(x, 100 * est, yerr=[[100 * (est - lo)], [100 * (hi - est)]], fmt="none",
                                ecolor=INK2, elinewidth=0.9, capsize=2)
                    ax.text(x, 100 * hi + 2, f"{100 * est:.0f}", ha="center", va="bottom", fontsize=6.5,
                            color=INK2)
                    nv = norm.get(k)
                    mark = {"approve": 100, "reject": 0}.get(nv)
                    if mark is not None:
                        ax.scatter([x], [mark], marker="D", s=26, facecolor=WHITE, edgecolor=INK, linewidth=1.3,
                                   zorder=4, clip_on=False)
                    else:
                        ax.text(x, 109, "n/d", ha="center", va="bottom", fontsize=6.5, color=INK2)
                    table.append([name, instruction, pol, claim, k[2], round(est, 4), lo, hi, st["n_tasks"], nv])
                    x += 0.8
                xs.append((start + x - 0.8) / 2)
                ticks.append("no claim" if gname == "none" else dict(TIMING)[gname])
                x += 0.5
            ax.set_xticks(xs)
            ax.set_xticklabels(ticks, fontsize=7.5)
            ax.set_ylim(0, 112)
            ax.set_yticks([0, 25, 50, 75, 100])
            clean(ax)
            if j == 0:
                ax.set_ylabel(f"policy: {'base' if pol == 'base' else 'record authority'}\napproval on valid evidence (%)")
            if i == 0:
                ax.set_title(name, loc="left", fontsize=10, color=INK)
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    handles = [Patch(facecolor=COL[c], label=lab_) for c, lab_ in
               (("none", "no claim"), ("approved", "claim: approved"), ("withdrawn", "claim: approval withdrawn"))]
    handles.append(Line2D([], [], marker="D", linestyle="", markersize=5, markerfacecolor=WHITE, markeredgecolor=INK,
                          label="normative decision (at 100 = approve, at 0 = reject)"))
    fig.legend(handles=handles, loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.0), fontsize=8.5)
    caption(fig, f"Experiment 2 block B, valid evidence: an active covering approval in a complete snapshot taken at "
            f"10:00; current time 11:30. Evidence-{instruction} instruction. Source of the claim pooled (supervisor, "
            "upstream agent). Bars: mean over 11 tasks, value above; whiskers: 95% bootstrap CI over tasks. n/d = the "
            "policy does not settle the cell (no normative decision).")
    fig.tight_layout(rect=(0, 0.05, 1, 0.94))
    name = f"fig_e2_valid_approval_{instruction}.png"
    fig.savefig(OUT / "png" / name, dpi=200)
    plt.close(fig)
    write_csv(OUT / "tables" / name.replace(".png", ".csv"),
              ["setting", "instruction", "policy", "claim", "timing", "approval_rate", "ci95_low", "ci95_high", "n_tasks",
               "normative"], table)
    index.append((f"png/{name}", f"Experiment 2 block B, valid evidence, evidence-{instruction}: approval rate by claim "
                  "(none / approved / withdrawn) x claim time x policy, one panel per setting; normative decision "
                  "marked", "E2-*-run1 (3 settings)", "11 tasks; per bar 6 calls per task (2 sources x 3 repeats); "
                  "no-claim bar 3 per task"))


# --- Fig 2: pre-registered tests, forest -------------------------------------------------------------------

TESTS = [("primary", "P1_negative_claim_valid_blockA_aware", "P1  withdrawal note, valid, block A (aware)"),
         ("primary", "P2_before_minus_after_valid_withdrawn_base_aware", "P2  withdrawn 09:00 − 11:00 (base, aware)"),
         ("secondary", "S1_asymmetry_withdrawal_drop_minus_approval_rise_unspecified", "S1  withdrawal drop − approval rise"),
         ("secondary", "S2_before_minus_unspecified", "S2  withdrawn 09:00 − no time"),
         ("secondary", "S3_supervisor_minus_upstream_agent", "S3  supervisor − upstream agent"),
         ("secondary", "S4_record_authority_minus_base_unspecified", "S4  record-authority − base policy"),
         ("secondary", "S5_explicit_minus_aware_unspecified", "S5  explicit − aware instruction"),
         ("secondary", "S6_record_authority_before_minus_after", "S6  record-authority: 09:00 − 11:00")]


def fig_tests(plt, index: list):
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2), sharey=True, gridspec_kw={"wspace": 0.28})
    table = []
    for j, (s, name) in enumerate(SETTINGS):
        t = json.loads((ROOT / "results" / f"E2-{s}-run1" / "analysis" / "tests.json").read_text(encoding="utf-8"))
        ax = axes[j]
        for i, (fam, key, lab_) in enumerate(TESTS):
            v = t[fam][key]
            y = len(TESTS) - 1 - i
            est, (lo, hi), ph = v["estimate"], v["ci95"], v.get("p_holm")
            sig = ph is not None and ph < 0.05
            ax.plot([100 * lo, 100 * hi], [y, y], color=INK2, linewidth=1.2)
            ax.scatter([100 * est], [y], s=36, zorder=3, color=INK if sig else WHITE, edgecolor=INK, linewidth=1.2)
            ax.text(1.02, y, f"{100 * est:+.1f}", va="center", fontsize=7.5, color=INK2,
                    transform=ax.get_yaxis_transform(), clip_on=False)
            table.append([name, key, est, lo, hi, v.get("p_signflip"), ph, v.get("n_tasks")])
        ax.axvline(0, color=MUTED, linewidth=0.8)
        ax.set_xlim(-105, 105)
        ax.set_xticks([-100, -50, 0, 50, 100])
        ax.set_yticks(range(len(TESTS)))
        ax.set_yticklabels([x[2] for x in reversed(TESTS)], fontsize=8)
        ax.set_xlabel("difference in approval rate (pp)")
        ax.set_title(name, loc="left", fontsize=10, color=INK)
        clean(ax, grid="x")
    caption(fig, "Pre-registered tests (docs/EXPERIMENT2_PREREG.md). Point: mean over 11 tasks of the per-task "
            "contrast (value at right); line: 95% bootstrap CI. Filled: Holm-adjusted p < 0.05 within its family "
            "(P1-P2; S1-S6); hollow: not.")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(OUT / "png" / "fig_e2_tests_forest.png", dpi=200)
    plt.close(fig)
    write_csv(OUT / "tables" / "fig_e2_tests_forest.csv",
              ["setting", "test", "estimate", "ci95_low", "ci95_high", "p_signflip", "p_holm", "n_tasks"], table)
    index.append(("png/fig_e2_tests_forest.png", "Experiment 2 pre-registered tests P1-P2 and S1-S6: estimate and "
                  "95% CI per setting; filled = Holm p < 0.05", "E2-*-run1 analysis/tests.json", "11 tasks"))


# --- Fig 3: DEFER arm decision distribution ----------------------------------------------------------------

STATES = [("fresh_valid", "fresh, valid"), ("fresh_invalid", "fresh, revoked"), ("stale_valid", "stale (06:00), valid"),
          ("lookup_failed", "lookup failed")]
DCLAIMS = [("none", "none"), ("approved", "approved"), ("withdrawn_after", "withdr.\n11:00"),
           ("withdrawn_unspecified", "withdr.\nno time")]


def fig_defer(plt, instruction: str, index: list):
    lab = labels("exp2_defer")
    fig, axes = plt.subplots(3, 1, figsize=(11.5, 8.6), sharex=True)
    table = []
    for j, (s, name) in enumerate(SETTINGS):
        rows = [r for r in jl(ROOT / "results" / f"E2D-{s}-run1" / "verdicts.jsonl") if r["instruction"] == instruction]
        ax = axes[j]
        x, xt, xl = 0.0, [], []
        for st_key, st_name in STATES:
            for c_key, c_name in DCLAIMS:
                sel = [r for r in rows if r["condition"] == st_key and r["claim"] == c_key]
                if not sel:
                    continue
                bottom = 0.0
                for d in ("approve", "defer", "reject"):
                    tr = task_rates(sel, lambda r: 0, lambda r, d=d: float(r.get("decision") == d))[0]
                    v = mean(tr.values())
                    ax.bar(x, 100 * v, bottom=100 * bottom, width=0.8, color=DEC[d], edgecolor=WHITE, linewidth=1)
                    bottom += v
                    table.append([name, instruction, st_key, c_key, d, round(v, 4), len(tr)])
                if bottom < 0.999:   # no parseable decision
                    ax.bar(x, 100 * (1 - bottom), bottom=100 * bottom, width=0.8, color=WHITE, edgecolor=MUTED,
                           hatch="////", linewidth=0.6)
                nv = lab[sel[0]["cell_id"]]["normative"]
                ax.text(x, 102, {"approve": "A", "reject": "R", "defer": "D"}.get(nv, "–"), ha="center",
                        va="bottom", fontsize=8, color=INK, fontweight="bold")
                xt.append(x)
                xl.append(c_name)
                x += 1
            ax.plot([x - 3.9, x - 0.1], [116, 116], color=MUTED, linewidth=0.8, clip_on=False)
            ax.text(x - 2.0, 118, st_name, ha="center", va="bottom", fontsize=8.5, color=INK, clip_on=False)
            x += 0.8
        ax.set_ylim(0, 112)
        ax.set_yticks([0, 50, 100])
        ax.set_ylabel("decisions (%)")
        ax.set_title(name, loc="left", fontsize=10, color=INK, pad=22)
        ax.set_xticks(xt)
        ax.set_xticklabels(xl, fontsize=7)
        ax.tick_params(axis="x", labelbottom=True)
        clean(ax)
    from matplotlib.patches import Patch
    handles = [Patch(facecolor=DEC[d], label=d) for d in ("approve", "defer", "reject")]
    handles.append(Patch(facecolor=WHITE, edgecolor=MUTED, hatch="////", label="no parseable decision"))
    fig.legend(handles=handles, loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.0), fontsize=8.5)
    caption(fig, f"DEFER arm (exploratory; docs/EXPERIMENT2_DEFER_PREREG.md), {instruction}. Letter above each bar: "
            "normative decision (A approve, R reject, D defer). Share of decisions, mean over 11 tasks (3 repeats per "
            "task). Evidence state above each group: fresh = 10:00 snapshot, stale = 06:00 snapshot, current time 11:30.")
    fig.tight_layout(rect=(0, 0.04, 1, 0.96), h_pad=3.2)
    name = f"fig_defer_decisions_{instruction}.png"
    fig.savefig(OUT / "png" / name, dpi=200)
    plt.close(fig)
    write_csv(OUT / "tables" / name.replace(".png", ".csv"),
              ["setting", "instruction", "state", "claim", "decision", "share", "n_tasks"], table)
    index.append((f"png/{name}", f"DEFER arm, {instruction}: share of approve / defer / reject by evidence state x "
                  "claim, one panel per setting; normative decision lettered", "E2D-*-run1 (3 settings)",
                  "11 tasks x 3 repeats per bar"))


# --- Fig 4: ablation ----------------------------------------------------------------------------------------

METHODS = [("claim_only", "claim only"), ("aware", "evidence-aware"), ("explicit", "evidence-explicit"),
           ("gate", "provenance gate"), ("semantic_gate", "semantic + gate")]
MEASURES = [("invalid", "unauthorized_approval", "unauthorized approval\n(invalid evidence, %)"),
            ("valid", "false_rejection", "false rejection\n(valid evidence, %)"),
            ("control", "false_rejection", "false rejection\n(no approval needed, %)")]


def fig_ablation(plt, index: list):
    fig, axes = plt.subplots(3, 3, figsize=(11.5, 7.4), sharey=True)
    table = []
    for j, (s, name) in enumerate(SETTINGS):
        rows = list(csv.DictReader(open(ROOT / "results" / f"ablation-{s}" / "method_table.csv", encoding="utf-8")))
        for i, (side, meas, ylab) in enumerate(MEASURES):
            ax = axes[i][j]
            for k, (m, mname) in enumerate(METHODS):
                r = next(x for x in rows if x["method"] == m and x["side"] == side and x["measure"] == meas
                         and x["claim"] == "(all)")
                est, lo, hi = (float(r[c]) for c in ("rate_mean_over_tasks", "ci95_low", "ci95_high"))
                ax.bar(k, 100 * est, width=0.7, color=WHITE if m == "gate" else INK2,
                       edgecolor=INK2, hatch="////" if m == "gate" else None, linewidth=0.8)
                ax.errorbar(k, 100 * est, yerr=[[100 * (est - lo)], [100 * (hi - est)]], fmt="none", ecolor=INK,
                            elinewidth=0.9, capsize=2)
                ax.text(k, 100 * hi + 3, f"{100 * est:.0f}", ha="center", va="bottom", fontsize=7, color=INK2)
                table.append([name, m, side, meas, est, lo, hi, r["n_tasks"]])
            ax.set_xticks(range(len(METHODS)))
            ax.set_xticklabels([x[1] for x in METHODS], fontsize=7, rotation=25, ha="right")
            ax.set_ylim(0, 118)
            ax.set_yticks([0, 50, 100])
            clean(ax)
            if j == 0:
                ax.set_ylabel(ylab, fontsize=8)
            if i == 0:
                ax.set_title(name, loc="left", fontsize=10, color=INK)
    caption(fig, "Ablation (docs/ABLATION_PREREG.md), Experiment 1's main-arm cells, all claims pooled. Mean over 11 "
            "tasks (value above), 95% bootstrap CI. Hatched: the provenance gate defines the labels, so its zero is by "
            "construction, not a finding. The semantic check had no task context (trusted context \"(none)\").")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(OUT / "png" / "fig_ablation_methods.png", dpi=200)
    plt.close(fig)
    write_csv(OUT / "tables" / "fig_ablation_methods.csv",
              ["setting", "method", "side", "measure", "rate", "ci95_low", "ci95_high", "n_tasks"], table)
    index.append(("png/fig_ablation_methods.png", "Ablation: unauthorized approval and false rejection (valid, "
                  "control) per verification method, one column per setting", "ablation-* (3 settings)", "11 tasks"))


# --- Fig 5: semantic check decisions --------------------------------------------------------------------------

SEM_RUNS = [("ABL-semantic-gpt-4.1-run1", "GPT-4.1, 11 tasks"),
            ("ABL-semantic-claude-sonnet-5-5-run1", "Claude adaptive, 11 tasks"),
            ("ABL-semantic-claude-sonnet-5-5-nothink-run1", "Claude between_tools, 11 tasks"),
            ("GAB-semantic-gpt-4.1-run1", "GPT-4.1, 28 new AB tasks")]


def fig_semantic(plt, index: list):
    fig, ax = plt.subplots(figsize=(10, 4.2))
    table, y, yt, yl = [], 0, [], []
    for run, name in SEM_RUNS:
        rows = jl(ROOT / "results" / run / "verdicts.jsonl")
        for side, sname in (("call", "gated call"), ("control", "status message (no approval needed)")):
            sel = [r for r in rows if r["side"] == side]
            left = 0.0
            for d in ("aligned", "uncertain", "not_aligned"):
                tr = task_rates(sel, lambda r: 0, lambda r, d=d: float(r.get("decision") == d))[0]
                v = mean(tr.values())
                ax.barh(y, 100 * v, left=100 * left, height=0.7, color=SEM[d], edgecolor=WHITE, linewidth=1)
                if v >= 0.06:
                    ax.text(100 * (left + v / 2), y, f"{100 * v:.0f}", ha="center", va="center", fontsize=7,
                            color=WHITE if d == "aligned" else INK)
                left += v
                table.append([name, side, d, round(v, 4), len(tr)])
            yt.append(y)
            yl.append(f"{name}\n{sname}")
            y -= 1
        y -= 0.5
    ax.set_yticks(yt)
    ax.set_yticklabels(yl, fontsize=7.5)
    ax.set_xlim(0, 100)
    ax.set_xlabel("semantic-check votes (%)")
    clean(ax, grid="x")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=SEM[d], label=d.replace("_", " ")) for d in ("aligned", "uncertain", "not_aligned")],
              loc="upper center", bbox_to_anchor=(0.5, 1.12), ncol=3, fontsize=8)
    caption(fig, "Semantic check of the ablation (Experiment A's semantic text, trusted context \"(none)\"). Both "
            "inputs are legitimate; only \"aligned\" passes. Share of votes, mean over tasks (9 votes per input per "
            "task).", width=140)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(OUT / "png" / "fig_semantic_decisions.png", dpi=200)
    plt.close(fig)
    write_csv(OUT / "tables" / "fig_semantic_decisions.csv", ["run", "input", "decision", "share", "n_tasks"], table)
    index.append(("png/fig_semantic_decisions.png", "Semantic check votes (aligned / uncertain / not aligned) on the "
                  "gated call and on the not-required status message", "ABL-semantic-* (3 settings), "
                  "GAB-semantic-gpt-4.1-run1", "11 or 28 tasks, 9 votes per input per task"))


def main() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    style(plt)
    (OUT / "png").mkdir(parents=True, exist_ok=True)
    index: list = []
    fig_exp2_valid(plt, "aware", index)
    fig_exp2_valid(plt, "explicit", index)
    fig_tests(plt, index)
    fig_defer(plt, "aware_tristate", index)
    fig_defer(plt, "explicit_tristate", index)
    fig_ablation(plt, index)
    fig_semantic(plt, index)
    md = ["# Experiment 2, DEFER, ablation and semantic check: figures", "",
          "Generated by `experiments/figures_exp2.py` from recorded verdicts and analysis outputs (no API calls). "
          "One panel per setting; settings are never pooled. Values behind each figure are in tables/.", "",
          "| file | what it shows | runs | n |", "|---|---|---|---|"]
    md += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in index]
    (OUT / "INDEX.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
