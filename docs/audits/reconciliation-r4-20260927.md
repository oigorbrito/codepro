# Reconciliation R4 — real execution and qualification preservation — 2026-09-27

**Status:** DONE

## Decision

R4 reconciles the current TypeScript/Express surface with the restored Python
execution core and preserves branch-only executor/provider qualification work
without selecting or promoting any external executor.

```text
UI / Express
    ->
src/chassis/vertical.ts
    ->
explicit CODEPRO_PYTHON
    ->
python -m arkx run
    ->
arkx.vertical
    ->
real Git state
real executor command
real changed files
real verifier
persisted evidence
```

No fallback, executor switch, routing decision, provider call, acceptance, or
promotion is introduced by this reconciliation.

## R4-A — real authoritative vertical

Starting reconciliation head:

```text
62fa8607a3e1a34254903ce7b8be3e6cf70b8a4e
```

The TypeScript vertical was replaced by a fail-closed adapter in:

```text
cdcf97c2c444865c361cc2868f1821edc6051ae6
reconcile: bind TypeScript vertical to authoritative Python core
```

The adapter requires explicit runtime bindings:

```text
CODEPRO_PYTHON
CODEPRO_EVIDENCE_DIR
```

It invokes:

```text
python -m arkx run
```

with `spawnSync(..., shell: false)`. It does not synthesize executor results,
changed files, verifier PASS, qualification, acceptance, fallback, or promotion.

### Local clean-checkout verification

Validation was executed from the reconciliation checkout on Windows.

Authoritative Python vertical tests:

```text
tests/test_vertical.py
18 tests
PASS
```

TypeScript/build gates:

```text
Typecheck  = PASS
FrontBuild = PASS
```

Real adapter positive control:

```text
authorized scope = target.txt
actual change     = target.txt
verifier          = real command reading target.txt
status            = VERIFIED
changed_files     = [target.txt]
result.json       = persisted
reason            = DECLARED_VERIFIER_PASSED
```

Negative scope control:

```text
authorized scope = target.txt
actual change     = other.txt
status            = BLOCKED
changed_files     = [other.txt]
reason            = CHANGED_FILES_OUTSIDE_AUTHORIZED_SCOPE
```

Static authoritative-path checks:

```text
simulatedChangedFiles = ABSENT
hardcoded verifier PASS = ABSENT
CODEPRO_PYTHON = PRESENT
CODEPRO_EVIDENCE_DIR = PRESENT
python -m arkx run = PRESENT
shell:false = PRESENT
```

The broader CLI doctor test observed in the same environment rejected Python
3.11 because the restored package requires Python >=3.12. That interpreter
compatibility result is not converted into a vertical execution failure or a
false PASS.

## R4-B — preserve executor/provider qualification assets

The following source heads remain the preservation authorities:

```text
ops/gemini-cli-executor-qualification
  e9212f3c8ff4323e81fbeeaac09c8731359c5789

ops/mini-v246-executor-qualification
  dabbc2dc8dcd835ce5521bb9e9eed60aec48c68b

ops/mini-v246-gemini-api-qualification
  89449861c6839d48ffdbbe5c0b485b15db3b1ed7

ops/mini-v246-runtime-access
  c43c8a5a622d5ddeb9e61fd570d83d5d54e17b53

ops/mini-v246-runtime-access-split
  6e354cc02a722e5665bd640e24d1834a4dbd8bfd

ops/mini-v246-verifier-controls-split
  0bde4a2125809ad914a9bb3a178ff468261be6b5
```

The active qualification/control source files were copied byte-identically
from those branches into the reconciliation line:

```text
.github/workflows/mini-v246-runtime-access.yml
  143369700e029258d9873c7e149a1570bc443662

tools/run_mini_v246_runtime_access.py
  0e4a44fc044863eee946374027aabbb21f8dde5b
tests/test_mini_v246_runtime_access.py
  3002ce770e9d1bf3f1d2ceeb8f1bc3b2175e175a

tools/run_mini_v246_verifier_controls.py
  c7ac62ad88702af7a19e1ea58547a558e4b66bd5
tests/test_mini_v246_verifier_controls.py
  a50c5a3580ed1e0a17ee9e700ec55ee852dab0bc

tools/run_gemini_cli_executor_qualification.py
  5ebce3720a3a22208e6bcf46bb353d98d2875db3
tests/test_gemini_cli_executor_qualification.py
  f6b726991265c88eb55b8a9f3ba82c25c3d52f5e

tools/run_mini_v246_executor_qualification.py
  1a3bb6088af6618eedda8cdb6b75666e1dfda3b6
tests/test_mini_v246_executor_qualification.py
  7be96b104f6db5cff926794523153874a5e5ae85

tools/run_mini_v246_gemini_api_qualification.py
  18830e3c63d87ae1dd3eac6b7836aa7cca555fd9
tests/test_mini_v246_gemini_api_qualification.py
  941c64817e8fd04c030ef8fbeb8d5aad777faed3
```

The historical runtime/verifier evidence branches remain preserved by exact
head. R4 does not rewrite their observations or promote them into current
results.

## Qualification semantics preserved

Runtime access proves only runtime access. Verifier controls prove only the
verifier control boundary. Qualification runners remain explicit qualification
tools rather than product-selection logic.

The imported code retains:

```text
mini-SWE-agent = v2.4.6
mini-SWE commit = a83fcae82d2a08f0ee0c688f9d137b3566c097f8
SWE-bench verifier = 5.0.2
Gemini API model = gemini/gemini-2.5-flash
Gemini API credential = GEMINI_API_KEY
Gemini CLI auth = authenticated CLI account; no Gemini API key
```

Provider-backed qualification runners fail closed unless
`--authorize-provider-call` is explicit. Credential values are not recorded.
They retain:

```text
executor_promotion = NOT_AUTHORIZED
product_binding = NOT_AUTHORIZED
NO_FALLBACK
```

No provider/API call was executed as part of R4-B preservation.

## Gate

```text
REAL_AUTHORIZED_VERTICAL             = PASS
EXECUTION_STATES_DISTINCT           = PASS
OBSERVED_CHANGED_FILE_SCOPE          = PASS
REAL_VERIFIER_EVIDENCE               = PASS
SIMULATED_AUTHORITATIVE_PASS         = ABSENT
AVAILABLE_NE_QUALIFIED               = ENFORCED
NO_SILENT_FALLBACK                   = ENFORCED
NO_SILENT_EXECUTOR_SWITCH            = ENFORCED
QUALIFICATION_ASSETS_PRESERVED       = PASS
PROVIDER_AUTH_SEMANTICS_PRESERVED    = PASS
EXTERNAL_EXECUTOR_PROMOTION          = NOT_AUTHORIZED

R4 = DONE
NEXT_BLOCK = R5
```

R5 owns full composed-repository requalification and the reviewed merge to
`main`.
