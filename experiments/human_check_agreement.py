"""Agreement of the human check with the final model codes (analysis fixed in
results/error-stages/human-check/README.md before any human code). No API calls.

    python experiments/human_check_agreement.py

Reads human-check/sheet_errors.csv (+ key.csv) and coded_final.csv; optionally sheet_ad_approvals.csv.
Writes human-check/REPORT_human.md and human_agreement.json. Refuses to run on an empty sheet.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter

from common import RESULTS
from error_coding_agreement import kappa

ES = RESULTS / "error-stages"
OUT = ES / "human-check"
DIMS = ("evidence_reading", "reason_conclusion", "driver", "timing_misread")
ALLOWED = {"evidence_reading": {"correct", "incorrect", "not_stated"},
           "reason_conclusion": {"supports_normative", "supports_actual", "cannot_establish", "none"},
           "driver": {"claim", "policy_misapplied", "evidence_misread", "uncertainty", "inconsistent", "other"},
           "timing_misread": {"yes", "no"}}


def stage(ev: str, rc: str, drv: str) -> str:
    if rc == "supports_normative":
        return "reason_decision_mismatch"
    if ev == "incorrect":
        return "evidence_misread"
    if ev == "correct":
        return "read_correctly_decided_wrong"
    return "claim_without_reading" if drv == "claim" else "not_stated_other"


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    z, p = 1.959964, k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (round(c - h, 3), round(c + h, 3))


def main() -> None:
    sheet = list(csv.DictReader(open(OUT / "sheet_errors.csv", encoding="utf-8")))
    key = {r["hc_id"]: r["row_id"] for r in csv.DictReader(open(OUT / "key.csv", encoding="utf-8"))}
    final = {r["row_id"]: r for r in csv.DictReader(open(ES / "coded_final.csv", encoding="utf-8"))}
    done = [r for r in sheet if all((r[f"h_{d}"] or "").strip() for d in DIMS)]
    if not done:
        raise SystemExit("sheet_errors.csv has no completed rows yet")
    bad = [(r["hc_id"], d, r[f"h_{d}"]) for r in done for d in DIMS if r[f"h_{d}"].strip() not in ALLOWED[d]]
    if bad:
        raise SystemExit(f"values outside the codebook: {bad[:10]}")
    pairs = []
    for r in done:
        f = final[key[r["hc_id"]]]
        h = {d: r[f"h_{d}"].strip() for d in DIMS}
        m = {"evidence_reading": f["evidence_reading"], "reason_conclusion": f["reason_conclusion"],
             "driver": f["final_driver"],
             "timing_misread": "yes" if "yes" in (f["timing_misread_A"], f["timing_misread_B"]) else "no"}
        h["stage"], m["stage"] = stage(h["evidence_reading"], h["reason_conclusion"], h["driver"]), f["final_stage"]
        pairs.append((r["experiment"], r["setting"], h, m))
    res = {"n_sheet": len(sheet), "n_completed": len(done), "missing": len(sheet) - len(done), "agreement": {}}
    for scope in ["all"] + sorted({f"{e}/{s}" for e, s, _, _ in pairs}):
        ps = [p for p in pairs if scope == "all" or f"{p[0]}/{p[1]}" == scope]
        res["agreement"][scope] = {d: {"n": len(ps), "raw": round(sum(h[d] == m[d] for _, _, h, m in ps) / len(ps), 3),
                                       "kappa": kappa([h[d] for *_, h, _ in ps], [m[d] for *_, m in ps])}
                                   for d in DIMS + ("stage",)}
    e1 = [p for p in pairs if p[0] == "E1" and p[1] == "gpt-4.1"]
    kh = sum(h["stage"] == "read_correctly_decided_wrong" for *_, h, _ in e1)
    km = sum(m["stage"] == "read_correctly_decided_wrong" for *_, m in e1)
    all_e1 = [f for f in final.values() if f["experiment"] == "E1" and f["setting"] == "gpt-4.1"]
    ka = sum(f["final_stage"] == "read_correctly_decided_wrong" for f in all_e1)
    res["e1_read_correctly_decided_wrong"] = {
        "human": {"k": kh, "n": len(e1), "share": round(kh / len(e1), 3) if e1 else None, "wilson95": wilson(kh, len(e1))},
        "model_same_rows": {"k": km, "n": len(e1)}, "model_all_123": {"k": ka, "n": len(all_e1)}}
    md = ["# Human check: agreement with the final model codes", "",
          f"Completed rows {len(done)} of {len(sheet)} (missing {len(sheet) - len(done)}). Analysis as fixed in "
          "README.md. Settings never pooled.", "", "| scope | " + " | ".join(DIMS + ("stage",)) + " |",
          "|---|" + "---|" * (len(DIMS) + 1)]
    for scope, v in res["agreement"].items():
        md.append(f"| {scope} (n={v['stage']['n']}) | " + " | ".join(f"{v[d]['kappa']} ({v[d]['raw']})"
                                                                     for d in DIMS + ("stage",)) + " |")
    x = res["e1_read_correctly_decided_wrong"]
    md += ["", f"E1 / gpt-4.1, read_correctly_decided_wrong: human {x['human']['k']}/{x['human']['n']} "
           f"({x['human']['share']}, Wilson 95% {x['human']['wilson95']}); model on the same rows "
           f"{km}/{len(e1)}; model on all {len(all_e1)}: {ka}.", "",
           "Stage confusion (human -> model), all rows:", ""]
    conf = Counter((h["stage"], m["stage"]) for *_, h, m in pairs)
    md += [f"- {a} -> {b}: {n}" for (a, b), n in sorted(conf.items())]
    adp = OUT / "sheet_ad_approvals.csv"
    if adp.exists():
        ad = [r for r in csv.DictReader(open(adp, encoding="utf-8")) if (r["h_source_named"] or "").strip()]
        if ad:
            res["ad"] = {"n": len(ad), "source_named": Counter(r["h_source_named"].strip() for r in ad),
                         "presents_id_as_record": Counter(r["h_presents_id_as_record"].strip() for r in ad)}
            md += ["", f"AgentDojo approvals coded: {len(ad)}; source named {dict(res['ad']['source_named'])}; "
                   f"presents the id as a record {dict(res['ad']['presents_id_as_record'])}."]
    (OUT / "human_agreement.json").write_text(json.dumps(res, indent=2, default=dict) + "\n", encoding="utf-8")
    (OUT / "REPORT_human.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
