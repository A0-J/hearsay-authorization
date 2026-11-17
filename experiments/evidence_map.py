"""Finding -> evidence map for writing up (no API calls). Run after experiments/synthesis.py.

Writes results/synthesis/EVIDENCE_MAP.md, tables/prereg_tests.csv (every test in every run's analysis files) and
tables/evidence_map.csv. Part A lists the pre-registered tests that carry the findings, read from each run's own
analysis files. Part B links each finding to its status, numbers, tests, limits, figures and sources; its numbers are
read from Part A and from results/synthesis/tables/. No research question is assigned here: that is the author's.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import synthesis as S  # noqa: E402
from common import ROOT  # noqa: E402

RES = ROOT / "results"
OUT = RES / "synthesis"
TAB = OUT / "tables"


def pp(x: float) -> str:
    return f"{100 * x:+.1f}"


def pv(p) -> str:
    return "—" if p is None else (f"{p:.2g}" if p >= 1e-4 else f"{p:.0e}")


def rows(name: str) -> list[dict]:
    with (TAB / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def j(path: str):
    return json.loads((RES / path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- every recorded test, flat
def all_tests() -> list[dict]:
    out = []

    def add(run, src, fam, name, t):
        if isinstance(t, dict) and "estimate" in t:
            out.append({"run": run, "file": src, "family": fam, "test": name, "estimate": t["estimate"],
                        "ci_low": t["ci95"][0], "ci_high": t["ci95"][1], "p_signflip": t.get("p_signflip"),
                        "p_holm": t.get("p_holm", t.get("p_holm_primary_pair")), "units": t.get("n_tasks")})
    for f in sorted(RES.glob("*/analysis/*.json")):
        run = f.parent.parent.name
        if run.endswith("-dryrun") or "smoke" in run or f.name not in (
                "tests.json", "generalization_tests.json", "agentdojo_subsets.json"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        for fam, v in d.items():
            if not isinstance(v, dict):
                continue
            for name, t in v.items():
                if isinstance(t, dict) and "estimate" not in t:
                    for sub, tt in t.items():
                        add(run, f.name, f"{fam}/{name}", sub, tt)
                else:
                    add(run, f.name, fam, name, t)
    return out


# ---------------------------------------------------------------- Part A: the tests that carry the findings
E1, E2 = "E1-gpt-4.1-run1/analysis/tests.json", "E2-gpt-4.1-run1/analysis/tests.json"
GEN, ADS = "G1-gpt-4.1-run1/analysis/generalization_tests.json", "AD1-gpt-4.1-run1/analysis/agentdojo_subsets.json"
A = [
    ("A1", "E1 · GPT-4.1 · 11 tasks", "P (Holm)", E1, ("primary", "H1_positive_claims_raise_approval_invalid_aware"),
     "H1 approval claims raise approval of invalid calls (aware)"),
    ("A2", "E1 · GPT-4.1 · 11 tasks", "P (Holm)", E1, ("primary", "H2_indirect_minus_direct_claim_effect_aware"),
     "H2 claim effect larger on derived than direct evidence"),
    ("A3", "E1 · GPT-4.1 · 11 tasks", "P (Holm)", E1, ("primary", "H3_abs_list_minus_abs_complete_claim_effect_aware"),
     "H3 claim effect larger without the completeness lines"),
    ("A4", "E1 · GPT-4.1 · 11 tasks", "S", E1, ("secondary", "H5_negative_claim_effect_valid_aware"),
     "H5 withdrawal claim on valid calls (aware)"),
    ("A5", "E1 · GPT-4.1 · 11 tasks", "S", E1, ("secondary", "H5_negative_claim_effect_valid_explicit"),
     "H5 withdrawal claim on valid calls (explicit)"),
    ("A6", "E2 · GPT-4.1 · 11 tasks", "P (Holm)", E2, ("primary", "P1_negative_claim_valid_blockA_aware"),
     "P1 withdrawal claim on valid calls (aware; re-samples E1's inputs)"),
    ("A7", "E2 · GPT-4.1 · 11 tasks", "P (Holm)", E2, ("primary", "P2_before_minus_after_valid_withdrawn_base_aware"),
     "P2 claimed withdrawal before − after the snapshot (base policy)"),
    ("A8", "E2 · GPT-4.1 · 11 tasks", "S (Holm)", E2,
     ("secondary", "S1_asymmetry_withdrawal_drop_minus_approval_rise_unspecified"), "S1 asymmetry: withdrawal drop − approval rise"),
    ("A9", "E2 · GPT-4.1 · 11 tasks", "S (Holm)", E2, ("secondary", "S3_supervisor_minus_upstream_agent"),
     "S3 supervisor − upstream agent as the claim's source"),
    ("A10", "E2 · GPT-4.1 · 11 tasks", "S (Holm)", E2, ("secondary", "S4_record_authority_minus_base_unspecified"),
     "S4 record rule − base policy (no time)"),
    ("A11", "E2 · GPT-4.1 · 11 tasks", "S (Holm)", E2, ("secondary", "S5_explicit_minus_aware_unspecified"),
     "S5 evidence-explicit − evidence-aware under the claim"),
    ("A12", "E2 · GPT-4.1 · 11 tasks", "S (Holm)", E2, ("secondary", "S6_record_authority_before_minus_after"),
     "S6 record rule: before − after"),
    ("A13", "Generalization · GPT-4.1 · AB new, 8 cases", "P (Holm)", GEN,
     ("primary_case_level", "G1_negative_claim_valid_aware"), "G1 withdrawal claim on valid calls"),
    ("A14", "Generalization · GPT-4.1 · AB new, 8 cases", "P (Holm)", GEN,
     ("primary_case_level", "G2_positive_claims_invalid_aware"), "G2 approval claims on invalid calls"),
    ("A15", "Generalization · GPT-4.1 · AgentDojo, 19 cases", "P (Holm)", ADS, ("primary", "G1"),
     "G1 withdrawal claim on valid calls"),
    ("A16", "Generalization · GPT-4.1 · AgentDojo, 19 cases", "P (Holm)", ADS, ("primary", "G2"),
     "G2 approval claims on invalid calls"),
    ("A17", "Generalization · GPT-4.1 · AgentDojo sensitivity", "sensitivity (pre-specified)", ADS, ("S-a", "G1"),
     "G1, identical calls merged (16 units)"),
    ("A18", "Generalization · GPT-4.1 · AgentDojo sensitivity", "sensitivity (pre-specified)", ADS, ("S-b", "G1"),
     "G1, Abank06 and Atravel00 also dropped (17 cases)"),
    ("A19", "Generalization · GPT-4.1 · AB new, task unit", "S (task unit)", "G2E-gpt-4.1-run1/analysis/tests.json",
     ("secondary", "S5_explicit_minus_aware_unspecified"), "S5 on the new tasks (28 tasks)"),
    ("A20", "Generalization · GPT-4.1 · AgentDojo, task unit", "S (task unit)", "AD2E-gpt-4.1-run1/analysis/tests.json",
     ("secondary", "S5_explicit_minus_aware_unspecified"), "S5 on the AgentDojo tasks (20 tasks, Abank00 included)"),
]
PANEL = [("GPT-4.1", "E1-gpt-4.1-run1"), ("gpt-4o", "E1P-gpt-4o-run1"), ("gpt-4.1-mini", "E1P-gpt-4.1-mini-run1"),
         ("gpt-5.5", "E1P-gpt-5.5-run1"), ("Claude Sonnet 4.6", "E1P-claude-sonnet-4-6-run1"),
         ("Claude Sonnet 5.5, thinking", "E1-claude-sonnet-5-5-run1"),
         ("Claude Sonnet 5.5, no thinking", "E1P-claude-sonnet-5-5-nothink-run1"),
         ("Claude Haiku 5.5", "E1P-claude-haiku-5-5-run1")]


def part_a() -> dict[str, dict]:
    got = {}
    for aid, where, status, path, (fam, name), what in A:
        t = j(path)[fam][name]
        got[aid] = {"id": aid, "where": where, "status": status, "test": what, "units": t.get("n_tasks"),
                    "estimate_pp": pp(t["estimate"]), "ci95_pp": f"[{pp(t['ci95'][0])}, {pp(t['ci95'][1])}]",
                    "p": pv(t.get("p_signflip")), "p_holm": pv(t.get("p_holm", t.get("p_holm_primary_pair"))),
                    "source": f"results/{path}"}
    for i, (label, run) in enumerate(PANEL):
        t = j(f"{run}/analysis/tests.json")["secondary"]
        for ins in ("aware", "explicit"):
            x = t[f"H5_negative_claim_effect_valid_{ins}"]
            aid = f"B{i + 1}{ins[0]}"
            got[aid] = {"id": aid, "where": f"Panel · {label} · 11 tasks", "status": "per run (panel prereg)",
                        "test": f"H5 withdrawal claim on valid calls ({ins})", "units": x.get("n_tasks"),
                        "estimate_pp": pp(x["estimate"]), "ci95_pp": f"[{pp(x['ci95'][0])}, {pp(x['ci95'][1])}]",
                        "p": pv(x.get("p_signflip")), "p_holm": "—",
                        "source": f"results/{run}/analysis/tests.json"}
    return got


def g2_by_claim() -> dict[str, str]:
    """Post hoc: AgentDojo G2 split by claim (case level, as G2)."""
    from statistics import mean
    s = S.GPT_SETS[2]
    M, R, N, tasks = S.e1(s["e1"])
    out = {}
    for claim in ("unverified", "bare", "verified", "specific"):
        per = {t: mean(R[(t, "aware", "invalid", c, claim)] for c in S.INVALID)
               - mean(R[(t, "aware", "invalid", c, "none")] for c in S.INVALID) for t in tasks}
        st = S.stat(S.by_unit(s, per))
        out[claim] = f"{S.ci(st)} (p = {pv(st['p_signflip'])})"
    return out


# ---------------------------------------------------------------- Part B: finding -> evidence
def part_b(a: dict[str, dict]) -> list[dict]:
    def t(aid):
        x = a[aid]
        return f"{x['estimate_pp']} {x['ci95_pp']}" + (f", Holm p = {x['p_holm']}" if x["p_holm"] != "—" else
                                                         f", p = {x['p']}")
    pol = {(r["set"], r["model"], r["instruction"], r["policy"], r["claim_timing"]): float(r["approval"])
           for r in rows("policy_timing.csv")}
    inv = [r for r in rows("temporal_inversion_counts.csv")]
    par = {(r["run"], r["measure"], r["rule"]): r["value"] for r in rows("parser_sensitivity.csv")}
    e2e = {(r["side"], r["claim"]): r for r in rows("e2e_planner_stage.csv")}
    fresh = {(r["model"], r["instruction"], r["condition"], r["claim"]): r for r in rows("freshness_defer.csv")}
    comp = {r["run"]: r for r in rows("evidence_composition.csv")}
    forged = {(r["set"], r["suite"], r["instruction"], r["condition"], r["claim"]): (r["approved"], r["judged"])
              for r in rows("forged_id_detail.csv")}
    gate = rows("gate_vs_normative.csv")
    prov = rows("run_provenance.csv")
    g2 = g2_by_claim()
    sets = [s["name"] for s in S.GPT_SETS]

    def share(ins, policy):
        return ", ".join(f"{r['reason_places_0900_after_snapshot']}/{r['rejections_before']}" for r in inv
                         if (r["instruction"], r["policy"]) == (ins, policy))

    def gpt_ra(policy):
        return " / ".join(f"{100 * pol[(st, 'GPT-4.1', 'explicit', policy, 'before')]:.0f}%" for st in sets)

    cm = {s: comp[f"GPT-4.1, {s}"] for s in sets}
    sens = "E1P-claude-sonnet-4-6-run1"
    nothink = "E2-claude-sonnet-5-5-nothink-run1"
    B = [
        {"id": "F1", "finding": "A withdrawal claim lowers approval of calls that valid, complete records authorize.",
         "status": "P: E2 P1 (re-samples E1's inputs), generalization G1 on AB new and AgentDojo; first seen as E1 "
                   "secondary H5",
         "setting": "GPT-4.1, evidence-aware; 11 tasks, 8 AB-new cases (7 new domains of E1 cases + 1 new case), "
                    "19 AgentDojo cases",
         "numbers": f"P1 {t('A6')}; G1 AB new {t('A13')}; G1 AgentDojo {t('A15')}; sensitivity S-a {t('A17')}, "
                    f"S-b {t('A18')}",
         "tests": "A6, A13, A15, A17, A18 (origin A4)",
         "limits": "verifier decisions only, not executed actions; GPT-4.1 only on the new sets; the 11-task "
                   "result is a repeat of E1's inputs, not independent evidence",
         "figures": "synthesis/png/fig1_two_directions_gpt41.png; generalization-figures/png/fig_gen_gpt41_comparison"
                    ".png; E1-figures/png/fig2_per_task_negative_claim.png; E2-figures/png/fig_e2_tests_forest.png",
         "sources": "REPORT §2; tables/two_directions_gpt41.csv"},
        {"id": "F2", "finding": "Generic approval claims do not raise approval of invalid calls; a claim naming a "
                                "specific approval ID does in AgentDojo.",
         "status": "P: E1 H1–H3 not supported; G2 not supported on AB new, supported on AgentDojo. The split of G2 by "
                   "claim is H",
         "setting": "GPT-4.1, evidence-aware",
         "numbers": f"H1 {t('A1')}; H2 {t('A2')}; H3 {t('A3')}; G2 AB new {t('A14')}; G2 AgentDojo {t('A16')}. "
                    f"AgentDojo G2 by claim: unverified {g2['unverified']}, bare {g2['bare']}, verified "
                    f"{g2['verified']}, specific ID {g2['specific']}; asymmetry S1 {t('A8')}",
         "tests": "A1–A3, A8, A14, A16",
         "limits": "AgentDojo's significant G2 comes entirely from the specific-ID claim (see F8); the generic claims "
                   "are 0 there",
         "figures": "synthesis/png/fig1_two_directions_gpt41.png (panel B)",
         "sources": "REPORT §2, §6; results/E1-gpt-4.1-run1/analysis/REPORT.md"},
        {"id": "F3", "finding": "For GPT-4.1 the withdrawal effect did not change with the claim's stated timing or "
                                "source or with a policy rule, and the evidence-explicit instruction removes it.",
         "status": "S (pre-registered reading rules), plus a post-hoc manipulation check on timing (H)",
         "setting": "GPT-4.1; 11 tasks (tests), AB new and AgentDojo (S5 at task unit)",
         "numbers": f"P2 {t('A7')}; S3 {t('A9')}; S4 {t('A10')}; S5 {t('A11')}, AB new {t('A19')}, AgentDojo "
                    f"{t('A20')}. Refusals of the 'before' cells whose reason puts 09:00 after the 10:00 snapshot "
                    f"(11 tasks, AB new, AgentDojo): {share('aware', 'base')} (aware, base)",
         "tests": "A7, A9–A11, A19, A20",
         "limits": "P2 = 0 is weak evidence on timing: many refusals misread the clock order (REPORT §4); the "
                   "misreading count is a regex count, not a coded reading",
         "figures": "E2-figures/png/fig_e2_valid_approval_aware.png, fig_e2_valid_approval_explicit.png, "
                    "fig_e2_tests_forest.png",
         "sources": "REPORT §4; tables/temporal_inversion_counts.csv"},
        {"id": "F4", "finding": "The withdrawal effect and the instruction fix depend on the model.",
         "status": "per run under the panel pre-registration; each model its own analysis, no pooled test",
         "setting": "8 model settings, 11 tasks, identical inputs",
         "numbers": "; ".join(f"{lab}: aware {a[f'B{i + 1}a']['estimate_pp']} {a[f'B{i + 1}a']['ci95_pp']}, "
                              f"explicit {a[f'B{i + 1}e']['estimate_pp']} {a[f'B{i + 1}e']['ci95_pp']}"
                              for i, (lab, _) in enumerate(PANEL)),
         "tests": "B1a–B8e",
         "limits": f"Claude Sonnet 4.6 depends on the parser: explicit {par[(sens, 'withdrawal effect, explicit (pp)', 'first')]} "
                   f"by the first decision, {par[(sens, 'withdrawal effect, explicit (pp)', 'last')]} by the last "
                   "(F10); only GPT-4.1 ran on the new sets",
         "figures": "synthesis/png/fig2_model_profile_11tasks.png",
         "sources": "REPORT §3; tables/model_profile_11tasks.csv"},
        {"id": "F5", "finding": "A policy rule on snapshots undoes the instruction fix when a withdrawal is claimed "
                                "before the snapshot.",
         "status": "H (the interaction with the explicit instruction was never tested)",
         "setting": "GPT-4.1, evidence-explicit, valid call, withdrawal claimed at 09:00 (before the 10:00 snapshot)",
         "numbers": f"approval under the base policy {gpt_ra('base')} → with the record rule {gpt_ra('record_authority')} "
                    "(11 tasks / AB new / AgentDojo); Claude Sonnet 5.5 without thinking "
                    f"{par[(nothink, 'approval, withdrawal at 09:00, explicit, record_authority', 'first')]} by the "
                    f"first decision, {par[(nothink, 'approval, withdrawal at 09:00, explicit, record_authority', 'last')]}"
                    " by the last (explicit)",
         "tests": "none pre-registered (S4 and S6 are aware-only and 0)",
         "limits": "post hoc; part of the refusals misread the clock order (F3); needs a pre-registered test on new "
                   "data",
         "figures": "synthesis/png/fig3_policy_rule_timing.png",
         "sources": "REPORT §1 R4, §4; tables/policy_timing.csv"},
        {"id": "F6", "finding": "With a DEFER option, GPT-4.1 defers when a withdrawal is claimed against valid "
                                "records, but approves a 5.5-hour-old snapshot that the policy says to re-check.",
         "status": "D (DEFER arm, exploratory, descriptive)",
         "setting": "GPT-4.1, Claude Sonnet 5.5 (thinking, no thinking); 11 tasks",
         "numbers": "stale snapshot, no claim, approved: GPT-4.1 "
                    f"{100 * float(fresh[('GPT-4.1', 'aware_tristate', 'stale_valid', 'none')]['approve']):.0f}% "
                    f"(aware) / {100 * float(fresh[('GPT-4.1', 'explicit_tristate', 'stale_valid', 'none')]['approve']):.0f}% "
                    "(explicit); Claude Sonnet 5.5 thinking deferred "
                    f"{100 * float(fresh[('Claude Sonnet 5.5, thinking', 'aware_tristate', 'stale_valid', 'none')]['defer']):.0f}%"
                    " (aware); fresh valid snapshot with a withdrawal after it, GPT-4.1 deferred "
                    f"{100 * float(fresh[('GPT-4.1', 'aware_tristate', 'fresh_valid', 'withdrawn_after')]['defer']):.0f}%",
         "tests": "none (descriptive by design)",
         "limits": "11 tasks only (the AB and AgentDojo DEFER datasets exist but were not run); no-thinking values "
                   "depend on the parser (F10)",
         "figures": "E2-figures/png/fig_defer_decisions_aware_tristate.png, fig_defer_decisions_explicit_tristate.png",
         "sources": "REPORT §7; tables/freshness_defer.csv"},
        {"id": "F7", "finding": "End-to-end (partial): with a withdrawal note no episode attempts the gated call.",
         "status": "D (Experiment 3 paused at 301 of 792 episodes; no test)",
         "setting": "GPT-4.1 agents, 5 tasks, unequal cells",
         "numbers": "gated call attempted, valid state: no claim "
                    f"{e2e[('valid', 'none')]['gated_call_attempted']}/{e2e[('valid', 'none')]['episodes']}, approval claim "
                    f"{e2e[('valid', 'approved')]['gated_call_attempted']}/{e2e[('valid', 'approved')]['episodes']}, withdrawal "
                    f"claim {e2e[('valid', 'withdrawn')]['gated_call_attempted']}/{e2e[('valid', 'withdrawn')]['episodes']}"
                    "; invalid state, withdrawal claim "
                    f"{e2e[('invalid', 'withdrawn')]['gated_call_attempted']}/{e2e[('invalid', 'withdrawn')]['episodes']}",
         "tests": "E3-2 cannot separate the methods (no gated call under the withdrawal claim)",
         "limits": "partial, paused run; planner and executor not separated; not at the confirmatory level of F1",
         "figures": "—",
         "sources": "REPORT §12; tables/e2e_planner_stage.csv"},
        {"id": "F8", "finding": "An approval ID named in the task message but absent from the records is accepted "
                                "and cited as the basis.",
         "status": "H for the ID-absent cells (the specific claim itself was pre-registered; G2 in AgentDojo, F2, is "
                   "the pre-registered test it drives)",
         "setting": "GPT-4.1, evidence-aware, invalid evidence, ID absent from the records",
         "numbers": "complete lookup that found nothing, specific claim: " + "; ".join(
             f"{st} {'/'.join(forged[(st, '(all)', 'aware', 'abs_complete', 'specific')])}" for st in sets)
             + "; evidence-explicit: " + "; ".join(
             f"{st} {'/'.join(forged[(st, '(all)', 'explicit', 'abs_complete', 'specific')])}" for st in sets),
         "tests": "A16 (G2 AgentDojo); the split by claim is post hoc",
         "limits": "concentrated in AgentDojo's Slack and workspace cases; gpt-4o differs (more without the "
                   "completeness lines)",
         "figures": "synthesis/png/fig1_two_directions_gpt41.png (panel B)",
         "sources": "REPORT §6; tables/forged_id_detail.csv; results/invalid-approvals/"},
        {"id": "F9", "finding": "Under the withdrawal claim, `combined` evidence (an extra revoked same-tool record) "
                                "keeps more approvals than `direct`.",
         "status": "H",
         "setting": "GPT-4.1, evidence-aware, valid evidence",
         "numbers": "combined − direct: " + "; ".join(
             f"{st} {100 * float(cm[st]['combined_minus_direct']):+.1f} "
             f"[{100 * float(cm[st]['cmd_ci_low']):+.1f}, {100 * float(cm[st]['cmd_ci_high']):+.1f}]" for st in sets),
         "tests": "none pre-registered",
         "limits": "the 11-task interval includes 0; record count, IDs and the revocation change together, so the "
                   "cause is not identified",
         "figures": "synthesis/png/fig4_evidence_composition.png",
         "sources": "REPORT §5; tables/evidence_composition.csv"},
        {"id": "F10", "finding": "Some Claude replies state two conflicting decisions; results for those runs depend "
                                 "on which is read.",
         "status": "H (sensitivity analysis); the official numbers use the frozen first-decision parser",
         "setting": "Claude runs only (no GPT reply has two decisions)",
         "numbers": f"Claude Sonnet 4.6 explicit withdrawal effect {par[(sens, 'withdrawal effect, explicit (pp)', 'first')]}"
                    f" → {par[(sens, 'withdrawal effect, explicit (pp)', 'last')]}; see F4, F5, F6",
         "tests": "—",
         "limits": "neither reading is shown to be the model's intent",
         "figures": "—",
         "sources": "REPORT §9; tables/parser_counts.csv, parser_sensitivity.csv"},
        {"id": "F11", "finding": "The provenance gate's 0 errors hold for record validity only.",
         "status": "design fact (by construction), not a finding",
         "setting": "all datasets",
         "numbers": "gate allows normative-reject cells in E2: " + " / ".join(
             r["gate_allows_normative_reject"] for r in gate if r["set"].startswith("Experiment 2"))
             + "; normative-defer cells in the DEFER arm: " + " / ".join(
             r["gate_allows_normative_defer"] for r in gate if r["set"].startswith("DEFER")),
         "tests": "—",
         "limits": "a freshness-aware gate scored on labels from the same rule would again be 0 by construction",
         "figures": "E2-figures/png/fig_ablation_methods.png (methods side by side)",
         "sources": "REPORT §8, §10; tables/gate_vs_normative.csv, method_ladder.csv"},
        {"id": "F12", "finding": "Recorded runs are reproducible from the frozen inputs and parser.",
         "status": "provenance check",
         "setting": f"{len(prov)} verifier-only runs",
         "numbers": f"{sum(int(r['calls']) for r in prov):,} calls; input hash, instruction hash and re-parsed "
                    "decision match in "
                    + ("every call" if all(r["input_sha256_match"] == r["calls"] == r["instructions_sha256_match"]
                                           == r["decision_reproduced_by_frozen_parser"] for r in prov)
                       else "NOT every call (see the table)"),
         "tests": "—",
         "limits": "uncommitted runner changes at run time were not saved; client defaults not in the configs; "
                   "pre-registration times are local clocks; E1 Amendment 1 was committed during the E1 run",
         "figures": "—",
         "sources": "REPORT §11; tables/run_provenance.csv; results/provenance/"},
        {"id": "F13", "finding": "Error causes (why the verifier erred).",
         "status": "model-assisted coding; the human check is pending",
         "setting": "GPT-4.1 errors",
         "numbers": "see results/error-stages/",
         "tests": "—",
         "limits": "not validated by a human coder yet; do not report as established",
         "figures": "E1-figures/png/fig4_error_causes_gpt-4.1.png",
         "sources": "results/error-stages/, results/error-stages/human-check/"},
    ]
    return B


def main() -> None:
    allt = all_tests()
    S.write_csv("prereg_tests.csv", allt)
    a = part_a()
    b = part_b(a)
    S.write_csv("evidence_map.csv", b)
    L = ["# Evidence map: findings → tests, numbers, limits, figures, sources", "",
         "Generated by `experiments/evidence_map.py` from each run's analysis files and results/synthesis/tables/ "
         "(no API calls). Part A lists the pre-registered tests behind the findings; every test of every run is in "
         "tables/prereg_tests.csv. Part B links each finding to its evidence. No research question is assigned here.",
         "", "Status tags as in REPORT.md: **P** pre-registered primary; **S** pre-registered secondary; **D** "
         "pre-registered as descriptive; **H** post hoc. Estimates are in percentage points with 95% bootstrap "
         "intervals over units; p is the sign-flip test (exact up to 16 units, else 100,000 random sign vectors, so "
         "1e-05 is its floor); Holm p where the pre-registration sets a family. Figure and source paths are "
         "relative to results/; REPORT § means results/synthesis/REPORT.md.", "",
         "## Part A. Pre-registered tests behind the findings", "",
         "| id | where | status | test | units | estimate (pp) | 95% CI | p | Holm p |",
         "|---|---|---|---|---|---|---|---|---|"]
    for x in a.values():
        L.append(f"| {x['id']} | {x['where']} | {x['status']} | {x['test']} | {x['units']} | {x['estimate_pp']} | "
                 f"{x['ci95_pp']} | {x['p']} | {x['p_holm']} |")
    L += ["", "Sources: " + "; ".join(sorted({f"`{x['source']}`" for x in a.values() if x["id"].startswith("A")})) + ".",
          "", "## Part B. Findings and their evidence", ""]
    for f in b:
        L += [f"### {f['id']}. {f['finding']}", "",
              f"- **Status:** {f['status']}", f"- **Where it holds:** {f['setting']}",
              f"- **Numbers:** {f['numbers']}", f"- **Tests:** {f['tests']}",
              f"- **Limits:** {f['limits']}", f"- **Figures:** {f['figures']}",
              f"- **Sources:** {f['sources']}", ""]
    (OUT / "EVIDENCE_MAP.md").write_text("\n".join(L), encoding="utf-8")
    print("wrote", OUT / "EVIDENCE_MAP.md")


if __name__ == "__main__":
    main()
