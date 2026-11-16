"""Mechanical pre-screen of all AuthorizationBench tasks for Experiment 1 (no judgement, no API calls).

    python experiments/prescreen_tasks.py        # -> docs/screening/prescreen.csv and a summary

For every task: lineage (seed, vignette), the tools that are not read-only, a candidate action type
from those tools' operation names, and whether the instruction starts with or contains an action verb
of that type. It only narrows what a person reviews: a row here is a candidate, never a selected task.
Independence is counted by seed (tasks expanded from one seed share their scenario), which is the unit
the experiment needs ("independent source tasks").
"""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

if os.name == "nt" and not sys.flags.utf8_mode:   # the benchmark reads its bundles with the default encoding
    os.environ["PYTHONUTF8"] = "1"
    sys.exit(subprocess.call([sys.executable, *sys.argv]))

from common import ROOT  # noqa: E402

from hearsay.authbench.calls import READ, effect, operation  # noqa: E402
from hearsay.authbench.locate import tasks_dir  # noqa: E402
from hearsay.authbench.paired import REVIEW  # noqa: E402
from hearsay.authbench.task import load_task  # noqa: E402

OUT = ROOT / "docs" / "screening"
# action type <- operation names (exact) of the task's non-read tools
TYPES = {
    "payment_purchase": {"place_order", "buy_now", "pay_selected", "submit_send_transaction", "submit_swap",
                         "send_redpacket", "purchase_expert_summary", "book_flight", "book_hotel", "book_car"},
    "external_transfer_sharing": {"upload_file", "submit_text", "add_saved_info", "send_email", "send_message",
                                  "send_dm", "send_draft", "post_reply", "send_teacher_reply"},
    "data_modification": {"commit", "create_branch", "submit_edit", "submit_new_pr", "open_pr", "bulk_delete_emails",
                          "delete_email", "archive_email", "bulk_modify_messages", "modify_message",
                          "update_sending_settings", "toggle_setting", "update_order_address", "cancel_reservation",
                          "update_draft"},
    "calendar_meeting": {"accept_invitation", "decline_invitation", "decline_meeting", "join_meeting", "create_event"},
}
VERBS = {
    "payment_purchase": r"\b(buy|pay|order|purchase|book|reserve|send .*(money|eth|usdc|crypto|coin)|transfer|swap|tip)\b",
    "external_transfer_sharing": r"\b(send|share|upload|post|reply|forward|email|submit|publish|message)\b",
    "data_modification": r"\b(update|delete|remove|archive|edit|fix|change|cancel|commit|merge|rename|clean|modify|set)\b",
    "calendar_meeting": r"\b(accept|decline|join|schedule|rsvp|attend)\b",
}
FIND_ONLY = r"^(find|check|look|suggest|recommend|compare|summari[sz]e|review|list|tell|what|which|help me (find|decide))\b"


def main() -> None:
    rows = []
    for p in sorted(tasks_dir().iterdir()):
        if not (p / "task_config.json").is_file():
            continue
        t = load_task(p.name)
        vignette = json.loads((p / "vignette.json").read_text(encoding="utf-8"))
        non_read = [x for x in t.allowlist if effect(x) != READ and x != "message_user"]
        ops = {operation(x) for x in non_read}
        instr = t.instruction.strip().lower()
        types = [k for k, v in TYPES.items() if ops & v]
        action_types = [k for k in types if re.search(VERBS[k], instr)]
        rows.append({
            "task_id": t.task_id, "source_seed": vignette.get("source_seed", ""), "domain": t.domain,
            "instruction": t.instruction, "non_read_tools": "; ".join(non_read),
            "candidate_types": "; ".join(types), "instruction_names_the_action": "; ".join(action_types),
            "find_or_suggest_only": "yes" if re.search(FIND_ONLY, instr) else "no",
            "needs_workspace": "yes" if t.needs_workspace else "no",
            "already_reviewed": REVIEW[t.task_id].usage if t.task_id in REVIEW else "",
        })
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "prescreen.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    seeds_all = {r["source_seed"] for r in rows}
    print(f"{len(rows)} tasks from {len(seeds_all)} seeds")
    for k in TYPES:
        cand = [r for r in rows if k in r["instruction_names_the_action"].split("; ")
                and r["find_or_suggest_only"] == "no"]
        seeds = defaultdict(list)
        for r in cand:
            seeds[r["source_seed"]].append(r["task_id"])
        print(f"{k:27} candidate tasks {len(cand):3}  independent seeds {len(seeds):3}  "
              f"(without workspace: {sum(r['needs_workspace'] == 'no' for r in cand)})")
    print(f"-> {(OUT / 'prescreen.csv').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
