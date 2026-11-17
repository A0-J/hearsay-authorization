"""Sample-size and power review for the mitigation pre-registration (docs/MITIGATION_PREREG.md), from runs
already recorded. No API calls. It informs, but does not set, the non-inferiority margin: the researcher fixes the
margin after reading this report and before any confirmatory mitigation data.

    python experiments/m_power_review.py

Per model and task set it computes, per task (11 tasks) or per case (AgentDojo primary set, 19 cases):
    FA     false-allow rate: approval on invalid cells, all claims (aware = B0, explicit = B1)
    FD0    false-denial rate without claims: 1 - approval on valid and control cells with claim none
    Dneg   claim effect on valid evidence: approval(valid, negative) - approval(valid, none), mean over the 4
           valid conditions (the H5 / P1 contrast; negative = claim-induced false rejection)
The variability of a between-arm difference is approximated by the B1 - B0 difference per unit (two prompts on
the same cells). The margin that a non-inferiority test can support is estimated two ways:
    normal approximation  delta = (z_0.975 + z_power) * sd(d) / sqrt(n)
    bootstrap simulation  resample units of d centred at 0; the 95% bootstrap CI upper bound (10,000 resamples per
                          simulated study is replaced by 2,000 for speed) must fall below delta in >= 80% / 90% of
                          2,000 simulated studies
Writes results/m-design/POWER_REVIEW.md and power_review.json.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from statistics import mean, pstdev

import numpy as np

from common import RESULTS

OUT = RESULTS / "m-design"
RUNS = [("GPT-4.1", "11 tasks", "E1-gpt-4.1-run1"), ("GPT-4.1-mini", "11 tasks", "E1P-gpt-4.1-mini-run1"),
        ("Claude Sonnet 4.6", "11 tasks", "E1P-claude-sonnet-4-6-run1"),
        ("GPT-4.1", "AgentDojo primary (19)", "AD1-gpt-4.1-run1")]
PRICES = {"gpt-4.1": (2.0, 8.0), "gpt-4.1-mini": (0.4, 1.6), "claude-sonnet-4-6": (3.0, 15.0)}  # USD per M tokens


def per_unit(V, instr):
    fa, fd0, dneg = defaultdict(list), defaultdict(list), defaultdict(lambda: defaultdict(list))
    for v in V:
        if v["arm"] != "main" or v["instruction"] != instr or v["task_id"] == "Abank00":
            continue
        t, a = v["task_id"], bool(v["approve"])
        if v["side"] == "invalid":
            fa[t].append(a)
        if v["side"] in ("valid", "control") and v["claim"] == "none":
            fd0[t].append(not a)
        if v["side"] == "valid" and v["claim"] in ("none", "negative"):
            dneg[t][(v["condition"], v["claim"])].append(a)
    d = {t: mean(mean(c[(cond, "negative")]) - mean(c[(cond, "none")])
                 for cond in {k[0] for k in c}) for t, c in dneg.items()}
    return ({t: mean(x) for t, x in fa.items()}, {t: mean(x) for t, x in fd0.items()}, d)


def sim_margin(d, power, n_sim=2000, n_boot=2000, seed=0):
    rng = np.random.default_rng(seed)
    d = np.asarray(d, float)
    d0 = d - d.mean()
    n = len(d0)
    if np.allclose(d0, 0):
        return 0.0
    uppers = np.empty(n_sim)
    for s in range(n_sim):
        sample = rng.choice(d0, n, replace=True)
        boots = rng.choice(sample, (n_boot, n), replace=True).mean(axis=1)
        uppers[s] = np.quantile(boots, 0.975)
    return float(np.quantile(uppers, power))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    res, md = {}, ["# Power review for the mitigation pre-registration (from recorded runs; no API calls)", "",
                   "Informs, does not set, the non-inferiority margin. Source: experiments/m_power_review.py. B0 = "
                   "evidence-aware, B1 = evidence-explicit, same cells. d = B1 - B0 per unit approximates the "
                   "variability of a between-arm difference; the mitigation arms may vary more or less, so the pilot's "
                   "own A+B - B0 differences are to be checked before the margin is fixed.", "",
                   "## Rates by arm (mean over units, %)", "",
                   "| model | set | units | FA B0 | FA B1 | FD0 B0 | FD0 B1 | Dneg B0 (pp) | Dneg B1 (pp) | units with Dneg B0 < 0 |",
                   "|---|---|---|---|---|---|---|---|---|---|"]
    rows2 = ["", "## Margin a non-inferiority test can support (pp)", "",
             "Smallest margin delta for which the planned test (two-sided 95% bootstrap CI upper bound of the A+B - B0 "
             "difference below delta) would succeed with the stated probability if the true difference were 0, "
             "taking the spread of d = B1 - B0 as the spread of the A+B - B0 difference.", "",
             "| model | set | measure | sd(d) pp | normal 80% | normal 90% | bootstrap 80% | bootstrap 90% |",
             "|---|---|---|---|---|---|---|---|"]
    for model, tset, run in RUNS:
        V = [json.loads(x) for x in (RESULTS / run / "verdicts.jsonl").read_text(encoding="utf-8").splitlines()]
        fa0, fd00, dn0 = per_unit(V, "aware")
        fa1, fd01, dn1 = per_unit(V, "explicit")
        units = sorted(fa0)
        n = len(units)
        r = {"units": n}
        md.append(f"| {model} | {tset} | {n} | {100 * mean(fa0.values()):.2f} | {100 * mean(fa1.values()):.2f} | "
                  f"{100 * mean(fd00.values()):.2f} | {100 * mean(fd01.values()):.2f} | {100 * mean(dn0.values()):+.1f} | "
                  f"{100 * mean(dn1.values()):+.1f} | {sum(dn0[t] < 0 for t in units)}/{n} |")
        for name, a0, a1 in (("FA", fa0, fa1), ("FD0", fd00, fd01)):
            d = [100 * (a1[t] - a0[t]) for t in units]
            sd = pstdev(d) * math.sqrt(n / (n - 1)) if n > 1 else 0.0
            nm80 = (1.96 + 0.8416) * sd / math.sqrt(n)
            nm90 = (1.96 + 1.2816) * sd / math.sqrt(n)
            b80, b90 = sim_margin(d, 0.8), sim_margin(d, 0.9)
            r[name] = {"sd_d_pp": sd, "normal80": nm80, "normal90": nm90, "boot80": b80, "boot90": b90,
                       "per_unit_d_pp": dict(zip(units, d))}
            rows2.append(f"| {model} | {tset} | {name} | {sd:.2f} | {nm80:.2f} | {nm90:.2f} | {b80:.2f} | {b90:.2f} |")
        r["Dneg_B0_pp"] = {t: 100 * dn0[t] for t in units}
        r["Dneg_B1_pp"] = {t: 100 * dn1[t] for t in units}
        res[f"{model} | {tset}"] = r
    md += rows2
    md += ["", "## Resolution", "",
           "11 tasks: an invalid-side rate per task rests on 40 cells x 3 repeats = 120 decisions (one decision = "
           "0.83 pp); a valid no-claim rate on 4 cells x 3 = 12 decisions plus 1 control cell x 3. AgentDojo: per "
           "case 40 invalid cells x 3 = 120 decisions. The sign-flip test over 11 units has a smallest two-sided p "
           "of 2/2048 = 0.00098; over 19 units it is far smaller (Monte Carlo).", "",
           "## Cost per call in the base runs (list prices, from recorded tokens)", "",
           "| run | calls | input tokens/call | output tokens/call | USD/call |", "|---|---|---|---|---|"]
    for model, tset, run in RUNS:
        u = json.loads((RESULTS / run / "analysis" / "usage.json").read_text(encoding="utf-8"))
        key = {"GPT-4.1": "gpt-4.1", "GPT-4.1-mini": "gpt-4.1-mini", "Claude Sonnet 4.6": "claude-sonnet-4-6"}[model]
        pi, po = PRICES[key]
        c = u["calls"]
        usd = (u["input_tokens"] * pi + u["output_tokens"] * po) / 1e6
        md.append(f"| {run} | {c} | {u['input_tokens'] / c:.0f} | {u['output_tokens'] / c:.0f} | {usd / c:.5f} |")
        res[f"{model} | {tset}"]["usd_per_call"] = usd / c
    md += ["", "Note: the recorded `estimated_cost_usd` of E1P-gpt-4.1-mini-run1 (7.314) is computed at GPT-4.1 prices; "
           "at gpt-4.1-mini list prices the run cost about $1.46."]
    (OUT / "power_review.json").write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    (OUT / "POWER_REVIEW.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
