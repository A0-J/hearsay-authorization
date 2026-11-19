"""Escalation follow-up (SIGX) cells: docs/SIGX_ESCALATION_PREREG_DRAFT.md."""
from __future__ import annotations

from collections import Counter

import pytest

pytest.importorskip("cryptography")

from hearsay.authbench import exp1  # noqa: E402
from hearsay.authbench.locate import DEFAULT_ROOT  # noqa: E402

pytestmark = pytest.mark.skipif(not (DEFAULT_ROOT / "authorization_eva_sandbox").is_dir(),
                                reason="no AuthorizationBench checkout")


@pytest.fixture(scope="module")
def tasks():
    from hearsay.authbench.exp1_tasks import build_tasks
    return build_tasks()


@pytest.fixture(scope="module")
def mods():
    from hearsay.authbench import sigstate, sigx
    return sigstate, sigx


def test_cells_and_labels(tasks, mods):
    sigstate, sigx = mods
    for t in tasks:
        cells = sigx.cells(t)
        assert len(cells) == len({c["cell_id"] for c in cells}) == 4 * 2 * 2 == 16
        assert Counter(c["presentation"] for c in cells) == Counter({p: 4 for p in sigstate.PRESENTATIONS})
        assert {c["instruction"] for c in cells} == {"aware"}
        for c in cells:
            lab = sigx.label(t, c)
            assert lab["expected"] == "reject" and not lab["gate_allowed"]
        for condition in sigx.CONDITIONS:
            assert sigx.forged_id_absent(t, condition)


def test_inputs_are_sigstate_inputs_on_experiment1(tasks, mods):
    sigstate, sigx = mods
    e1 = {c["cell_id"]: c["input"] for t in tasks for c in exp1.cells(t)}
    for t in tasks:
        for c in sigx.cells(t):
            plain = e1[c["e1_cell_id"]]
            assert c["input"] == sigstate.sig_input(t, "invalid", c["condition"], c["claim"], c["presentation"])
            lines = c["input"].split("\n")
            claim_lines = [x for x in lines if x.startswith("claim_check: ")]
            if c["presentation"] == "plain":
                assert c["input"] == plain
                continue
            if c["presentation"] in sigstate.CLAIM_PRESENTATIONS:
                key = "none" if c["claim"] == "none" else sigstate.CLAIM_PRESENTATIONS[c["presentation"]]
                assert claim_lines == [sigstate.CLAIM_LINES[key]]
            else:
                assert claim_lines == []
            assert sigstate.CHECK_LINE in lines


def test_sigstate_cells_unchanged(tasks, mods):
    """SIGX adds no cell to the signed-state experiment."""
    sigstate, _ = mods
    assert all(len(sigstate.cells(t)) == 100 for t in tasks)
    assert not any(c["condition"].startswith("abs_") for t in tasks for c in sigstate.cells(t))
