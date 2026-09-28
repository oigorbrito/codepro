# Reconciliation R4-B audit - executor/provider assets

Date: 2026-09-27

## Source identities

Gemini CLI:
e9212f3c8ff4323e81fbeeaac09c8731359c5789

mini-SWE-agent v2.4.6 executor:
dabbc2dc8dcd835ce5521bb9e9eed60aec48c68b

mini-SWE-agent v2.4.6 Gemini API:
89449861c6839d48ffdbbe5c0b485b15db3b1ed7

runtime access:
c43c8a5a622d5ddeb9e61fd570d83d5d54e17b53

runtime access split:
6e354cc02a722e5665bd640e24d1834a4dbd8bfd

verifier controls split:
0bde4a2125809ad914a9bb3a178ff468261be6b5

## Reconciliation disposition

Gemini CLI qualification: MERGE
mini-SWE v2.4.6 qualification: MERGE
Gemini API qualification: MERGE
runtime-access controls: MERGE
verifier controls: MERGE

Historical raw evidence remains preserved in its source branches.
Raw branch ancestry was not merged into the reconciled branch.

No src/arkx boundary was replaced.
No src/chassis boundary was replaced.
No frontend/server boundary was replaced.

## Preserved semantics

mini-SWE-agent = v2.4.6
mini-SWE-agent SHA = a83fcae82d2a08f0ee0c688f9d137b3566c097f8
Gemini API model = gemini/gemini-2.5-flash
Gemini API credential = GEMINI_API_KEY
Gemini CLI authentication != GEMINI_API_KEY
SWE-bench verifier = 5.0.2
runtime-access provider call = NOT_EXECUTED
executor promotion = NOT_AUTHORIZED

## Integration validation

qualification tool compilation = PASS
focused qualification contract tests = PASS
Python vertical regression = PASS
CLI regression = PASS
qualification regression = PASS when present
project/availability regression = PASS when present
TypeScript typecheck = PASS
frontend build = PASS

No qualification runner was executed during integration.
No provider/model call was made during integration.
No paid API is required by this integration gate.

AVAILABLE != QUALIFIED
QUALIFIED != SELECTED_BY_RANK
EXECUTED != VERIFIED
VERIFIED != ACCEPTED
ACCEPTED != PROMOTED

NO_SILENT_FALLBACK
NO_SILENT_EXECUTOR_SWITCH
NO_SILENT_SCOPE_EXPANSION

R4-B = DONE
R4 = DONE
R5 = NEXT
