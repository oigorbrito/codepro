# Reconciliation R5 — composed repository requalification — 2026-09-27

**Status:** IN_PROGRESS / BLOCKED_EXECUTION_ENVIRONMENT

## Candidate identity

```text
main_at_precheck = 075b6f944ff7c4245139f6f0845ac2db45f31d42
reconciliation_head_after_r4 = dc021094dbd0a59641b50b86bd261a6d02f97b43
r5_validation_maintenance = 32a7447a90157923546639252c88d370e8bc09eb
branch = reconcile/04a-capability-recovery
```

At the R5 precheck, the reconciliation branch was six commits ahead of
`main` and zero commits behind. Published `main` history has not been
rewritten.

## Preservation precheck

Useful post-deviation assets remain byte-identical to `main`:

```text
server.ts                              2f9e5e403fc11d300bdfbf38274675c0c6b1e0ee
src/App.tsx                            69dc0b53a28888c4e7a50470017282f2b2b697e7
package.json                           d807bc73c9522d5af12080b2a9bfb84944f6a688
tsconfig.json                          c27c5496b1ec3809b95fd885a0a7b0a6f4bee19f
src/chassis/inspection.ts              288bc820c1536d5c8306950d6e89249cb419561d
experiments/runtime-telemetry-fixture.json
                                      6001658e143807b41a1a7a4a86a021a34406382a
AGENTS.md                              ca1df9ce6474f08f90d51e793f48a549c82bba73
```

Representative restored operational assets remain byte-identical to the exact
recovery predecessor `cc44d80a06f2967d3d6e7030409a692921dd6b0a`:

```text
pyproject.toml                         b2d816bc2f6ccf0cdedf247a4ca03fa922739485
src/arkx/spine.py                      27c0e1b506030fc0b9d16b2e64222be9ec327eeb
src/arkx/vertical.py                   ba9e7cfca51ccb2c49fce794d00309cb35d0c378
tests/test_vertical.py                 1801436e6b302f68cef472fb8cb4b4fb01c7dcfc
```

Intentional reconciled changes remain localized to the boundaries already
authorized by R3/R4, including telemetry naming/compatibility and the
TypeScript-to-Python real execution adapter.

## CI / validation consistency maintenance

R2 identified the final `spine-ignore-request-scope` mutation anchor as stale:
the probe expected a predecessor expression that no longer matched the restored
`spine.py` shape. The mutation was never observed to survive; the validator
aborted before applying it.

R5 repaired only the validator anchor in:

```text
32a7447a90157923546639252c88d370e8bc09eb
test: repair stale spine mutation anchor for reconciliation
```

The mutation still tests the same invariant: removing the
characterization-candidate-files / requested-scope rejection must be killed by
`tests.test_spine`. The production `src/arkx/spine.py` blob remains unchanged
from the recovery predecessor.

This repair is necessary because `.github/workflows/foundation.yml` executes
`tools/mutation_probe.py`; carrying the known-stale anchor into the final
reconciled state would make a healthy CI runner fail for validator maintenance
rather than product behavior.

## Existing R4 execution evidence retained

The real TypeScript adapter was locally validated before R4 closure with:

```text
Python vertical focused tests = PASS (18)
Typecheck                     = PASS
Frontend build                = PASS
Real adapter positive control = VERIFIED
Observed changed_files        = [target.txt]
Persisted result.json         = PRESENT
Negative scope control        = BLOCKED
Negative changed_files        = [other.txt]
simulatedChangedFiles         = ABSENT
hardcoded verifier PASS       = ABSENT
```

R5 must rerun the composed state after R4-B and the mutation-probe maintenance;
historical R4 evidence is not substituted for the R5 gate.

## GitHub Actions availability

Recent pull-request Foundation execution observed a job-level failure with no
step payload and a skipped compatibility job. No executed test step produced a
failure. This remains classified as runner/infrastructure non-execution:

```text
INFRA_FAILURE != IMPLEMENTATION_FAILURE
NOT_EXECUTED  != PASS
```

Therefore R5 requires a fresh clean local requalification while hosted runner
execution is unavailable.

## Required R5 execution gate

From a clean worktree at the exact reconciliation head:

```text
SUPPORTED_PYTHON_3_12_PLUS
PACKAGE_INSTALL
CLI_VERSION
CLI_DOCTOR
CLI_INSPECT
FOUNDATION_CHECK
BASELINE
FULL_PYTHON_TEST_SUITE
MUTATION_PROBE
CHASSIS_FINGERPRINT
PYTHON_COMPILE
R4B_QUALIFICATION_CONTRACT_TESTS
NODE_INSTALL
TYPESCRIPT_TYPECHECK
LOCAL_INFERENCE_TELEMETRY_CHECK
FRONTEND_BUILD
REAL_TS_TO_PYTHON_VERTICAL_POSITIVE
REAL_TS_TO_PYTHON_VERTICAL_NEGATIVE_SCOPE
```

No provider-backed qualification runner is to be invoked during this gate.
No credential is required. No external executor is selected or promoted.


## Hosted R5 gate

Because the user-local PowerShell environment is temporarily unavailable, the
repository now carries a provider-free hosted requalification gate:

```text
tools/check-r5-composed-vertical.ts
.github/workflows/reconciliation-r5.yml
```

The workflow covers:

```text
Python 3.13 package install
CLI version / doctor / inspect
foundation check
baseline
full Python unittest suite
mutation sensitivity probe
chassis fingerprint
Python compile
Node 22 dependency install
TypeScript typecheck
local-inference telemetry validation
frontend build
authoritative adapter static checks
real TS -> Python positive control
real TS -> Python negative scope control
provider-safety check
```

The workflow contains no provider credential binding and does not invoke the
Gemini CLI, Gemini API qualification runner, or Anthropic-backed qualification
runner.

A validation-only draft pull request was opened:

```text
PR #80
reconcile/04a-capability-recovery -> main
state = DRAFT
merge = NOT_AUTHORIZED_PENDING_R5
```

The Windows llama.cpp smoke remains the only environment-specific check that
cannot be reproduced by the hosted Linux gate. Its prior Phase 2 qualification
remains preserved; R5 will not fabricate a fresh Windows observation.

## Hosted execution observation

The first hosted R5 workflow definition contained a self-check defect in the
`provider-safety` job: literal forbidden tokens appeared in the grep commands
that searched the workflow itself. That validator defect was corrected in:

```text
09c2ff300c2b02b72fc5e1f106dd7f37cdda61e6
ci: make R5 provider-safety check non-self-matching
```

The corrected workflow contains no literal provider credential variable and no
literal provider qualification runner command. Its safety check constructs the
forbidden tokens dynamically and inspects the workflow text.

Pull-request checks on the corrected head produced:

```text
Reconciliation R5        run 36346515666
  python-foundation                failure / 0 steps executed
  typescript-and-real-vertical     failure / 0 steps executed
  provider-safety                  failure / 0 steps executed

Foundation               run 36346515633
  foundation                       failure / 0 steps executed
  compatibility                    skipped

TypeScript telemetry     run 36346515608
  telemetry-contract               failure / 0 steps executed
```

An earlier failed Foundation run was explicitly rerun and again produced a
job-level failure with no steps. Job-log retrieval had no log blob because no
step execution occurred.

Because three independent workflows, including a trivial provider-safety job,
all fail before their first step, these results are classified as hosted runner
non-execution rather than implementation-test failures.

```text
INFRA_FAILURE != IMPLEMENTATION_FAILURE
ZERO_STEPS_EXECUTED != TEST_FAILURE
ZERO_STEPS_EXECUTED != PASS
```

The R5 execution gates remain pending. The reconciliation PR stays draft and
`main` remains unchanged.

## External service status cross-check

At the time of this audit, the public GitHub Status API reported:

```text
GitHub overall = All Systems Operational
Actions        = operational
```

Therefore the observed zero-step failures are not attributed to a confirmed
global GitHub Actions incident. The remaining blocker is classified only as
repository/account execution provisioning unavailable from the evidence
currently exposed to this project.

Possible account/repository causes such as private-repository Actions quota,
budget/billing, or Actions policy/settings remain hypotheses until directly
observed. They are not recorded as established cause.

```text
GLOBAL_ACTIONS_OUTAGE_CONFIRMED = FALSE
ACCOUNT_OR_REPO_CAUSE_CONFIRMED = FALSE
EXECUTION_ENVIRONMENT_AVAILABLE = FALSE
```

## Minimal runner scheduling probe

To isolate repository code and action dependencies from runner provisioning, R5
temporarily added a one-job diagnostic workflow with:

```text
runner = ubuntu-slim
checkout = NONE
setup-python = NONE
setup-node = NONE
command = echo + uname
```

Observed run:

```text
Actions runner diagnostic
run 36347693088

schedule-probe = failure
steps executed = 0
```

In the same synchronization event:

```text
Reconciliation R5 run 36347693076
  python-foundation                failure / 0 steps
  typescript-and-real-vertical     failure / 0 steps
  provider-safety                  failure / 0 steps

Foundation run 36347693102
  foundation                       failure / 0 steps
  compatibility                    skipped
```

This materially narrows the blocker:

```text
CODEPRO_SOURCE_FAILURE             = NOT_OBSERVED
CHECKOUT_ACTION_FAILURE            = NOT_REQUIRED_TO_REPRODUCE
PYTHON_SETUP_FAILURE               = NOT_REQUIRED_TO_REPRODUCE
NODE_SETUP_FAILURE                 = NOT_REQUIRED_TO_REPRODUCE
UBUNTU_24_04_SPECIFIC_FAILURE      = NOT_REQUIRED_TO_REPRODUCE
RUNNER_PROVISIONING_NON_EXECUTION  = OBSERVED
```

The public GitHub Status API reports Actions operational, so no global incident
is established. Account/repository-specific Actions provisioning remains the
bounded blocker classification; billing/quota/budget/policy remain possible but
unconfirmed subcauses.

The temporary scheduling workflow is not part of the reconciled product and is
removed after capturing this evidence.

## Billing / quota observation

The repository owner reports that billing is currently zero.

For this private repository, GitHub-hosted Actions usage is subject to the
account's included Actions allowance. GitHub documents that usage is blocked
after the included quota is exhausted when no valid payment method is available;
a budget configured to stop usage at its limit can also stop metered usage.

The user-reported zero billing state is therefore consistent with the observed
zero-step runner provisioning failures, but it does not by itself distinguish
among:

```text
INCLUDED_ACTIONS_QUOTA_EXHAUSTED
NO_VALID_PAYMENT_METHOD_FOR_OVERAGE
ZERO_OR_REACHED_ACTIONS_BUDGET_WITH_STOP_USAGE
OTHER_ACCOUNT_OR_REPOSITORY_ACTIONS_POLICY
```

No connector-visible billing/quota endpoint is available in this project, so
the precise subcause remains unverified.

```text
BILLING_ZERO_REPORTED                = TRUE
BILLING_ZERO_EXPLAINS_PATTERN        = PLAUSIBLE
EXACT_BILLING_OR_QUOTA_SUBCAUSE      = UNVERIFIED
RUNNER_PROVISIONING_NON_EXECUTION    = OBSERVED
```

## Product-surface reconciliation gap found during closure review

A full R1-to-R5 matrix review found one remaining reconciliation gap that is
independent of the hosted-runner blocker.

The real vertical endpoint is already bound to the authoritative Python core,
but the Express/API product surface still exposes separate TypeScript semantic
implementations for:

```text
/api/characterize       -> src/chassis/characterization.ts
/api/assess-progress    -> src/chassis/progress.ts
/api/routing            -> src/chassis/routing.ts
/api/m1/review          -> src/chassis/m1Acceptance.ts
```

The React UI calls the routing and M1 review endpoints, so these are not merely
dead compatibility files.

The Python package contains the proven characterization, progress, routing, and
independent-acceptance contracts, but the current Python CLI exposes only
`doctor`, `inspect`, and `run`. Therefore the standalone TypeScript
endpoints have not been rebound to the proven Python semantics.

The TypeScript P1/P2/P3 contracts are also not schema-identical to the Python
contracts (for example, progress/routing states and outputs differ). The M1
TypeScript review can independently emit `ACCEPTED` from a submitted summary,
rather than consuming the authoritative Python acceptance record/evidence
boundary.

The Express doctor surface is also stale relative to R4:

```text
server.ts:
  Python Interpreter (Optional/Legacy)
  python check excluded from overall doctor status

src/chassis/vertical.ts:
  CODEPRO_PYTHON is mandatory
  implicit fallback is disabled
```

This is a product-surface consistency issue, not a missing-file restoration
issue.

Required disposition before R5 closure:

```text
P1/P2/P3 TypeScript surfaces:
  REBIND to authoritative Python semantics
  OR explicitly DEMOTE to non-authoritative preview/compatibility surfaces

M1 TypeScript acceptance:
  REBIND to independent Python acceptance evidence
  OR DEMOTE so it cannot issue authoritative ACCEPTED

Express doctor:
  report the explicit CODEPRO_PYTHON execution dependency accurately
  and fail/limit health semantics consistently with the real vertical
```

No executor/provider change, fallback, routing promotion, or paid API call is
authorized by this corrective item.

```text
MISSING_HISTORICAL_FILES                    = FALSE
POST_DEVIATION_FILES_DELETED               = FALSE
TS_P1_P2_P3_CANONICALITY_RESOLVED           = FALSE
TS_M1_ACCEPTANCE_CANONICALITY_RESOLVED      = FALSE
EXPRESS_DOCTOR_REAL_CORE_ALIGNMENT          = FALSE
```

## Historical ops-branch evidence retention

The active qualification/control source files needed for the reconciled code
line are already present in the reconciliation branch. Historical raw evidence
from the split branches remains branch-bound by design, including runtime-access
and verifier-control logs.

The exact preservation heads remain:

```text
ops/mini-v246-runtime-access-split
  6e354cc02a722e5665bd640e24d1834a4dbd8bfd

ops/mini-v246-verifier-controls-split
  0bde4a2125809ad914a9bb3a178ff468261be6b5
```

This is not a missing-file restoration gap because the evidence remains
reachable at its recorded immutable commit identity. However, these branches
must not be deleted as cleanup unless their raw evidence is first retained by an
explicit durable mechanism such as a preserved tag/branch or an intentional
evidence import.

```text
HISTORICAL_EVIDENCE_LOST = FALSE
SPLIT_BRANCH_DELETION_AUTHORIZED = FALSE
```

## Gate state

```text
NO_LOST_PROVEN_CAPABILITY          = PRECHECK_PASS
NO_UNJUSTIFIED_DUPLICATE_BOUNDARY  = PENDING_PRODUCT_SURFACE_RECONCILIATION
NEW_USEFUL_WORK_PRESERVED          = PRECHECK_PASS
OLD_CRITICAL_TESTS_REQUALIFIED     = PENDING_EXECUTION_ENVIRONMENT
CURRENT_TESTS_PASS                 = PENDING_EXECUTION_ENVIRONMENT
REAL_EXECUTION_PATH_VERIFIED       = PENDING_EXECUTION_ENVIRONMENT
MAIN_HISTORY_PRESERVED             = PASS

R5 = IN_PROGRESS
```

Do not merge to `main` or mark reconciliation complete until the pending
product-surface reconciliation is resolved and the execution gate is captured
and verified.
