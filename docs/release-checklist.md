# CodePro release checklist

Use this checklist for every public release. A checked item is evidence of the
release process only; it does not promote a provider, model, executor, or
benchmark claim by itself.

## 1. Source and contract gates

- [ ] `main` is the default branch and has no unmerged release PRs.
- [ ] All release issues are closed or explicitly recorded as blocked.
- [ ] Version in `src/arkx/__init__.py` matches the release tag.
- [ ] Decision records, README, CLI help, and compatibility requirements are current.
- [ ] Foundation CI passes on the release commit.
- [ ] Mutation probe passes with zero surviving mutations.

## 2. Package and CLI gates

- [ ] Build sdist and wheel with `python -m build`.
- [ ] Validate metadata with `twine check dist/*`.
- [ ] Install the wheel in clean Python environments for every supported version.
- [ ] Run `codepro --version`, `codepro doctor`, and `codepro inspect`.
- [ ] Record SHA-256 hashes for every published artifact.
- [ ] Run `pip-audit` against the release environment and retain the raw report.

## 3. External security and supply-chain gates

- [ ] Run OpenSSF Scorecard against the repository and retain the JSON result.
- [ ] Run CodeQL or an equivalent independent static-analysis service.
- [ ] Publish an SBOM (CycloneDX or SPDX) with the release artifacts.
- [ ] Publish through a short-lived trusted publisher (OIDC) where the package
      index supports it; do not commit long-lived publish tokens.

## 4. Benchmark gates

- [ ] Freeze dataset, split, task IDs, base commits, model/provider identity,
      configuration, budget, runtime, and treatment identity.
- [ ] Run the official evaluator in a reproducible container or declared cloud
      executor. Keep `run.json`, summary, per-instance reports, test output,
      patches, and environment facts.
- [ ] Publish the report and raw run archive online, linked from the release.
- [ ] Report resolved, unresolved, infrastructure, ambiguous, and indeterminate
      outcomes separately. Never infer success from missing evidence.
- [ ] Keep benchmark evidence separate from local unit-test evidence.

## 5. Human acceptance and publication

- [ ] An independent authority accepts the evidence and records the acceptance
      run ID, authority identity, artifacts, and evidence references.
- [ ] Promotion is explicitly decided after acceptance; no score or executor
      output grants tenure implicitly.
- [ ] Create the immutable tag and GitHub release only after all required gates.
- [ ] Attach package artifacts, hashes, SBOM, security reports, and benchmark
      report/raw archive to the GitHub release.
- [ ] Re-open or mark the release blocked if a later verification invalidates
      any required evidence.

## Current v0.2.0 record

- Release commit: `bb1b4547da8596322f35f2e955d91b49f58786aa`.
- Foundation CI and Python compatibility checks passed.
- Focused acceptance/promotion tests passed.
- Existing external Gold evidence: run
  `arkx-p82-gold-docker-lf-20260923-02`, dataset
  `SWE-bench/SWE-bench_Verified`, one frozen task, `resolved: 1/1`.
- This one-task Gold result is recorded as authority evidence for that frozen
  task only; it is not a general model, provider, or mechanism qualification.
