# 0110 — Codepro project identity and `arkx` namespace

## Status

Accepted. Product and distribution identity is `Codepro`; `arkx` remains the
technical Python namespace until a separately evaluated migration exists.

## Decision

Current and new user-facing documentation, release metadata, experiment
reports, and evidence indexes must identify the product as **Codepro**. The
installed distribution and CLI already use `codepro`.

The import namespace `arkx`, paths under `src/arkx`, and historical evidence
references are preserved for compatibility and traceability. They are not a
second product identity. A namespace migration would be a separate breaking
change requiring import-compatibility tests, artifact migration, and a new
acceptance decision.

The physical workspace path `D:\\projetos\\arkx` is environment state, not
release metadata, and is not renamed by this decision.

## Acceptance criteria

- current README and release-facing documents use Codepro as product name;
- package metadata and CLI remain consistently `codepro`;
- technical references to `arkx` state that it is the Python namespace where
  ambiguity is possible;
- historical logs and audit records are not rewritten;
- no release or qualification status changes as a result of this naming work.

