# Phase 5 - CodePro local-runtime plumbing audit

Date: 2026-09-28

Frozen path: CodePro -> loopback llama-server -> exact model alias -> response -> telemetry.
Reference fixture: L3 Granite 4.2 3B.
REFERENCE_FIXTURE != SELECTED_MODEL
COMPATIBLE != PROMOTED

Endpoint: http://127.0.0.1:18088/v1
Model alias: codepro-phase5-granite42-3b
Timeout: 30 seconds
Fallback: DISABLED
Failure boundaries: HTTP, RUNTIME, MODEL, TIMEOUT, PROTOCOL.

Smoke classification: LOCAL_RUNTIME_PLUMBING_PASS
Probe semantics graded: False
Response observed: True
Response content length: 46
Response content SHA256: 215875dda4c6c433cc8c6fbfb7d3fce6b9bf793b0d391c27743c4c21527b2bb4
Telemetry complete: True
Wall time ms: 548
Prompt tokens: 20
Completion tokens: 10
Total tokens: 30
Provider API cost USD: 0
Server termination: PASS

Diagnostic attempts are preserved under evidence/phase5-local-runtime/diagnostics/.
Attempt 1 exposed a 16-token harness truncation.
Attempt 2 showed freeform response variance with a healthy transport.
Attempts 3 and 4 independently reproduced the same HTTP 500 grammar incompatibility for constrained chat on this frozen model/template path.
None of those semantic/grammar behaviors is promoted into the Phase 5 plumbing gate.

PHASE_5 = COMPLETE
Evidence: evidence/phase5-local-runtime/frozen-smoke/
Next: Phase 6 - execution and verifier plumbing.
