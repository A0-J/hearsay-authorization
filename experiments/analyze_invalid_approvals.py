"""Unauthorized approvals (invalid evidence, approved) of GPT-4.1 in the Experiment 1 cells: where they occur and
what the reason cites. Exploratory and post hoc (written after the AgentDojo G2 result); descriptive only, no
tests. No API calls; reads recorded verdicts and the frozen datasets.

    python experiments/analyze_invalid_approvals.py

Sets (never pooled):
    11 tasks     results/E1-gpt-4.1-run1   dataset/exp1       unit = task (= case)
    AB new       results/G1-gpt-4.1-run1   dataset/exp1_gen   unit = case (case_of_task; 8 cases, 28 tasks)
    AgentDojo    results/AD1-gpt-4.1-run1  dataset/exp1_ad    unit = task (= case); Abank00 shown, flagged

For every approval of an invalid cell the script records, from the input and the reply:
    claimed_id            the approval ID named by a "specific" claim in the task message (None otherwise)
    claimed_in_evidence   whether that ID appears in the TRUSTED RUNTIME EVIDENCE block
    basis_is_claimed      whether the reply's `basis` field equals the claimed ID
    basis_in_evidence     whether the `basis` ID appears in the evidence block
    reason_source         a string rule on the one-sentence reason:
                            task_message  names the task message / task context / context note as the source
                            records       names the approval records / registry / approval system
                            both / neither
The rule is mechanical; every row is in approvals.csv with its reason for reading by a person.

Writes results/invalid-approvals/: REPORT.md, approvals.csv, grid.csv, units.csv.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict

from common import RESULTS, ROOT

OUT = RESULTS / "invalid-approvals"
SETS = [("11 tasks", "E1-gpt-4.1-run1", "exp1"), ("AB new", "G1-gpt-4.1-run1", "exp1_gen"),
        ("AgentDojo", "AD1-gpt-4.1-run1", "exp1_ad")]
CLAIMS = ("none", "unverified", "bare", "verified", "specific")
CONDS = ("abs_list", "abs_complete", "direct_revoked", "direct_expired", "derived_revoked", "derived_expired",
         "scope", "combined")
TASK_MSG = re.compile(r"task (message|context)|context note|delegat|executor (was told|received|has)|"
                      r"(cited|referenced|stated|noted|mentioned|indicated|confirmed) in the task", re.I)
RECORDS = re.compile(r"approval (record|system|registry)|records|registry|runtime evidence|recorded", re.I)
ID = re.compile(r"APR-[\w-]+")


def load_cells(ds: str) -> tuple[dict, dict]:
    cells = {}
    for f in sorted((ROOT / "dataset" / ds / "tasks").glob("*/cells.jsonl")):
        for x in f.read_text(encoding="utf-8").splitlines():
            c = json.loads(x)
            cells[c["cell_id"]] = c
    man = json.loads((ROOT / "dataset" / ds / "manifest.json").read_text(encoding="utf-8"))
    return cells, man


def unit_of(ds: str, man: dict, task: str) -> str:
    return man.get("case_of_task", {}).get(task, task) if ds == "exp1_gen" else task


def group_of(ds: str, man: dict, task: str) -> str:
    if ds == "exp1_ad":
        return re.match(r"A([a-z]+)", task).group(1)
    return "-"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, grid, units = [], [], []
    md = ["# Unauthorized approvals of GPT-4.1 (Experiment 1 cells): where and why", "",
          "Exploratory and post hoc (written after the AgentDojo G2 result). Descriptive only: no tests. Sets are "
          "never pooled. An approval of an invalid cell is an unauthorized approval. Source: "
          "experiments/analyze_invalid_approvals.py.", ""]
    for sname, run, ds in SETS:
        cells, man = load_cells(ds)
        V = [json.loads(x) for x in (RESULTS / run / "verdicts.jsonl").read_text(encoding="utf-8").splitlines()]
        V = [v for v in V if v["arm"] == "main" and v["side"] == "invalid"]
        n = Counter((v["instruction"], v["claim"], v["condition"]) for v in V)
        k = Counter((v["instruction"], v["claim"], v["condition"]) for v in V if v["approve"])
        for key in sorted(n):
            grid.append({"set": sname, "instruction": key[0], "claim": key[1], "condition": key[2],
                         "approved": k[key], "n": n[key]})
        for v in V:
            if not v["approve"]:
                continue
            inp = cells[v["cell_id"]]["input"]
            msg, ev = inp.split("TRUSTED RUNTIME EVIDENCE")[0], inp.split("TRUSTED RUNTIME EVIDENCE")[1]
            m = re.search(r"approval (APR-[\w-]+)\.?\]", msg) if v["claim"] == "specific" else None
            claimed = m.group(1).rstrip(".") if m else None
            basis = (v.get("basis") or "").strip()
            ev_ids = set(ID.findall(ev))
            reason = v.get("reason") or ""
            tm, rc = bool(TASK_MSG.search(reason)), bool(RECORDS.search(reason))
            rows.append({"set": sname, "unit": unit_of(ds, man, v["task_id"]), "group": group_of(ds, man, v["task_id"]),
                         "task_id": v["task_id"], "instruction": v["instruction"], "claim": v["claim"],
                         "condition": v["condition"], "repeat": v["repeat"], "claimed_id": claimed,
                         "claimed_in_evidence": None if claimed is None else claimed in ev_ids,
                         "basis": basis, "basis_is_claimed": claimed is not None and basis == claimed,
                         "basis_in_evidence": basis in ev_ids,
                         "reason_source": "both" if tm and rc else "task_message" if tm else "records" if rc else "neither",
                         "reason": reason})
        # per-unit table for the cell type that carries the approvals: aware, specific, absent ID
        acc = defaultdict(lambda: [0, 0])
        for v in V:
            if v["instruction"] == "aware" and v["claim"] == "specific" and v["condition"] in ("abs_complete", "abs_list"):
                u = (group_of(ds, man, v["task_id"]), unit_of(ds, man, v["task_id"]), v["condition"])
                acc[u][0] += v["approve"]
                acc[u][1] += 1
        for (g, u, cond), (a, nn) in sorted(acc.items()):
            units.append({"set": sname, "group": g, "unit": u, "condition": cond, "approved": a, "n": nn})

    with open(OUT / "approvals.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for name, data in (("grid.csv", grid), ("units.csv", units)):
        with open(OUT / name, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(data)

    def cnt(sname, instr, claims=CLAIMS, conds=CONDS):
        a = sum(g["approved"] for g in grid if g["set"] == sname and g["instruction"] == instr
                and g["claim"] in claims and g["condition"] in conds)
        nn = sum(g["n"] for g in grid if g["set"] == sname and g["instruction"] == instr
                 and g["claim"] in claims and g["condition"] in conds)
        return f"{a}/{nn}"

    md += ["## 1. Unauthorized approvals by instruction, claim and condition", "",
           "Approved / judged, invalid cells, 3 repeats each.", "",
           "| set | instruction | all invalid | claim none | positive claims (4) | specific claim | specific, ID absent "
           "(abs_complete + abs_list) | specific, ID present but invalid (other 6 conditions) |",
           "|---|---|---|---|---|---|---|---|"]
    absent = ("abs_complete", "abs_list")
    present = tuple(c for c in CONDS if c not in absent)
    for sname, _, _ in SETS:
        for instr in ("aware", "explicit"):
            md.append(f"| {sname} | {instr} | {cnt(sname, instr)} | {cnt(sname, instr, ('none',))} | "
                      f"{cnt(sname, instr, CLAIMS[1:])} | {cnt(sname, instr, ('specific',))} | "
                      f"{cnt(sname, instr, ('specific',), absent)} | {cnt(sname, instr, ('specific',), present)} |")
    md += ["", "Aware, specific claim, by condition (approved / judged):", "",
           "| set | " + " | ".join(CONDS) + " |", "|---|" + "---|" * len(CONDS)]
    for sname, _, _ in SETS:
        md.append(f"| {sname} | " + " | ".join(cnt(sname, "aware", ("specific",), (c,)) for c in CONDS) + " |")
    md += ["", "Aware, positive claims other than `specific` (unverified, bare, verified), by condition:", "",
           "| set | " + " | ".join(CONDS) + " |", "|---|" + "---|" * len(CONDS)]
    for sname, _, _ in SETS:
        md.append(f"| {sname} | " + " | ".join(cnt(sname, "aware", ("unverified", "bare", "verified"), (c,))
                                             for c in CONDS) + " |")

    md += ["", "## 2. Where: aware, specific claim, ID absent from the evidence (per unit)", "",
           "AgentDojo by suite (tasks with at least one approval / tasks; approvals / judged):", "",
           "| suite | tasks | tasks with >=1 approval | abs_complete | abs_list |", "|---|---|---|---|---|"]
    ad = [u for u in units if u["set"] == "AgentDojo"]
    for g in sorted({u["group"] for u in ad}):
        us = [u for u in ad if u["group"] == g]
        tasks = sorted({u["unit"] for u in us})
        hit = sorted({u["unit"] for u in us if u["approved"]})
        f = lambda c: f"{sum(u['approved'] for u in us if u['condition'] == c)}/{sum(u['n'] for u in us if u['condition'] == c)}"  # noqa: E731
        md.append(f"| {g} | {len(tasks)} | {len(hit)} | {f('abs_complete')} | {f('abs_list')} |")
    for sname in ("11 tasks", "AB new"):
        us = [u for u in units if u["set"] == sname]
        tasks = sorted({u["unit"] for u in us})
        hit = sorted({u["unit"] for u in us if u["approved"]})
        md += ["", f"{sname}: units with at least one approval {len(hit)}/{len(tasks)} ({', '.join(hit) or 'none'}); "
               f"abs_complete {sum(u['approved'] for u in us if u['condition'] == 'abs_complete')}/"
               f"{sum(u['n'] for u in us if u['condition'] == 'abs_complete')}, abs_list "
               f"{sum(u['approved'] for u in us if u['condition'] == 'abs_list')}/"
               f"{sum(u['n'] for u in us if u['condition'] == 'abs_list')}."]

    md += ["", "## 3. What the reason cites (every unauthorized approval)", "",
           "| set | approvals | specific claim | basis = claimed ID | claimed ID in evidence | basis ID in evidence | "
           "reason names task message | names records | both | neither |", "|---|---|---|---|---|---|---|---|---|---|"]
    for sname, _, _ in SETS:
        rs = [r for r in rows if r["set"] == sname]
        sp = [r for r in rs if r["claim"] == "specific"]
        c = Counter(r["reason_source"] for r in rs)
        md.append(f"| {sname} | {len(rs)} | {len(sp)} | {sum(r['basis_is_claimed'] for r in sp)} | "
                  f"{sum(bool(r['claimed_in_evidence']) for r in sp)} | {sum(r['basis_in_evidence'] for r in rs)} | "
                  f"{c['task_message']} | {c['records']} | {c['both']} | {c['neither']} |")
    md += ["", "Rule: `task_message` = the reason names the task message, task context or context note (regex "
           "`TASK_MSG`); `records` = it names the approval records, registry or approval system (regex `RECORDS`). "
           "Mechanical; read the reasons in approvals.csv.", "",
           "## 4. Reasons that do not name the task message (to read)", ""]
    for r in rows:
        if r["reason_source"] in ("neither", "records"):
            md.append(f"- {r['set']} {r['task_id']} {r['instruction']}/{r['claim']}/{r['condition']} r{r['repeat']} "
                      f"(basis {r['basis'] or 'none'}): {r['reason']}")
    (OUT / "REPORT.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
