# 0169 — Chassis shootout runner contract

## Status

CANDIDATE — requires hosted GitHub Actions execution before acceptance.

## Decision basis

problem_class = comparative coding-agent runner reproducibility  
decision = add one dependency-free, fail-closed runner contract for #99  
basis_type = PROJECT_INVARIANT + LOCAL_EVIDENCE  
basis_ref = issues #84, #98, #99; existing provider-free GitHub Actions workflows  
supported_claim = CodePro already separates command observation from verification and preserves raw hosted-CI evidence  
applicability = Nano and Agentless require identical evidence semantics before any quality comparison  
deviation = none; this does not execute either real upstream candidate yet

## Contract

The runner:

- executes argv without shell interpretation;
- records candidate process outcome as observation only;
- runs an independent verifier;
- derives PASS/FAIL only from the verifier;
- separates timeout/launch errors as infrastructure failure;
- records runner identity and project/candidate revisions;
- always writes structured evidence before returning its final status.

The hosted workflow proves the plumbing with deterministic fixtures labelled nano and agentless; those fixture labels are not claims that either upstream candidate executed.

A deliberate broken control must:

1. return a failing workflow step;
2. classify as VERIFIED_FAIL;
3. retain its JSON evidence artifact.

## Boundaries

CI_CONTRACT_VALIDATION != REAL_MODEL_BENCHMARK  
FIXTURE_ADAPTER_PASS != UPSTREAM_CANDIDATE_PASS  
COMMAND_EXIT != TASK_SUCCESS  
IMPLEMENTED != EXECUTED

Real Nano and Agentless baselines belong to #101 and #102 after #100 freezes the workload/verifier/budgets.
