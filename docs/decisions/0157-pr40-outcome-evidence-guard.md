# Decision 0157: positive outcome evidence guard

## Status

Validated as an isolated follow-up to PR40. Promotion is not authorized.

## Problem

The outcome contracts allowed `PASS` and `ACCEPTED` objects without evidence,
and allowed an empty authority. That made a positive serialized state possible
without an attributable authority or evidence reference.

## Decision

Verification and acceptance outcomes require a non-empty authority. The
positive states `PASS` and `ACCEPTED` additionally require non-empty evidence
references. Other states retain their explicit non-positive semantics.

This block changes only the pure outcome contract. It does not execute a
verifier, provider, runtime, harness, executor, or agent loop.

## Evidence

The focused outcome suite includes negative tests for missing evidence and
authority. Promotion remains unauthorized and Qualification Run v1 remains
blocked.
