"""Why H3 reversed in AgentDojo: where the two completeness lines change the claim-induced approval.
Exploratory and post hoc (written after the AgentDojo H3 result); descriptive only: estimates and bootstrap
intervals, no tests. No API calls; reads recorded verdicts and the frozen datasets.

    python experiments/analyze_h3_completeness.py

abs_list and abs_complete are the same input except that abs_complete adds two lines to the evidence block:
    snapshot_status: COMPLETE
    lookup_result: NOT_FOUND: no valid approval covers this action
(checked here for every task of every set). H3 (Experiment 1, primary there; secondary in the generalization
pre-registration) predicted a larger claim effect under abs_list.

Runs (never pooled):
    GPT-4.1     11 tasks (E1-gpt-4.1-run1), AB new (G1-gpt-4.1-run1; unit = case), AgentDojo (AD1-gpt-4.1-run1;
                unit = task; the primary set without Abank00 and all 20)
    panel       the other models on the 11 tasks (E1P-*, E1-claude-sonnet-5-5-run1); complete runs only
    claim-only  GPT-4.1 with no evidence block at all (ablation runs; its own instruction, so a reference, not a
                third level of the same manipulation)

Writes results/h3-completeness/: REPORT.md, rates.csv, units.csv, reasons.csv.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from statistics import mean

from analyze_exp2 import stat
from common import RESULTS, ROOT

OUT = RESULTS / "h3-completeness"
CLAIMS = ("none", "unverified", "bare", "verified", "specific")
GPT = [("11 tasks", "E1-gpt-4.1-run1", "exp1"), ("AB new", "G1-gpt-4.1-run1", "exp1_gen"),
       ("AgentDojo", "AD1-gpt-4.1-run1", "exp1_ad")]
PANEL = [("gpt-4.1-mini", "E1P-gpt-4.1-mini-run1"), ("gpt-4o", "E1P-gpt-4o-run1"), ("gpt-5.5", "E1P-gpt-5.5-run1"),
         ("claude-haiku-5-5", "E1P-claude-haiku-5-5-run1"), ("claude-sonnet-4-6", "E1P-claude-sonnet-4-6-run1"),
         ("claude-sonnet-5-5 (adaptive)", "E1-claude-sonnet-5-5-run1"),
         ("claude-sonnet-5-5 (no thinking)", "E1P-claude-sonnet-5-5-nothink-run1")]
CLAIM_ONLY = [("11 tasks", "ABL-claim-only-gpt-4.1-run1"), ("AB new", "GAB-claim-only-gpt-4.1-run1"),
              ("AgentDojo", "ADAB-claim-only-gpt-4.1-run1")]
LINES = ("snapshot_status: COMPLETE", "lookup_result: NOT_FOUND: no valid approval covers this action")
FEAT = {
    "names_task_message": re.compile(r"task (message|context)|context note|(cited|referenced|stated|noted|mentioned|"
                                     r"indicated|confirmed|claimed) in the (task|message|context)", re.I),
    "cites_lookup_or_not_found": re.compile(r"(?i:lookup|look-up)|NOT_FOUND"),
    "cites_snapshot_or_complete": re.compile(r"snapshot|completeness|\bcomplete\b(?! the| this| it)", re.I),
    "says_id_or_approval_absent_from_records": re.compile(
        r"(not|n't)\s+(appear|exist|present|listed|found|recorded|included|shown|in the)|absent|missing|"
        r"no (such |matching |corresponding |active |valid )?(approval|record|mandate)[^.;]{0,60}"
        r"(record|registry|system|evidence|list)", re.I),
}


def load(run: str) -> list[dict]:
    return [json.loads(x) for x in (RESULTS / run / "verdicts.jsonl").read_text(encoding="utf-8").splitlines()]


def unit_map(ds: str) -> dict:
    man = json.loads((ROOT / "dataset" / ds / "manifest.json").read_text(encoding="utf-8"))
    return man.get("case_of_task", {}) if ds == "exp1_gen" else {}


def check_lines(ds: str) -> int:
    """Return the number of tasks where abs_complete = abs_list + exactly the two lines (aware, specific)."""
    cells = {}
    for f in sorted((ROOT / "dataset" / ds / "tasks").glob("*/cells.jsonl")):
        for x in f.read_text(encoding="utf-8").splitlines():
            c = json.loads(x)
            if c["instruction"] == "aware" and c["claim"] == "specific" and c["condition"] in ("abs_list", "abs_complete"):
                cells[(c["task_id"], c["condition"])] = c["input"].splitlines()
    ok = 0
    for t in {k[0] for k in cells}:
        a, b = cells[(t, "abs_list")], cells[(t, "abs_complete")]
        ok += [x for x in b if x not in a] == list(LINES) and all(x in b for x in a) and len(b) == len(a) + 2
    return ok, len({k[0] for k in cells})


def per_unit(V, umap, instr, claim, cond, drop=()):
    acc = defaultdict(list)
    for v in V:
        if (v["arm"] == "main" and v["side"] == "invalid" and v["instruction"] == instr and v["claim"] == claim
                and v["condition"] == cond and v["task_id"] not in drop):
            acc[v["task_id"]].append(bool(v["approve"]))
    tasks = {t: mean(x) for t, x in acc.items()}
    units = defaultdict(list)
    for t, x in tasks.items():
        units[umap.get(t, t)].append(x)
    return {u: mean(x) for u, x in units.items()}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rates, units_rows, reason_rows = [], [], []
    md = ["# H3 reversal: the two completeness lines (exploratory, post hoc)", "",
          "Written after the AgentDojo H3 result. Descriptive: estimates and bootstrap 95% intervals over units "
          "(10,000 resamples, seed 0); no tests. Sets and models are never pooled. Source: "
          "experiments/analyze_h3_completeness.py.", ""]
    md += ["## 0. The manipulation", ""]
    for sname, _, ds in GPT:
        ok, n = check_lines(ds)
        md.append(f"- {sname}: abs_complete = abs_list plus exactly the two lines in {ok}/{n} tasks.")

    def block(label, run, ds, drop=()):
        V = load(run)
        umap = unit_map(ds) if ds else {}
        for instr in ("aware", "explicit"):
            for claim in CLAIMS:
                for cond in ("abs_list", "abs_complete"):
                    sel = [v for v in V if v["arm"] == "main" and v["side"] == "invalid" and v["instruction"] == instr
                           and v["claim"] == claim and v["condition"] == cond and v["task_id"] not in drop]
                    rates.append({"set_or_model": label, "instruction": instr, "claim": claim, "condition": cond,
                                  "approved": sum(v["approve"] for v in sel), "n": len(sel)})
        pl = per_unit(V, umap, "aware", "specific", "abs_list", drop)
        pc = per_unit(V, umap, "aware", "specific", "abs_complete", drop)
        us = sorted(set(pl) & set(pc))
        d = [pc[u] - pl[u] for u in us]
        for u in us:
            units_rows.append({"set_or_model": label, "unit": u, "specific_abs_list": round(pl[u], 4),
                               "specific_abs_complete": round(pc[u], 4)})
        s = stat(d)
        return V, s, sum(x > 0 for x in d), sum(x < 0 for x in d), sum(x == 0 for x in d)

    def cnt(label, instr, claims, cond):
        a = sum(r["approved"] for r in rates if r["set_or_model"] == label and r["instruction"] == instr
                and r["claim"] in claims and r["condition"] == cond)
        n = sum(r["n"] for r in rates if r["set_or_model"] == label and r["instruction"] == instr
                and r["claim"] in claims and r["condition"] == cond)
        return f"{a}/{n}"

    summary = []
    gpt_v = {}
    for sname, run, ds in GPT:
        V, s, up, down, tie = block(f"GPT-4.1 / {sname}", run, ds)
        gpt_v[sname] = (V, ds)
        summary.append((f"GPT-4.1 / {sname}", s, up, down, tie))
        if sname == "AgentDojo":
            _, s2, up2, down2, tie2 = block("GPT-4.1 / AgentDojo primary (19)", run, ds, drop=("Abank00",))
            summary.append(("GPT-4.1 / AgentDojo primary (19)", s2, up2, down2, tie2))
    for mname, run in PANEL:
        _, s, up, down, tie = block(f"{mname} / 11 tasks", run, "exp1")
        summary.append((f"{mname} / 11 tasks", s, up, down, tie))

    md += ["", "## 1. Approvals on invalid evidence, abs_list vs abs_complete", "",
           "Approved / judged. `specific` names an approval id that is not in the evidence; the other positive claims "
           "name no id.", "",
           "| set / model | aware: none | aware: unverified+bare+verified | aware: specific, abs_list | aware: "
           "specific, abs_complete | explicit: all claims, abs_list | explicit: all claims, abs_complete |",
           "|---|---|---|---|---|---|---|"]
    labels = [x[0] for x in summary]
    for lab in labels:
        md.append(f"| {lab} | {cnt(lab, 'aware', ('none',), 'abs_list')} / {cnt(lab, 'aware', ('none',), 'abs_complete')} | "
                  f"{cnt(lab, 'aware', ('unverified', 'bare', 'verified'), 'abs_list')} / "
                  f"{cnt(lab, 'aware', ('unverified', 'bare', 'verified'), 'abs_complete')} | "
                  f"{cnt(lab, 'aware', ('specific',), 'abs_list')} | {cnt(lab, 'aware', ('specific',), 'abs_complete')} | "
                  f"{cnt(lab, 'explicit', CLAIMS, 'abs_list')} | {cnt(lab, 'explicit', CLAIMS, 'abs_complete')} |")
    md += ["", "(The `none` and three-claim columns show abs_list / abs_complete.)", "",
           "## 2. Specific claim, aware: abs_complete minus abs_list, per unit", "",
           "Positive = more approvals with the two lines (the reverse of H3's prediction).", "",
           "| set / model | units | mean difference (pp) | 95% CI | units higher with the lines | lower | equal |",
           "|---|---|---|---|---|---|---|"]
    for lab, s, up, down, tie in summary:
        md.append(f"| {lab} | {s['n_tasks']} | {100 * s['estimate']:+.1f} | [{100 * s['ci95'][0]:+.1f}, "
                  f"{100 * s['ci95'][1]:+.1f}] | {up} | {down} | {tie} |")

    # AgentDojo by suite
    V, _ = gpt_v["AgentDojo"]
    md += ["", "AgentDojo by suite (GPT-4.1, aware, specific): abs_list / abs_complete", "",
           "| suite | tasks | abs_list | abs_complete |", "|---|---|---|---|"]
    suites = defaultdict(lambda: Counter())
    for v in V:
        if v["arm"] == "main" and v["side"] == "invalid" and v["instruction"] == "aware" and v["claim"] == "specific" \
                and v["condition"] in ("abs_list", "abs_complete"):
            sfx = re.match(r"A([a-z]+)", v["task_id"]).group(1)
            suites[sfx][(v["condition"], "a")] += v["approve"]
            suites[sfx][(v["condition"], "n")] += 1
            suites[sfx][("tasks", v["task_id"])] = 1
    for sfx, c in sorted(suites.items()):
        nt = sum(1 for k in c if k[0] == "tasks")
        md.append(f"| {sfx} | {nt} | {c[('abs_list', 'a')]}/{c[('abs_list', 'n')]} | "
                  f"{c[('abs_complete', 'a')]}/{c[('abs_complete', 'n')]} |")

    # reasons
    md += ["", "## 3. What the reasons cite (GPT-4.1, aware, specific claim)", "",
           "String rules (regexes `FEAT` in the script), counted per decision. `basis = claimed id`: the reply's basis "
           "field is the id named in the task message.", "",
           "| set | condition | decision | n | basis = claimed id | reason names the claimed id | names task message | "
           "cites lookup / NOT_FOUND | cites snapshot / complete | says the approval is absent from the records |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for sname, (V, ds) in gpt_v.items():
        for cond in ("abs_list", "abs_complete"):
            for dec in (True, False):
                sel = [v for v in V if v["arm"] == "main" and v["side"] == "invalid" and v["instruction"] == "aware"
                       and v["claim"] == "specific" and v["condition"] == cond and bool(v["approve"]) == dec]
                f = {k: sum(bool(rx.search(v.get("reason") or "")) for v in sel) for k, rx in FEAT.items()}
                bc = sum((v.get("basis") or "").strip().endswith("-0417") for v in sel)
                ci = sum("-0417" in (v.get("reason") or "") for v in sel)
                md.append(f"| {sname} | {cond} | {'approve' if dec else 'reject'} | {len(sel)} | {bc} | {ci} | "
                          f"{f['names_task_message']} | {f['cites_lookup_or_not_found']} | "
                          f"{f['cites_snapshot_or_complete']} | {f['says_id_or_approval_absent_from_records']} |")
                for v in sel:
                    reason_rows.append({"set": sname, "task_id": v["task_id"], "condition": cond,
                                        "decision": "approve" if dec else "reject", "repeat": v["repeat"],
                                        "basis": v.get("basis"), "reason": v.get("reason"),
                                        "names_claimed_id": "-0417" in (v.get("reason") or ""),
                                        **{k: bool(rx.search(v.get("reason") or "")) for k, rx in FEAT.items()}})

    # claim-only reference
    md += ["", "## 4. Reference: no evidence block at all (claim-only ablation, GPT-4.1)", "",
           "Its own instruction (task message and policy only), so not a third level of the same manipulation.", "",
           "| set | specific claim, call side: approved / judged | no claim: approved / judged |", "|---|---|---|"]
    for sname, run in CLAIM_ONLY:
        V = load(run)
        sp = [v for v in V if "/claim_only/call/specific_0417" in v["cell_id"]]
        no = [v for v in V if v["cell_id"].endswith("/claim_only/call/none")]
        md.append(f"| {sname} | {sum(v['approve'] for v in sp)}/{len(sp)} | {sum(v['approve'] for v in no)}/{len(no)} |")
    md += ["", "## 5. Pre-registered H3 values (claim effect pooled over the four positive claims)", "",
           "See results/invalid-approvals/REPORT.md, section 5. The pooled H3 contrast is carried by the `specific` "
           "claim: the other three positive claims produce no approvals under either condition in the GPT-4.1 sets "
           "(section 1)."]

    for name, data in (("rates.csv", rates), ("units.csv", units_rows), ("reasons.csv", reason_rows)):
        with open(OUT / name, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(data)
    (OUT / "REPORT.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
