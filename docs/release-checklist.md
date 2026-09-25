# CodePro release-candidate checklist

This checklist covers release engineering and evidence. It does not promote an
executor, benchmark result, P8.2 treatment, or product claim by itself.

## Decision basis

The release path follows the Python Packaging User Guide packaging flow:
versioned source -> build sdist/wheel -> validate/install artifacts -> publish
only after acceptance.

Primary references:

- https://packaging.python.org/en/latest/flow/
- https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/
- https://packaging.python.org/en/latest/guides/tool-recommendations/
- https://docs.github.com/en/actions/concepts/security/artifact-attestations

## A. Freeze the candidate

- [ ] Identify one exact 40-character commit SHA.
- [ ] Record the intended CodePro version and release scope.
- [ ] Confirm the candidate contains no unintended generated/local artifacts.
- [ ] Do not substitute a newer branch tip after evidence starts.

## B. Build and verify the exact SHA

Run the `Release candidate evidence` workflow manually with the exact SHA.

The workflow must:

- [ ] check out and verify that exact SHA;
- [ ] build both sdist and wheel with `python -m build`;
- [ ] validate both with `twine check`;
- [ ] audit the declared project dependency graph with `pip-audit`;
- [ ] install the wheel in an isolated venv with no `PYTHONPATH`;
- [ ] run `pip check`;
- [ ] smoke `codepro --version`, `--help`, `doctor --json`, and
      `inspect --json`;
- [ ] run the repository foundation, complete unit suite, mutation probe, and
      chassis fingerprint on the same SHA;
- [ ] calculate SHA-256 for every distribution artifact;
- [ ] retain raw build/environment/output evidence.

## C. Supported Python installation

The candidate wheel must install and start under every supported interpreter
declared by the project:

- [ ] Python 3.12
- [ ] Python 3.13
- [ ] Python 3.14

Compatibility success is package/runtime evidence only. It is not executor or
benchmark qualification.

## D. Supply-chain evidence

- [ ] Retain the workflow URL, exact source SHA, distribution hashes, and raw
      artifact bundle.
- [ ] Prefer short-lived OIDC/Trusted Publishing for an eventual package-index
      publication; do not introduce a long-lived publish token.
- [ ] If GitHub artifact attestations are available for the repository plan,
      attest release artifacts and verify the attestation before publication.
      GitHub documents that private/internal repositories require Enterprise
      Cloud for artifact attestations on current plans.
- [ ] If attestations are unavailable, record that limitation; hashes and
      workflow evidence remain evidence but are not equivalent to an
      attestation.
- [ ] Produce/attach an SBOM before any release policy that requires one.
      SBOM generation is not silently treated as complete by this workflow.

## E. Operational-product evidence

For a technical/chassis release, explicitly state that the artifact does not
prove operational task execution.

For an operational-product release, additionally require the separately
authorized public vertical and its evidence:

- [ ] task submission;
- [ ] explicitly bound executor/reference profile;
- [ ] execution under declared scope/budget/environment;
- [ ] raw trajectory/patch;
- [ ] verification;
- [ ] replay/audit;
- [ ] independent acceptance.

## F. Acceptance and publication

- [ ] Review the complete evidence bundle.
- [ ] Record independent acceptance or an explicit blocked/rejected state.
- [ ] Only after acceptance, create the immutable tag/release.
- [ ] Publication is a separate explicit action; this workflow never uploads to
      PyPI or promotes an executor automatically.

## Billing / runner failure

If GitHub Actions cannot allocate a runner because of billing/spending limits:

```text
CI = BLOCKED_NOT_EXECUTED
```

Do not call it PASS or code failure. The same commands may be executed
mechanically in a clean environment to collect local evidence, but local
evidence remains distinct from GitHub CI evidence.
