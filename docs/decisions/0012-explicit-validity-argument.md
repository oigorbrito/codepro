# ADR 0012 — Require claim-linked validity arguments

## Status

Accepted for the Arkx empirical chassis.

## Observed need

The chassis now freezes study design, workload, run provenance, and analysis rules. It still needs an explicit mechanism preventing claims from silently exceeding what the workload and measurements support.

Generic "threats to validity" lists are insufficient because they can be detached from the actual inference.

## Decision

Add Validity Plan v1. Every declared study metric receives a construct mapping with rationale and limitation. Workload references and target population are explicit. Threats link a claim at risk to a mechanism, mitigation, residual risk, and evidence.

For benchmark-oriented studies, construct, external, conclusion, and reliability/reproducibility dimensions are mandatory. Internal validity is added where applicable rather than asserted universally.

Engineering-research studies also record artifact strengths, weaknesses, limitations, and state-of-art alternatives or an explicit justification for their absence.

## Limitation

This contract forces explicit reasoning; it cannot prove that a representativeness or construct-validity argument is correct. Those claims still require substantive evidence and review.

## Rollback/removal condition

Replace this contract if a future methodology-specific validity framework provides equivalent or stronger claim-linked reasoning without generic checklist behavior.
