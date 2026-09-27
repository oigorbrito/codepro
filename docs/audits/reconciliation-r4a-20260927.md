# Reconciliation R4-A audit - real vertical adapter

Date: 2026-09-27

## Decision

React / Express: KEEP
src/chassis/vertical.ts: MERGE
src/arkx/vertical.py: authoritative execution core
simulated changed files: DROP - regression
hardcoded verifier PASS: DROP - regression

## Authoritative path

React / Express API
-> TypeScript fail-closed adapter
-> explicit CODEPRO_PYTHON
-> python -m arkx run
-> arkx.vertical
-> real Git state / executor / verifier / persisted evidence

Bindings:
- CODEPRO_PYTHON
- CODEPRO_EVIDENCE_DIR

No implicit Python fallback.
No shell execution.
No executor switch.
No provider invocation.

## Authoritative gate

PythonExecutionCore = 0
Typecheck = 0
FrontBuild = 0
RealVerticalAdapter = 0
AdapterExecution = 0
SimulatedChangedFiles = False
HardcodedVerifierPASS = False
CODEPRO_PYTHON_Present = True
CODEPRO_EVIDENCE_Present = True
PythonModuleInvocation = True
SpawnWithoutShell = True

Positive control:
status = VERIFIED
reason = DECLARED_VERIFIER_PASSED
changed_files = target.txt
result.json = persisted

Negative control:
status = BLOCKED
reason = CHANGED_FILES_OUTSIDE_AUTHORIZED_SCOPE
changed_files = other.txt

R4-A = DONE
R4-B = NEXT
R4 = IN_PROGRESS

PRESERVE_IMPLEMENTATION != PROMOTE_EXECUTOR
EXECUTED != VERIFIED
VERIFIED != ACCEPTED
ACCEPTED != PROMOTED
