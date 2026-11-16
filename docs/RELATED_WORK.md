# Related work and how this study differs

Checked 2026-11-16. "Read" means the full text was read; "abstract" means only the abstract or the
conference page was available. Novelty claims need a full item-by-item comparison before submission.

## Closest work

| work | what it manipulates | what the verifier sees | evidence channel | outcome measured | read |
|---|---|---|---|---|---|
| *Silence Is Endorsement: Verification-Status Laundering in LLM Agent Pipelines* (Hu, arXiv:2609.20211, 2026) | the verification-status framing around a fixed claim: no claim / "(UNVERIFIED)" marker / marker lost / "VERIFIED" | a handoff note and the action (hand-authored 56 items; WildGuard; ATBench) | none: no approval record, registry or lookup | monitor approve/refuse (forced-choice log-probabilities for 9 open models ≤ 32B; 5 samples for DeepSeek-V4-Flash and GPT-4o-mini); a summarizer–memory–monitor pipeline | full text |
| *Do Verifier Judgments Survive Abstraction? Measuring Verification Transport for LLM Agent Evaluation* (NeurIPS 2026) | how much execution evidence a verifier sees (native / abstracted / restored) | frozen trajectories of 4 agent benchmarks; 7 verifier backbones | execution provenance, restored or lossy | stability of task-outcome judgements; restoring provenance recovers ~85.5% of failures, less when provenance is lossy or unavailable | abstract |
| *Act on Your Behalf, Beyond Your Authorization* (AuthorizationBench; Zhang et al., arXiv:2610.27548, 2026) | situational triggers in 286 executable tasks | the acting agent itself (no separate verifier) | the task contract (evaluation only) | out-of-authorization actions in sandboxed services | full text |

## What *Silence Is Endorsement* already establishes

- An unsupported authorization claim raises approval relative to no claim. Its Δclaim = p(marker lost) −
  p(no claim) is the same contrast as our Δ_claim **without** an evidence channel.
- Ordinary summarizers and memory compressors drop the "unverified" status. A full pipeline raises risky
  approval to 57–81%.
- An explicit instruction to reject unverified authorization is not a reliable cross-model fix: residual
  vulnerability in some models, over-refusal in others.
- It recommends carrying verification status as structured state bound to the claim, and states that it
  does not implement or validate such an architecture. Its appendix J tests a **structured in-band**
  carrier (a JSON status field or typed tags inside the handoff) and finds that whether it survives a
  summarizer depends on the summarizer, not the format.

So "a downstream verifier believes an upstream claim" and "prompting is not a reliable fix" are prior
results. This study must not claim them.

## Where this study differs

1. **Runtime-managed, out-of-band evidence.** Every evidence-provided verifier receives a policy (π) and an
   approval state (σ) that a trusted runtime looks up from the action, outside the handoff and
   independent of the claim. *Silence Is Endorsement* studies status carried in the handoff, structured
   or not. The question here is whether claims still change decisions once such external evidence is
   present, and how that depends on the evidence's completeness and uncertainty states: **Claim
   Non-Amplification**, Allow(a, π, σ, c) = Allow(a, π, σ, ∅).
2. **The state of the evidence is the manipulated variable.** It can be valid, silently absent, explicitly
   absent, explicitly invalid (expired, revoked, out of scope), mismatched (wrong id, other valid
   approval), unavailable, or partial. The pilot's observation concerns exactly this split. Claims were
   promoted to authority when the record was silent (fabricated: 45% with the claim, 0% without; meeting
   tasks only). They were never promoted when the record held an explicit invalidity (expired, revoked,
   out of scope: 0%). This is exploratory; the condition was singled out after seeing the data.
3. **Original executable tasks and real tool calls.** Probes are calls in AuthorizationBench's own tool
   schemas and services, built by rule from the original fixtures, not hand-authored items. The
   end-to-end experiment measures service state changes, not only monitor decisions.
4. **Authorization and intent are separate labels.** The semantic check is supplementary, not the main
   contribution.

## Other related lines (from the papers above, not yet read)

Semantic laundering across agent interfaces (Romanchuk & Bondar, arXiv:2601.08333); provenance-based
defenses (Wang et al., arXiv:2605.26497; Zhu et al., arXiv:2602.17913); governing agent memory (Lam et al.,
arXiv:2603.11768); consent integrity for black-box agents (arXiv:2606.02668). To read before writing the
related-work section.

Sources: [arXiv:2609.20211](https://arxiv.org/abs/2609.20211),
[NeurIPS 2026 page](https://neurips.cc/virtual/2026/173017), [arXiv:2610.27548](https://arxiv.org/abs/2610.27548).
