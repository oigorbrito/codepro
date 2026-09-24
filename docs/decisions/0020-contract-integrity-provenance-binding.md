# ADR 0020 — Contract integrity and provenance binding

## Status

Accepted for the Arkx empirical chassis.

## Observed need

Adversarial contract probes found that several locally deterministic components could still accept semantically invalid boundary data:

1. blank evidence references could satisfy presence checks;
2. P0 telemetry did not enforce temporal event ordering;
3. negative budgets and non-finite numeric observations could enter decisions;
4. permissive deserialization could coerce malformed values such as a string `"false"` into boolean `True`;
5. P5 could verify with no required regression result;
6. promotion assessments were not bound to the exact frozen gate;
7. Analysis, Measurement, and Validity freezes validated against a Study Spec without preserving the governing Study Spec hash;
8. Run Manifest references to workload, configuration, and environment were nominal rather than content-bound.

These are integrity failures at contract boundaries. They do not justify additional orchestration layers.

## Decision

Prefer fail-closed, content-bound contracts over backward compatibility.

- Evidence references must be substantive non-blank strings.
- P0 event streams reject temporal regression, duplicate task boundaries, and events after task finish.
- Quantitative measurements and budgets reject negative, boolean-as-integer, and non-finite values where those values are not meaningful.
- Boundary parsers validate types instead of silently coercing them.
- Patch verification requires at least one required regression result and evidence for a passing required result.
- Promotion assessment and decision are bound to a `FrozenPromotionGate` content hash.
- Frozen Analysis Plan, Measurement Contract, and Validity Plan preserve and include the governing `study_spec_hash` in artifact identity.
- Run Manifest schema v2 binds Study Spec, workload, treatment/configuration, environment, code, and raw execution record with immutable/content-addressed identities.

## Evidence

The changes are covered by adversarial unit tests and the repository CI workflow. A green CI run is implementation evidence only; it is not evidence that a policy improves benchmark outcomes.

## Alternatives considered

- Keep permissive parsing and validate only at freeze time: rejected because malformed imported artifacts can circulate before freeze.
- Preserve schema v1 aliases: rejected where aliases would retain ambiguous or weaker integrity semantics.
- Add a new orchestration or validation service: rejected because the observed failures can be closed inside existing contracts.
- Treat nominal references as sufficient provenance: rejected because mutable targets can retain the same human-readable identifier.

## Limitation

Content hashes establish identity, not truthfulness or temporal precedence by themselves. Commit-anchored references and retained raw evidence remain necessary. Real-world effectiveness of routing, planning, or executor composition still requires separately frozen empirical studies.

## Rollback/removal condition

These checks may be replaced only by a simpler mechanism that preserves the same fail-closed semantics, content bindings, and state separation without increasing coupling.
