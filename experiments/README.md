# Experiments

This directory contains small, intentional fixtures and experiment metadata governed by [the experimental protocol](../docs/experimental-protocol.md).

Synthetic fixtures exercise contract semantics and deterministic behavior. They are not treatment runs, benchmark results, scientific evidence, or promotion evidence unless an explicitly frozen study executes them as observations.

Generated raw runs and artifacts stay outside version control under the ignored `runs/` and `artifacts/` paths unless intentionally preserved as small reviewable fixtures.

```text
SYNTHETIC_FIXTURE != EMPIRICAL_RUN
EMPIRICAL_RUN != ACCEPTED_RESULT
ACCEPTED_RESULT != PROMOTED
```
