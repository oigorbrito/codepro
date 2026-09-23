# Decision 0017 — Executor, provider and sandbox contracts

## Status

Accepted as the second architecture strengthening block.

## Decision

Introduce small protocols for `Executor`, `Provider` and `Sandbox`, plus
serializable request/result boundaries. The executor returns execution state
and artifacts only; verification, acceptance, promotion and routing remain
outside the protocol.

Provider failures use the common error envelope. Missing provider/model
identity remains explicit and does not select a fallback.

## Falsifiable hypothesis

If the core flow depends only on these protocols, deterministic fakes can
exercise completed, failed and blocked paths without importing mini-SWE-agent,
OpenRouter, Docker or SWE-bench.

## Acceptance criteria

- fake executor, provider and sandbox tests pass;
- failed/blocked execution requires a structured error;
- provider and sandbox can be replaced independently;
- missing provider/model identity remains `None`;
- no real executor/provider is selected or promoted by this block.
