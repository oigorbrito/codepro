# 0011 — P8.2a baseline execution path

- Status: experimental infrastructure
- Date: 2026-09-23

P8.2a adds a narrow headless adapter around mini-SWE-agent 2.x's public
Python API. A worker process owns the Python environment containing
mini-SWE-agent; Arkx captures logs, trajectory, diff, timestamps, exit state,
and usage metadata. The adapter never invokes verification or acceptance.

Acceptance is represented by an explicit authority contract and keeps
`ACCEPTED`, `REJECTED`, `INDETERMINATE`, `NOT_EXECUTED`, and `BLOCKED`
distinct. Runs are append-only by task and attempt, so reruns cannot silently
replace prior artifacts.

This is infrastructure qualification only. No Wave 0 task sample or real
model run is recorded until the public task artifacts and acceptance authority
are available. The frozen Wave 0 manifest uses the official SWE-bench Verified
test split at revision `78f471bf655a3137b2e8a75af1501690ec009ec3`, and records
`UNKNOWN` strata where no prior auditable Arkx classification exists. B/C/D
remain out of scope.

The official authority adapter serializes only `instance_id`,
`model_name_or_path`, and `model_patch` for inference. It invokes
`swebench.harness.run_evaluation` with a unique run id and maps infrastructure
errors to `INDETERMINATE`/`BLOCKED`, never to task rejection. Gold-patch
qualification is a separate gate. The official package is now available in
the isolated `.venv-swebench` environment (`swebench 5.0.2`, upstream commit
`02e7a74ffd0b707aab73d203fe87bdc7c76afc8e`) and its CLI help passes. The
Modal qualification reached the official harness but is blocked by missing
`~/.modal.toml` credentials. The local Docker Linux engine is also
unavailable. The deterministic headless probe now passes with an explicit
`DeterministicModelConfig.outputs` fixture recorded in
`experiments/p82-deterministic-headless-probe.json`.
