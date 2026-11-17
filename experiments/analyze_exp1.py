"""Pre-registered analysis of Experiment 1 run 1 (docs/EXPERIMENT1_PREREG.md). No API calls.

    python experiments/analyze_exp1.py results/E1-gpt-4.1-run1

Unit = task. Each cell is averaged over its repeats per task; a contrast is a per-task difference;
the estimate is the mean over tasks, the 95% interval a bootstrap over tasks (10,000 resamples, seed 0)
and the p-value an exact sign-flip permutation test over tasks. H1-H3 are Holm-corrected as one family.
Writes results/<run>/analysis/: cell_rates.csv (per task), cell_summary.csv (over tasks), tests.json,
gee.txt, basis.csv, failures.jsonl, usage.json, plots/*.png, REPORT.md (tables only; no interpretation).
"""

from __future__ import annotations

import csv
import itertools
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

from common import ROOT

DATA = ROOT / "dataset" / "exp1"
INVALID = ("abs_list", "abs_complete", "direct_revoked", "direct_expired", "derived_revoked", "derived_expired",
           "scope", "combined")
VALID = ("direct", "derived", "scope", "combined")
POS = ("unverified", "bare", "verified", "specific")
DIRECT, INDIRECT = ("direct_revoked", "direct_expired"), ("derived_revoked", "derived_expired", "scope", "combined")
PRICE = {"gpt-4.1": (2.0, 8.0),             # USD per million input / output tokens (OpenAI list price, 2026-11)
         "claude-sonnet-5-5": (2.0, 10.0)}  # Anthropic list price (2026-11); no caching, no batch
INK, INK2, MUTED, SURFACE = "#0b0b0b", "#52514e", "#898781", "#fcfcfb"
# categorical slots of the reference palette, one fixed colour per claim in every chart (colour follows the entity)
CLAIM_COLOR = {"none": "#2a78d6", "bare": "#eb6834", "negative": "#1baf7a", "verified": "#eda100",
               "unverified": "#e87ba4", "specific": "#008300"}
SEQ = ["#fcfcfb", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def load(run: Path):
    verdicts = [json.loads(x) for x in (run / "verdicts.jsonl").read_text(encoding="utf-8").splitlines()]
    cfg = json.loads((run / "manifest.json").read_text(encoding="utf-8"))["config"]
    data = ROOT / "dataset" / cfg.get("dataset_dir", "exp1")      # exp1, or the generalization tasks' exp1_gen
    labels = {}
    for d in sorted((data / "tasks").iterdir()):
        for x in (d / "labels.jsonl").read_text(encoding="utf-8").splitlines():
            lab = json.loads(x)
            labels[lab["cell_id"]] = lab
    types = {d.name: json.loads((d / "spec.json").read_text(encoding="utf-8"))["task_type"]
             for d in (data / "tasks").iterdir()}
    return verdicts, labels, types


def rates(verdicts):
    acc = defaultdict(list)
    for v in verdicts:
        acc[(v["task_id"], v["arm"], v["instruction"], v["side"], v["condition"], v["claim"])].append(v["approve"])
    return {k: (mean(x), sum(x), len(x)) for k, x in acc.items()}


def stat(values: list[float], n_boot: int = 10000, seed: int = 0) -> dict:
    n = len(values)
    est = mean(values)
    rng = random.Random(seed)
    boots = sorted(mean(rng.choices(values, k=n)) for _ in range(n_boot))
    obs = abs(est)
    if all(abs(v) < 1e-12 for v in values):
        p = 1.0
    elif n <= 16:   # exact (every Experiment 1 analysis: 11 tasks)
        count = sum(1 for signs in itertools.product((1, -1), repeat=n)
                    if abs(sum(s * v for s, v in zip(signs, values)) / n) >= obs - 1e-12)
        p = count / 2 ** n
    else:           # more than 16 units (generalization): 100,000 random sign vectors, seed 0, as analyze_exp2.stat
        rs = random.Random(seed)
        hits = sum(1 for _ in range(100000)
                   if abs(sum(v if rs.random() < 0.5 else -v for v in values) / n) >= obs - 1e-12)
        p = (hits + 1) / 100001
    return {"estimate": round(est, 4), "ci95": [round(boots[int(0.025 * n_boot)], 4),
                                                round(boots[int(0.975 * n_boot) - 1], 4)],
            "p_signflip": round(p, 5), "n_tasks": n, "per_task": [round(v, 4) for v in values]}


def holm(ps: dict[str, float]) -> dict[str, float]:
    order = sorted(ps, key=ps.get)
    out, running = {}, 0.0
    for i, k in enumerate(order):
        running = max(running, min(1.0, ps[k] * (len(order) - i)))
        out[k] = round(running, 5)
    return out


def analysis(verdicts, labels, types):
    R = rates(verdicts)
    tasks = sorted({v["task_id"] for v in verdicts})

    def r(t, instr, side, cond, claim, arm="main"):
        return R[(t, arm, instr, side, cond, claim)][0]

    def delta(t, instr, cond, claims=POS):
        return mean(r(t, instr, "invalid", cond, c) for c in claims) - r(t, instr, "invalid", cond, "none")

    def h1(t, instr):
        return mean(delta(t, instr, c) for c in INVALID)

    tests = {
        "H1_positive_claims_raise_approval_invalid_aware": stat([h1(t, "aware") for t in tasks]),
        "H2_indirect_minus_direct_claim_effect_aware": stat(
            [mean(delta(t, "aware", c) for c in INDIRECT) - mean(delta(t, "aware", c) for c in DIRECT) for t in tasks]),
        "H3_abs_list_minus_abs_complete_claim_effect_aware": stat(
            [delta(t, "aware", "abs_list") - delta(t, "aware", "abs_complete") for t in tasks]),
    }
    adj = holm({k: v["p_signflip"] for k, v in tests.items()})
    for k in tests:
        tests[k]["p_holm"] = adj[k]
    sec = {}
    for instr in ("aware", "explicit"):
        for c in POS:
            sec[f"H4_claim_effect_{c}_{instr}"] = stat([mean(delta(t, instr, cond, (c,)) for cond in INVALID)
                                                       for t in tasks])
        sec[f"H4_verified_minus_bare_{instr}"] = stat(
            [mean(r(t, instr, "invalid", cond, "verified") - r(t, instr, "invalid", cond, "bare") for cond in INVALID)
             for t in tasks])
        sec[f"H4_bare_minus_unverified_{instr}"] = stat(
            [mean(r(t, instr, "invalid", cond, "bare") - r(t, instr, "invalid", cond, "unverified") for cond in INVALID)
             for t in tasks])
        sec[f"H5_negative_claim_effect_valid_{instr}"] = stat(
            [mean(r(t, instr, "valid", cond, "negative") - r(t, instr, "valid", cond, "none") for cond in VALID)
             for t in tasks])
        for c in ("unverified", "bare", "verified"):
            sec[f"H7_control_{c}_minus_none_{instr}"] = stat(
                [r(t, instr, "control", "not_required", c) - r(t, instr, "control", "not_required", "none")
                 for t in tasks])
        sec[f"claim_effect_pooled_invalid_{instr}"] = stat([h1(t, instr) for t in tasks])
        for cond in INVALID:
            sec[f"claim_effect_{cond}_{instr}"] = stat([delta(t, instr, cond) for t in tasks])
        sec[f"false_rejection_valid_none_{instr}"] = stat(
            [mean(1 - r(t, instr, "valid", cond, "none") for cond in VALID) for t in tasks])
    sec["H6_aware_minus_explicit_claim_effect"] = stat([h1(t, "aware") - h1(t, "explicit") for t in tasks])
    sec["H6_explicit_minus_aware_false_rejection_valid_none"] = stat(
        [mean((1 - r(t, "explicit", "valid", c, "none")) - (1 - r(t, "aware", "valid", c, "none")) for c in VALID)
         for t in tasks])
    for cond in ("abs_list", "direct_revoked"):
        sec[f"H8_pilot_format_specific_minus_none_{cond}"] = stat(
            [r(t, "aware_pilot_format", "invalid", cond, "specific", "pilot_format")
             - r(t, "aware_pilot_format", "invalid", cond, "none", "pilot_format") for t in tasks])
    by_type = defaultdict(list)
    for t in tasks:
        by_type[types[t]].append(round(h1(t, "aware"), 4))
    sec.update(amendment1(R, tasks))
    return R, tasks, tests, sec, dict(by_type)


def amendment1(R, tasks) -> dict:
    """Amendment 1 (docs/EXPERIMENT1_PREREG.md): claim-induced flips on evidence-competent cells only, and
    comprehension failures (no-claim decision wrong in at least one repeat) reported apart."""
    out = {}
    plan = (("invalid", INVALID, POS, lambda rate: rate),               # flip = approval
            ("valid", VALID, ("negative",), lambda rate: 1 - rate),     # flip = rejection
            ("control", ("not_required",), ("unverified", "bare", "verified"), lambda rate: 1 - rate))
    for instr in ("aware", "explicit"):
        for side, conds, claims, flip in plan:
            per_task, competent_n, failures_n = [], 0, 0
            for t in tasks:
                vals = []
                for cond in conds:
                    base = R[(t, "main", instr, side, cond, "none")][0]
                    correct = (base == 0.0) if side == "invalid" else (base == 1.0)
                    if not correct:
                        failures_n += 1
                        continue
                    competent_n += 1
                    vals += [flip(R[(t, "main", instr, side, cond, c)][0]) for c in claims]
                if vals:
                    per_task.append(mean(vals))
            key = f"A1_flip_rate_competent_{side}_{instr}"
            out[key] = {**stat(per_task), "competent_cells": competent_n,
                        "comprehension_failure_cells": failures_n} if per_task else {
                "estimate": None, "competent_cells": 0, "comprehension_failure_cells": failures_n}
    return out


def gee(verdicts) -> str:
    try:
        import pandas as pd
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
    except ImportError as e:
        return f"not fitted: {e}"
    group = {**{c: "absent" for c in ("abs_list", "abs_complete")}, **{c: "direct" for c in DIRECT},
             **{c: "indirect" for c in INDIRECT}}
    rows = [{"approve": int(v["approve"]), "claim": "none" if v["claim"] == "none" else "positive",
             "repr": group[v["condition"]], "task": v["task_id"]}
            for v in verdicts if v["arm"] == "main" and v["side"] == "invalid" and v["instruction"] == "aware"]
    df = pd.DataFrame(rows)
    try:
        model = smf.gee("approve ~ C(claim, Treatment('none')) * C(repr, Treatment('direct'))", "task", df,
                        family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable())
        return str(model.fit().summary())
    except Exception as e:   # noqa: BLE001  (e.g. perfect separation when a cell is all 0)
        return f"not fitted: {type(e).__name__}: {e}"


def plots(R, tasks, out: Path) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    import shutil
    shutil.rmtree(out, ignore_errors=True)          # no stale figures from an earlier analysis
    out.mkdir(parents=True)
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2,
                         "ytick.color": INK2, "text.color": INK, "figure.facecolor": SURFACE,
                         "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE})
    cmap = LinearSegmentedColormap.from_list("seq_blue", SEQ)
    claims = ("none",) + POS

    def cell_mean(instr, side, cond, claim, arm="main"):
        return mean(R[(t, arm, instr, side, cond, claim)][0] for t in tasks)

    files = []
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), constrained_layout=True)
    for ax, instr in zip(axes, ("aware", "explicit")):
        m = [[cell_mean(instr, "invalid", c, k) for k in claims] for c in INVALID]
        im = ax.imshow(m, cmap=cmap, vmin=0, vmax=1, aspect="auto")
        ax.set_xticks(range(len(claims)), claims)
        ax.set_yticks(range(len(INVALID)), INVALID)
        ax.set_title(f"Invalid evidence: approval rate ({instr})", color=INK, fontsize=10, loc="left")
        for i, row in enumerate(m):
            for j, v in enumerate(row):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8, color=INK if v < 0.55 else SURFACE)
        for s in ax.spines.values():
            s.set_visible(False)
    fig.colorbar(im, ax=axes, shrink=0.8, label="approval rate (mean over tasks; correct = 0)")
    fig.savefig(out / "invalid_approval_heatmap.png", dpi=160)
    plt.close(fig)
    files.append("invalid_approval_heatmap.png")

    def grouped(fname, title, groups, claims, getter, ylabel):
        fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
        width = 0.8 / len(claims)
        for ax, instr in zip(axes, ("aware", "explicit")):
            for j, claim in enumerate(claims):
                xs = [i + (j - (len(claims) - 1) / 2) * width for i in range(len(groups))]
                ys = [getter(instr, g, claim) for g in groups]
                bars = ax.bar(xs, ys, width=width * 0.92, color=CLAIM_COLOR[claim], label=claim, edgecolor=SURFACE,
                              linewidth=2)
                for b, y in zip(bars, ys):
                    ax.text(b.get_x() + b.get_width() / 2, y + 0.02, f"{y:.2f}", ha="center", fontsize=7, color=INK2)
            ax.set_xticks(range(len(groups)), groups)
            ax.set_ylim(0, 1.12)
            ax.set_title(instr, color=INK, fontsize=10, loc="left")
            ax.grid(axis="y", color="#e6e5e1", linewidth=0.6)
            ax.set_axisbelow(True)
            for sp in ("top", "right"):
                ax.spines[sp].set_visible(False)
        axes[0].set_ylabel(ylabel)
        fig.suptitle(title, x=0.01, ha="left", color=INK, fontsize=10)
        fig.legend(*axes[0].get_legend_handles_labels(), title="claim", frameon=False, ncol=len(claims),
                   loc="upper right", bbox_to_anchor=(0.99, 1.0))
        fig.tight_layout(rect=(0, 0, 1, 0.9))
        fig.savefig(out / fname, dpi=160)
        plt.close(fig)
        files.append(fname)

    grouped("valid_approval.png", "Valid evidence: approval rate (mean over tasks; correct = 1)", list(VALID),
            ("none", "bare", "negative"), lambda instr, g, c: cell_mean(instr, "valid", g, c), "approval rate")
    grouped("control_approval.png", "Not-required control: approval rate (mean over tasks; correct = 1)",
            ["not_required"], ("none", "unverified", "bare", "verified"),
            lambda instr, g, c: cell_mean(instr, "control", g, c), "approval rate")

    fig, ax = plt.subplots(figsize=(6, 3.4), constrained_layout=True)
    conds = ("abs_list", "direct_revoked")
    for j, claim in enumerate(("none", "specific")):
        ys = [cell_mean("aware_pilot_format", "invalid", c, claim, "pilot_format") for c in conds]
        xs = [i + (j - 0.5) * 0.3 for i in range(len(conds))]
        bars = ax.bar(xs, ys, width=0.28, color=CLAIM_COLOR[claim], label=claim, edgecolor=SURFACE, linewidth=2)
        for b, y in zip(bars, ys):
            ax.text(b.get_x() + b.get_width() / 2, y + 0.02, f"{y:.2f}", ha="center", fontsize=8, color=INK2)
    ax.set_xticks(range(len(conds)), ["abs_list (pilot 'fabricated')", "direct_revoked (pilot 'revoked')"])
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("approval rate (correct = 0)")
    ax.set_title("Pilot-format replication arm", color=INK, fontsize=10, loc="left")
    ax.legend(title="claim", frameon=False)
    ax.grid(axis="y", color="#e6e5e1", linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.savefig(out / "pilot_format_replication.png", dpi=160)
    plt.close(fig)
    files.append("pilot_format_replication.png")
    return files


def main() -> None:
    run = Path(sys.argv[1]).resolve()
    out = run / "analysis"
    out.mkdir(exist_ok=True)
    verdicts, labels, types = load(run)
    R, tasks, tests, sec, by_type = analysis(verdicts, labels, types)

    with open(out / "cell_rates.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["task_id", "task_type", "arm", "instruction", "side", "condition", "claim", "approvals", "n", "rate"])
        for (t, arm, instr, side, cond, claim), (rate, k, n) in sorted(R.items()):
            w.writerow([t, types[t], arm, instr, side, cond, claim, k, n, round(rate, 4)])
    summary = defaultdict(list)
    for (t, arm, instr, side, cond, claim), (rate, _, _) in R.items():
        summary[(arm, instr, side, cond, claim)].append(rate)
    with open(out / "cell_summary.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["arm", "instruction", "side", "condition", "claim", "mean_approval_over_tasks", "min", "max",
                    "n_tasks"])
        for k, v in sorted(summary.items()):
            w.writerow([*k, round(mean(v), 4), round(min(v), 4), round(max(v), 4), len(v)])

    failures, parse_errors = [], Counter()
    basis = Counter()
    for v in verdicts:
        lab = labels[v["cell_id"]]
        expected = lab["expected"] == "approve"
        if v.get("parse_error"):
            parse_errors[v["parse_error"][:40]] += 1
        if v["approve"] != expected:
            failures.append({k: v[k] for k in ("cell_id", "repeat", "task_id", "arm", "instruction", "side",
                                                "condition", "claim", "decision", "basis", "reason")})
        if v["approve"] and v["arm"] == "main":
            if v["side"] == "valid":
                basis[("valid_approved", "correct" if v.get("basis") == lab["covering_approval_id"] else
                       f"other:{v.get('basis')}")] += 1
            elif v["side"] == "invalid":
                b = str(v.get("basis"))
                kind = ("cited_record_0417" if b.endswith("-0417") else "narrow_0418" if b.endswith("-0418")
                        else "unauthorized_0419" if b.endswith("-0419") else "background" if b.endswith(("-0101", "-0102"))
                        else "none" if b.lower() in ("none", "null", "") else "other")
                basis[("invalid_approved", f"{v['condition']}|{kind}")] += 1
    with open(out / "failures.jsonl", "w", encoding="utf-8") as f:
        for x in failures:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    with open(out / "basis.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["group", "basis", "count"])
        for (g, b), n in sorted(basis.items()):
            w.writerow([g, b, n])
    tin = sum(v["usage"].get("input_tokens", 0) for v in verdicts)
    tout = sum(v["usage"].get("output_tokens", 0) for v in verdicts)
    model = verdicts[0].get("served_model") or ""
    price = next((p for k, p in PRICE.items() if model.startswith(k)), None)
    usage = {"calls": len(verdicts), "input_tokens": tin, "output_tokens": tout, "served_models": dict(
        Counter(v.get("served_model") for v in verdicts)), "estimated_cost_usd":
        round(tin / 1e6 * price[0] + tout / 1e6 * price[1], 3) if price else None,
        "parse_errors": dict(parse_errors)}
    (out / "usage.json").write_text(json.dumps(usage, indent=2) + "\n", encoding="utf-8")
    (out / "tests.json").write_text(json.dumps({"primary": tests, "secondary": sec, "h1_by_task_type": by_type},
                                               indent=2) + "\n", encoding="utf-8")
    (out / "gee.txt").write_text(gee(verdicts) + "\n", encoding="utf-8")
    files = plots(R, tasks, out / "plots")

    def row(name, s):
        if s.get("estimate") is None:
            return f"| {name} | (no competent cells) | | | |"
        extra = (f" competent {s['competent_cells']}, comprehension failures {s['comprehension_failure_cells']}"
                 if "competent_cells" in s else "")
        return (f"| {name} | {s['estimate']:+.4f} | [{s['ci95'][0]:+.4f}, {s['ci95'][1]:+.4f}] | {s['p_signflip']:.4f}"
                + (f" | {s['p_holm']:.4f} |" if "p_holm" in s else f" |{extra} |"))

    lines = ["# Experiment 1 run 1: results", "", f"Run: `{run.name}`. Pre-registration: docs/EXPERIMENT1_PREREG.md "
             "(commit e5fb9fd). Tables only.", "",
             f"Calls {usage['calls']}; input tokens {tin}; output tokens {tout}; estimated cost "
             f"${usage['estimated_cost_usd']}; parse errors {sum(parse_errors.values())}; served models "
             f"{usage['served_models']}.", "", f"Tasks (n = {len(tasks)}): " + ", ".join(tasks), "",
             "## Primary tests (evidence-aware, invalid evidence; unit = task)", "",
             "| test | estimate | 95% CI (bootstrap over tasks) | p (exact sign-flip) | p (Holm, H1-H3) |",
             "|---|---|---|---|---|"]
    lines += [row(k, v) for k, v in tests.items()]
    lines += ["", "## Secondary tests", "", "| test | estimate | 95% CI | p (sign-flip) | |", "|---|---|---|---|---|"]
    lines += [row(k, v) for k, v in sec.items()]
    lines += ["", "## Claim effect on invalid evidence by task type (evidence-aware, per-task values)", "",
              "| task type | per-task values |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in sorted(by_type.items())]
    lines += ["", "## Mean approval rate over tasks, main arm", "",
              "| instruction | side | condition | " + " | ".join(("none",) + POS + ("negative",)) + " |",
              "|---|---|---|" + "---|" * 6]
    for instr in ("aware", "explicit"):
        for side, conds in (("invalid", INVALID), ("valid", VALID), ("control", ("not_required",))):
            for cond in conds:
                cells = []
                for claim in ("none",) + POS + ("negative",):
                    v = summary.get(("main", instr, side, cond, claim))
                    cells.append(f"{mean(v):.3f}" if v else "")
                lines.append(f"| {instr} | {side} | {cond} | " + " | ".join(cells) + " |")
    lines += ["", "## Pilot-format replication arm (mean approval over tasks)", "",
              "| condition | none | specific |", "|---|---|---|"]
    for cond in ("abs_list", "direct_revoked"):
        lines.append(f"| {cond} | {mean(summary[('pilot_format', 'aware_pilot_format', 'invalid', cond, 'none')]):.3f} | "
                     f"{mean(summary[('pilot_format', 'aware_pilot_format', 'invalid', cond, 'specific')]):.3f} |")
    fail_by = Counter((x["arm"], x["instruction"], x["side"], x["condition"], x["claim"]) for x in failures)
    lines += ["", f"## Incorrect decisions ({len(failures)} of {len(verdicts)} calls; all in failures.jsonl)", "",
              "| arm | instruction | side | condition | claim | count |", "|---|---|---|---|---|---|"]
    lines += [f"| {' | '.join(k)} | {n} |" for k, n in sorted(fail_by.items())]
    lines += ["", "## Basis cited (main arm approvals)", "", "| group | basis | count |", "|---|---|---|"]
    lines += [f"| {g} | {b} | {n} |" for (g, b), n in sorted(basis.items())]
    lines += ["", "## Files", "", "cell_rates.csv, cell_summary.csv, tests.json, gee.txt, basis.csv, failures.jsonl, "
              "usage.json, plots/: " + ", ".join(files)]
    (out / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"-> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
