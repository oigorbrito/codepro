"""Deterministic patch verification, separate from final acceptance (P5)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Any


SCHEMA_VERSION = 2


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class TestResultStatus(_ValueEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_EXECUTED = "NOT_EXECUTED"
    UNKNOWN = "UNKNOWN"


class PatchVerificationStatus(_ValueEnum):
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class ReasonCode(_ValueEnum):
    REPRODUCTION_REQUIRED_MISSING_BEFORE_PATCH = "REPRODUCTION_REQUIRED_MISSING_BEFORE_PATCH"
    ISSUE_NOT_REPRODUCED_BEFORE_PATCH = "ISSUE_NOT_REPRODUCED_BEFORE_PATCH"
    REPRODUCTION_REQUIRED_MISSING_AFTER_PATCH = "REPRODUCTION_REQUIRED_MISSING_AFTER_PATCH"
    ISSUE_STILL_REPRODUCES_AFTER_PATCH = "ISSUE_STILL_REPRODUCES_AFTER_PATCH"
    PATCH_NOT_APPLIED = "PATCH_NOT_APPLIED"
    REQUIRED_REGRESSION_FAILED = "REQUIRED_REGRESSION_FAILED"
    REQUIRED_TEST_NOT_EXECUTED = "REQUIRED_TEST_NOT_EXECUTED"
    SCOPE_CHANGED = "SCOPE_CHANGED"
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    ALL_GATES_SATISFIED = "ALL_GATES_SATISFIED"


@dataclass(frozen=True)
class TestResult:
    test_id: str
    status: TestResultStatus
    required: bool
    evidence_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_id": self.test_id,
            "status": self.status.value,
            "required": self.required,
            "evidence_ref": self.evidence_ref,
        }


@dataclass(frozen=True)
class PatchVerificationInput:
    task_id: str
    issue_reproduction_required: bool
    issue_reproduced_before_patch: bool | None
    patch_applied: bool | None
    regression_results: tuple[TestResult, ...] | None
    issue_reproduces_after_patch: bool | None
    changed_files: tuple[str, ...] | None
    expected_scope: tuple[str, ...] | None
    evidence_refs: tuple[str, ...] | None
    schema_version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class PatchVerificationResult:
    task_id: str
    issue_reproduced_before_patch: bool | None
    patch_applied: bool | None
    regression_tests_passed: bool | None
    issue_reproduces_after_patch: bool | None
    scope_changed: bool | None
    evidence_sufficient: bool | None
    status: PatchVerificationStatus
    reason_codes: tuple[ReasonCode, ...]
    telemetry: dict[str, Any] = field(default_factory=dict)
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "issue_reproduced_before_patch": self.issue_reproduced_before_patch,
            "patch_applied": self.patch_applied,
            "regression_tests_passed": self.regression_tests_passed,
            "issue_reproduces_after_patch": self.issue_reproduces_after_patch,
            "scope_changed": self.scope_changed,
            "evidence_sufficient": self.evidence_sufficient,
            "status": self.status.value,
            "reason_codes": [code.value for code in self.reason_codes],
            "telemetry": self.telemetry,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def verify_patch(value: PatchVerificationInput) -> PatchVerificationResult:
    if value.issue_reproduction_required:
        if value.issue_reproduced_before_patch is None:
            return _result(
                value,
                PatchVerificationStatus.BLOCKED,
                regressions=None,
                scope_changed=None,
                reasons=[ReasonCode.REPRODUCTION_REQUIRED_MISSING_BEFORE_PATCH],
            )
        if value.issue_reproduced_before_patch is False:
            return _result(
                value,
                PatchVerificationStatus.REJECTED,
                regressions=None,
                scope_changed=None,
                reasons=[ReasonCode.ISSUE_NOT_REPRODUCED_BEFORE_PATCH],
            )
        if value.issue_reproduces_after_patch is None:
            return _result(
                value,
                PatchVerificationStatus.BLOCKED,
                regressions=None,
                scope_changed=None,
                reasons=[ReasonCode.REPRODUCTION_REQUIRED_MISSING_AFTER_PATCH],
            )

    required_observation_missing = any(
        item is None
        for item in (
            value.patch_applied,
            value.regression_results,
            value.changed_files,
            value.expected_scope,
        )
    )
    if required_observation_missing:
        return _result(
            value,
            PatchVerificationStatus.UNKNOWN,
            regressions=None,
            scope_changed=None,
            reasons=[ReasonCode.EVIDENCE_MISSING],
        )

    if value.patch_applied is False:
        return _result(
            value,
            PatchVerificationStatus.REJECTED,
            regressions=None,
            scope_changed=False,
            reasons=[ReasonCode.PATCH_NOT_APPLIED],
        )

    assert value.regression_results is not None
    required = [test for test in value.regression_results if test.required]
    if any(test.status is TestResultStatus.FAILED for test in required):
        return _result(
            value,
            PatchVerificationStatus.REJECTED,
            regressions=False,
            scope_changed=None,
            reasons=[ReasonCode.REQUIRED_REGRESSION_FAILED],
        )
    if any(test.status in (TestResultStatus.NOT_EXECUTED, TestResultStatus.UNKNOWN) for test in required):
        return _result(
            value,
            PatchVerificationStatus.BLOCKED,
            regressions=None,
            scope_changed=None,
            reasons=[ReasonCode.REQUIRED_TEST_NOT_EXECUTED],
        )

    if value.issue_reproduction_required and value.issue_reproduces_after_patch is True:
        return _result(
            value,
            PatchVerificationStatus.REJECTED,
            regressions=True,
            scope_changed=None,
            reasons=[ReasonCode.ISSUE_STILL_REPRODUCES_AFTER_PATCH],
        )

    assert value.changed_files is not None
    assert value.expected_scope is not None
    scope_changed = bool(set(value.changed_files) - set(value.expected_scope))
    if scope_changed:
        return _result(
            value,
            PatchVerificationStatus.REJECTED,
            regressions=True,
            scope_changed=True,
            reasons=[ReasonCode.SCOPE_CHANGED],
        )

    if not value.evidence_refs:
        return _result(
            value,
            PatchVerificationStatus.BLOCKED,
            regressions=True,
            scope_changed=False,
            reasons=[ReasonCode.EVIDENCE_MISSING],
        )

    return _result(
        value,
        PatchVerificationStatus.VERIFIED,
        regressions=True,
        scope_changed=False,
        reasons=[ReasonCode.ALL_GATES_SATISFIED],
    )


def _result(
    value: PatchVerificationInput,
    status: PatchVerificationStatus,
    *,
    regressions: bool | None,
    scope_changed: bool | None,
    reasons: list[ReasonCode],
) -> PatchVerificationResult:
    return PatchVerificationResult(
        task_id=value.task_id,
        issue_reproduced_before_patch=value.issue_reproduced_before_patch,
        patch_applied=value.patch_applied,
        regression_tests_passed=regressions,
        issue_reproduces_after_patch=value.issue_reproduces_after_patch,
        scope_changed=scope_changed,
        evidence_sufficient=(bool(value.evidence_refs) if value.evidence_refs is not None else None),
        status=status,
        reason_codes=tuple(reasons),
        telemetry={
            "patch_verification_status": status.value,
            "required_tests": None
            if value.regression_results is None
            else sum(test.required for test in value.regression_results),
            "passed_tests": None
            if value.regression_results is None
            else sum(test.status is TestResultStatus.PASSED for test in value.regression_results),
            "failed_tests": None
            if value.regression_results is None
            else sum(test.status is TestResultStatus.FAILED for test in value.regression_results),
            "scope_changed": scope_changed,
            "issue_reproduction_required": value.issue_reproduction_required,
            "issue_reproduced_before_patch": value.issue_reproduced_before_patch,
            "issue_reproduces_after_patch": value.issue_reproduces_after_patch,
        },
    )
