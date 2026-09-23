# ADR 0021 — Minimal installable CLI boundary

## Status

Superseded by ADR 0022. This record preserves the CLI decision as originally accepted before the product rename.

## Observed need

The executor-agnostic chassis was importable and its baseline module was runnable, but an empirical CLI probe showed that:

- no installable project metadata existed;
- no `dekon` command existed;
- `python -m arkx` had no entrypoint;
- help/version behavior could not be exercised as a product interface.

The missing CLI was a product-surface gap, not evidence for adding orchestration.

## Decision

Add the minimum installable CLI boundary:

- standard-library `argparse` only;
- zero runtime dependencies;
- `dekon` as the public console command;
- `python -m arkx` as the equivalent module entrypoint;
- `--help`, `--version`, and `doctor` only;
- no executor invocation, routing side effects, interactive TUI, configuration mutation, or task execution.

The existing Python implementation namespace remains `arkx` for this change. Renaming the package namespace is a separate migration and must not be coupled to CLI introduction.

## Empirical acceptance

The CLI is acceptable only if CI demonstrates:

1. editable installation succeeds;
2. `dekon --help` exits zero;
3. `dekon --version` exits zero with an explicit version;
4. `dekon doctor` exits zero on supported CI interpreters;
5. `python -m arkx --help` is equivalent at the entrypoint boundary;
6. the existing chassis suite, mutation probe, semantic fingerprint, and Python 3.12/3.13/3.14 compatibility remain green.

## Alternatives

- Add Typer/Click: rejected because the current surface does not justify a runtime dependency.
- Add an interactive prompt now: rejected because no executor invocation contract has been promoted.
- Rename the Python package to `dekon` in the same change: rejected because it increases migration scope without improving CLI capability.

## Removal condition

Replace this CLI layer only if a simpler interface preserves installability, deterministic exit semantics, zero silent execution, and the same tested product boundary.
