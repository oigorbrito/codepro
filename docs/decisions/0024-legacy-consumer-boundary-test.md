# Decision 0024 — Legacy consumer boundary test

## Status

Accepted as the ninth architecture strengthening block.

## Decision

The legacy orchestration result is confined to `orchestration.py` and the
explicit package compatibility alias. A static architecture test prevents new
core modules from importing that result directly.

## Falsifiable hypothesis

If legacy consumers are checked continuously, future neutral modules cannot
silently reintroduce the executor-dependent result boundary.

## Acceptance criteria

- no forbidden legacy imports exist in core modules;
- public neutral and legacy result names remain distinct;
- the boundary test runs with the contract suite;
- existing orchestration compatibility remains intact.
