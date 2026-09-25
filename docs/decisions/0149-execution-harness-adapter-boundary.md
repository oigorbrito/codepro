# Decision 0149 — Execution/harness adapter boundary

Date: 2026-09-25

## Result

The PR30 execution/harness cluster cannot be integrated into `main` through a
mechanical adapter at the current boundary.

`main`'s governed spine accepts a bound executor invoker that returns a
`CommandResult`: an observation of one authorized command, including process
status, stdout/stderr, timeout, and environment error. PR30's executor contract
returns an `ExecutionResult`: a lifecycle-classified run with `RunState`,
artifact references, usage, and a harness/provider/executor error envelope.

Those results have different authority and semantics. A conversion from
`ExecutionResult` to `CommandResult` would have to invent an argv, cwd,
process outcome, or command observation. A conversion in the other direction
would have to invent task completion, artifacts, usage, or executor state.
Neither is a valid adapter without a declared execution authority.

## Classification

`ADAPTER_CONTRACT_UNDEFINED`

This is an architectural decision boundary, not a runtime or test failure.
No provider was called and no product behavior was changed.

## Evidence

- `main` boundary: `src/arkx/spine.py::BoundExecutorInvoker.invoke` returns
  `CommandResult`.
- `main` command contract: `src/arkx/command.py::CommandResult` requires
  argv, cwd, exit code, stdout/stderr, timeout state, duration, and environment
  error semantics.
- PR30 boundary: `src/arkx/execution.py::Executor.execute` returns
  `ExecutionResult`.
- PR30 result contract: `ExecutionResult` carries `RunState`, artifact refs,
  usage, and an `ErrorEnvelope`, but no command/process observation.

## Allowed next decisions

1. Make `main`'s governed spine the authority and port PR30 execution to a
   concrete `BoundExecutorInvoker` that produces real `CommandResult` values;
   or
2. Make PR30's execution contract the authority and add an explicit governed
   adapter layer that records command observations before producing
   `ExecutionResult`.

Until one authority is selected, the execution/harness cluster remains
`DEFERRED_ADAPTER_REQUIRED`. No routing, provider, benchmark, or promotion
work should proceed through this unresolved boundary.
