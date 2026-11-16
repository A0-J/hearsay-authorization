"""Hearsay on AuthorizationBench: original tasks, the benchmark's real HTTP services, a verifier in front of
every state-changing business call, and an independent approval record.

  locate     where the pinned AuthorizationBench checkout is, and making it importable
  task       one task bundle as the runtime needs it (instruction, sealed prompt, tool allowlist)
  calls      which business calls change state (and therefore pass the verifier)
  approvals  the independent approval record: lookup, validity window, revocation, issuer authority, scope
  verify     the verification methods; every method can judge the same proposed call (shadow evaluation)
  planner    the planner agent that writes the delegation message
  runtime    one episode: environment up, planner, executor, routed tool calls, artifacts
  selfcheck  checks the routed path against a live environment without any LLM call
"""
