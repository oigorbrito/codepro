# ADR 0096: Resume only from persisted causal boundaries

## Status

Accepted for local architectural evidence.

## Decision

`decide_resume()` is a pure replay decision. A terminal event means no resume
is allowed. An execution reference without verification resumes verification;
verification without acceptance resumes acceptance; acceptance without
promotion resumes promotion. A plan without execution requires explicit
restart, because missing execution evidence cannot prove that the executor did
not run. A recovery reference without a new execution requires explicit replan.

## Falsifiable hypothesis and acceptance criteria

H1: crash recovery never reexecutes a stage whose evidence is missing by
assumption. Tests must cover restart-required, verification-resume,
acceptance-resume, and terminal decisions.

## Consequences

The protocol is safe but conservative. A future resume service may execute the
returned action only after checking the same identities, budgets and policies;
this decision does not authorize an executor switch or fallback.
