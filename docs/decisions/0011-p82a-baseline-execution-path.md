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
are available. B/C/D remain out of scope.
