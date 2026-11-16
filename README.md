# Hearsay Is Not Authorization

Evidence-grounded verification of inherited authorization claims in multi-agent delegation
(a DualFlow follow-up).

An upstream agent tells a downstream agent that a task is authorized. The downstream agent cannot
see whether that is true. This project puts real tool-using agents in that position, lets the claim
and the independent approval record disagree, and measures what actually gets executed under five
verification methods: none, an LLM verifier with the claim only, an LLM verifier with the record as
evidence, a provenance-checking authorization gate, and a DualFlow-style semantic + provenance gate.
Both sides are measured: unauthorized execution, and legitimate standing approvals wrongly blocked.

The design, conditions, measures and hypotheses are in [PLAN.md](PLAN.md).

## Layout

| path | what |
|---|---|
| `src/hearsay/scenarios.py` | 8 base tasks × 8 claim/record conditions = 64 scenarios |
| `src/hearsay/records.py` | approval records, issuer authority, the provenance gate (ground-truth semantics) |
| `src/hearsay/agent_loop.py` | tool-using agent on the OpenAI Responses API (function calling, multi-turn) |
| `src/hearsay/sandbox.py` | the executor's tools as mock services; state-changing calls pass the guard |
| `src/hearsay/guards.py` | the five verification methods |
| `src/hearsay/episode.py` | coordinator agent → executor agent → sandbox; outcome from executed effects |
| `src/hearsay/prompts.py` | every instruction the agents and verifiers receive |
| `src/hearsay/fake.py` | a fake client for dry runs and tests (0 API calls) |
| `experiments/run.py`, `analyze.py` | collection (parallel, resumable) and tables |

## Running

```bash
pip install -e .[dev]
python -m pytest                                                     # 0 API calls

PYTHONPATH=src python experiments/run.py --dry-run --workers 4        # whole pipeline, fake client
PYTHONPATH=src python experiments/analyze.py results/dry_run

# real agents: put the key in openai_api_key.txt (gitignored) or set OPENAI_API_KEY
PYTHONPATH=src python experiments/run.py --name pilot --workers 8
PYTHONPATH=src python experiments/analyze.py results/pilot
```

Useful options: `--methods`, `--conditions`, `--bases`, `--repeats`, `--executors gpt-4o-mini gpt-4.1`,
`--delegation scripted` (fixed claim text, no coordinator agent), `--record-lookup` (the executor can
query the approval system), `--resume` (re-run errored episodes only).

Each episode in `results/<name>/episodes.jsonl` keeps every model output, tool call, guard decision
and verifier vote.

## AuthorizationBench runtime (in progress)

The runtime is moving onto original [AuthorizationBench](https://github.com/PEACH-Research-Lab/AuthorizationBench)
tasks and the benchmark's own HTTP services; see PLAN.md §9 for the design and its status.

| path | what |
|---|---|
| `src/hearsay/authbench/task.py` | a task bundle: instruction, sealed prompt, blueprint tool allowlist |
| `src/hearsay/authbench/runtime.py` | environment, the router every executor call goes through, one episode |
| `src/hearsay/authbench/calls.py` | which business calls change state (and pass the verifier) |
| `src/hearsay/authbench/approvals.py` | the independent approval record |
| `src/hearsay/authbench/verify.py` | verification methods, all judging the same proposal (shadow) |
| `src/hearsay/authbench/selfcheck.py` | blocked calls never reach the service (live check, 0 API calls) |
| `src/hearsay/authbench/paired.py` | the dataset spec: selected tasks, policy, claim, probes, six approval conditions |
| `src/hearsay/authbench/dataset.py` | reading the dataset at run time (ground truth only for evaluation) |
| [`dataset/`](dataset/README.md) | the Hearsay pilot dataset: lineage, selection of all 286 tasks, policy, approval states, labels |
| `experiments/run_authbench.py`, `replay_verifiers.py` | episodes; re-judging saved proposals |

```bash
python experiments/fetch_authbench.py                 # clone the benchmark at the pinned commit
pip install -e .[dev,authbench]
# Windows: set PYTHONUTF8=1 (the benchmark reads its UTF-8 bundles with the default encoding)
python -m hearsay.authbench.selfcheck --task T0010-l-b-h
python experiments/run_authbench.py --task T0010-l-b-h --dry-run      # 0 API calls
python experiments/run_authbench.py --task T0010-l-b-h --name smoke   # gpt-4.1 for every role
python experiments/build_dataset.py                  # regenerate dataset/ from the spec
python experiments/run_authbench.py --task T0007-a-g-h --condition valid fabricated --dry-run
```

Only tasks without workspace tools run so far (10 of 286); the rest need the benchmark's Docker
agent container, which is not wired yet.
