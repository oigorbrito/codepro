# Verification boundary

`tests/` contains executable verification for the CodePro chassis and empirical contracts.

The suite covers deterministic behavior, fail-closed semantics, serialization, frozen-artifact identity, provenance, planning/verification/handoff boundaries, and adversarial contract cases. `tools/check_foundation.py` remains a repository-level foundation check; it is not a substitute for the executable test suite.

A passing local or CI suite is local implementation evidence only:

```text
LOCAL_PASS != SCIENTIFIC_SIGNAL
TEST_PASS != CAPABILITY_PROMOTED
```
