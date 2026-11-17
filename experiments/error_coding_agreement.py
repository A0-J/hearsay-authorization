"""Inter-coder agreement and adjudication for the error coding (exploratory; no API calls).

    python experiments/error_coding_agreement.py

Two coders (A: model_coding_{gpt,claude}.csv; B: model_coding_B_{gpt,claude}.csv) coded every incorrect E1/E2
decision independently from the same blinded input (coding_input_*.csv) and the same codebook, without seeing each
other's codes, the rule-based stages or the manual samples. This script:
  1. computes Cohen's kappa and raw agreement per dimension, overall and per setting;
  2. writes adjudication.csv: every row where A and B differ on evidence_reading, reason_conclusion or driver, with
     both codes and the reason, and an empty `adjudicated_*` column for each differing dimension (filled by hand;
     this script never overwrites a filled file);
  3. derives the final stage per row, from agreed codes or from the adjudicated ones:
        reason_decision_mismatch      reason_conclusion = supports_normative
        evidence_misread              evidence_reading = incorrect
        read_correctly_decided_wrong  evidence_reading = correct (sub-label: driver)
        claim_without_reading         evidence_reading = not_stated (sub-label: driver)
     and compares it with the manual stages of the two manual samples (third reference);
  4. writes coded_final.csv, agreement.json and REPORT_agreement.md.

WHO CODED (corrected 2026-11-17): no person has coded these rows. Coders A and B were separate subagent instances
of the same Claude model as the assistant (Claude Opus 5.5); the adjudication and the "manual" samples
(manual_sample*.csv) were written by the assistant itself. Agreement here is agreement between instances of one
model: it measures consistency, not validity. A human check is prepared separately (results/error-stages/human-check/).
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict

from common import RESULTS

D = RESULTS / "error-stages"
DIMS = ("evidence_reading", "reason_conclusion", "driver", "timing_misread")
ADJ_DIMS = ("evidence_reading", "reason_conclusion", "driver")


def read(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def kappa(a: list[str], b: list[str]) -> float | None:
    n = len(a)
    if n == 0:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return None if pe == 1 else round((po - pe) / (1 - pe), 3)


def stage(ev: str, concl: str, driver: str) -> tuple[str, str]:
    if concl == "supports_normative":
        return "reason_decision_mismatch", driver
    if ev == "incorrect":
        return "evidence_misread", driver
    if ev == "correct":
        return "read_correctly_decided_wrong", driver
    return "claim_without_reading" if driver == "claim" else "not_stated_other", driver


def main() -> None:
    inp = {r["row_id"]: r for part in ("gpt", "claude") for r in read(D / f"coding_input_{part}.csv")}
    A = {r["row_id"]: r for part in ("gpt", "claude") for r in read(D / f"model_coding_{part}.csv")}
    B = {r["row_id"]: r for part in ("gpt", "claude") for r in read(D / f"model_coding_B_{part}.csv")}
    assert set(A) == set(B) == set(inp), "both coders coded every row"
    ids = sorted(inp, key=int)

    agree = {"overall": {}, "by_setting_experiment": {}}
    for dim in DIMS:
        a, b = [A[i][dim] for i in ids], [B[i][dim] for i in ids]
        agree["overall"][dim] = {"kappa": kappa(a, b), "raw": round(sum(x == y for x, y in zip(a, b)) / len(a), 3),
                                 "n": len(a)}
    groups = defaultdict(list)
    for i in ids:
        groups[f"{inp[i]['experiment']}/{inp[i]['setting']}"].append(i)
    for g, gi in sorted(groups.items()):
        agree["by_setting_experiment"][g] = {
            dim: {"kappa": kappa([A[i][dim] for i in gi], [B[i][dim] for i in gi]),
                  "raw": round(sum(A[i][dim] == B[i][dim] for i in gi) / len(gi), 3), "n": len(gi)} for dim in DIMS}

    adj_path = D / "adjudication.csv"
    filled = adj_path.exists() and any(any((r.get(f"adjudicated_{d}") or "").strip() for d in ADJ_DIMS)
                                       for r in read(adj_path))
    if not filled:
        with open(adj_path, "w", encoding="utf-8", newline="") as fh:
            cols = ["row_id", "experiment", "setting", "side", "normative_decision", "actual_decision", "handoff_claim",
                    "policy"] + [f"{c}_{d}" for d in ADJ_DIMS for c in ("A", "B", "adjudicated")] + ["A_note", "B_note",
                                                                                                    "reason"]
            w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
            w.writeheader()
            for i in ids:
                if any(A[i][d] != B[i][d] for d in ADJ_DIMS):
                    row = {k: inp[i][k] for k in ("row_id", "experiment", "setting", "side", "normative_decision",
                                                  "actual_decision", "handoff_claim", "policy", "reason")}
                    for d in ADJ_DIMS:
                        row[f"A_{d}"], row[f"B_{d}"], row[f"adjudicated_{d}"] = A[i][d], B[i][d], ""
                    row["A_note"], row["B_note"] = A[i]["note"], B[i]["note"]
                    w.writerow(row)
    adj = {r["row_id"]: r for r in read(adj_path)}

    final, unresolved = [], 0
    for i in ids:
        codes = {}
        for d in ADJ_DIMS:
            if A[i][d] == B[i][d]:
                codes[d] = A[i][d]
            else:
                v = (adj.get(i, {}).get(f"adjudicated_{d}") or "").strip()
                codes[d] = v or "UNRESOLVED"
                unresolved += not v
        st, sub = (stage(codes["evidence_reading"], codes["reason_conclusion"], codes["driver"])
                   if "UNRESOLVED" not in codes.values() else ("UNRESOLVED", "-"))
        final.append({"row_id": i, "experiment": inp[i]["experiment"], "setting": inp[i]["setting"],
                      **codes, "timing_misread_A": A[i]["timing_misread"], "timing_misread_B": B[i]["timing_misread"],
                      "final_stage": st, "final_driver": sub})
    with open(D / "coded_final.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(final[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(final)

    # third reference: the assistant's manual stages (manual_sample*.csv; Claude, not a person), matched on cell/repeat
    coded = read(D / "errors_coded.csv")
    key_of = {str(n): (r["experiment"], r["setting"], r["cell_id"], str(r["repeat"])) for n, r in enumerate(coded)}
    fin = {key_of[f["row_id"]]: f["final_stage"] for f in final}
    manual = []
    for p, col in (("manual_sample.csv", "manual_stage"), ("manual_sample_v2.csv", "manual_stage")):
        for m in read(D / p):
            k = (m["experiment"], m["setting"], m["cell_id"], str(m["repeat"]))
            if k in fin and m.get(col):
                manual.append((m[col], fin[k]))
    agree["manual_vs_final"] = {"n": len(manual), "raw": round(sum(x == y for x, y in manual) / len(manual), 3)
                                if manual else None, "kappa": kappa([x for x, _ in manual], [y for _, y in manual])}
    agree["unresolved_cells"] = unresolved
    (D / "agreement.json").write_text(json.dumps(agree, indent=2) + "\n", encoding="utf-8")

    counts = Counter((f["experiment"], f["setting"], f["final_stage"]) for f in final)
    subs = defaultdict(Counter)
    for f in final:
        subs[(f["experiment"], f["setting"], f["final_stage"])][f["final_driver"]] += 1
    tot = Counter((f["experiment"], f["setting"]) for f in final)
    md = ["# Error coding: agreement and final stages (exploratory)", "",
          "Two independent coders (A, B) coded all incorrect Experiment 1 (GPT-4.1) and Experiment 2 decisions from "
          "the same blinded input and codebook. Disagreements are adjudicated in adjudication.csv. Settings are never "
          "pooled. DEFER-arm errors are classified mechanically (normative vs actual decision) in REPORT.md.", "",
          "## Agreement (Cohen's kappa, raw agreement)", "", "| scope | " + " | ".join(DIMS) + " |",
          "|---|" + "---|" * len(DIMS)]
    md.append("| all rows (n=%d) | " % len(ids) + " | ".join(
        f"{agree['overall'][d]['kappa']} ({agree['overall'][d]['raw']})" for d in DIMS) + " |")
    for g, v in agree["by_setting_experiment"].items():
        md.append(f"| {g} (n={v[DIMS[0]]['n']}) | " + " | ".join(f"{v[d]['kappa']} ({v[d]['raw']})" for d in DIMS) + " |")
    mv = agree["manual_vs_final"]
    md += ["", f"Final stage vs the manual stage of the two manual samples: n = {mv['n']}, raw agreement "
           f"{mv['raw']}, kappa {mv['kappa']}. Unresolved disagreements: {unresolved}.", "",
           "**Who coded.** No person has coded these rows. Coders A and B were separate subagent instances of the "
           "same Claude model as the assistant (Claude Opus 5.5), each blind to the other. The adjudication and the "
           "manual samples were written by the assistant. The kappas above are agreement between instances of one "
           "model (consistency), not validity, and the manual-sample comparison is not a human reference. A human "
           "check is prepared in human-check/.", "",
           "## Final stages", "", "| experiment | setting | stage | n | of errors | driver |", "|---|---|---|---|---|---|"]
    for (e, s, st), n in sorted(counts.items()):
        md.append(f"| {e} | {s} | {st} | {n} | {tot[(e, s)]} | "
                  f"{', '.join(f'{k}: {v}' for k, v in subs[(e, s, st)].most_common())} |")
    (D / "REPORT_agreement.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
