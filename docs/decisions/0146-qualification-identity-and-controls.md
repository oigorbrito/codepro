# Decision 0146 — Qualification identity and verifier controls

Date: 2026-09-24  
Status: accepted as documentation policy  
Classification: `PROTOCOL_STRENGTHENING`

## Decision

Codepro adopts four explicit identity levels for empirical work:

```text
experiment_id  = protocol and scope
trial_id       = frozen comparison cell
attempt_id     = one execution attempt
verifier_run_id = one verifier cache namespace for one control/patch attempt
```

Stable identity applies to equivalent frozen protocol inputs. A verifier run
ID must still be unique across distinct controls, patches and retries because
benchmark harnesses may cache by run identity rather than by diff content.

Every qualification manifest must index dataset/task, environment, executor,
provider/model, configuration, verifier, budget, treatment, control role,
provider-called status, raw artifacts, and independent acceptance. Missing
identity or raw evidence remains an explicit non-success state.

Provider-free verifier qualification requires a paired control:

```text
no-op/empty patch  -> expected failure
gold/oracle patch  -> expected resolution
```

The controls qualify only the declared verifier and environment authority.
They do not qualify an agent, provider, model, treatment, or product release.

## Rationale and acceptance criteria

The current repository already separates execution, verification, acceptance
and promotion, but identity requirements were distributed across manifests,
ADRs and logs. The update makes the comparison unit and verifier cache boundary
explicit without adding a runtime service or changing executor behavior.

This documentation decision is accepted when:

- `AGENTS.md`, the experimental protocol and architecture page state the same
  identity levels and control rule;
- future qualification records can locate raw evidence from one manifest;
- no-op and gold controls are represented as required states, not inferred
  from a candidate result;
- local tests and benchmark results remain clearly separated from external
  authority and promotion.

No provider, executor, model, or treatment is promoted by this decision.
