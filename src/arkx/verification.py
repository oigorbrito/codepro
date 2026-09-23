"""Deterministic patch verification, separate from final acceptance (P5)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Any


SCHEMA_VERSION = 1


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
    REPRODUCTION_REQUIRED_MISSING = "REPRODUCTION_REQUIRED_MISSING"
    ISSUE_NOT_REPRODUCED = "ISSUE_NOT_REPRODUCED"
    PATCH_NOT_APPLIED = "PATCH_NOT_APPLIED"
    REQUIRED_REGRESSION_FAILED = "REQUIRED_REGRESSION_FAILED"
    REQUIRED_TEST_NOT_EXECUTED = "REQUIRED_TEST_NOT_EXECUTED"
    POST_PATCH_REPRODUCTION_FAILED = "POST_PATCH_REPRODUCTION_FAILED"
    SCOPE_CHANGED = "SCOPE_CHANGED"
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    ALL_GATES_SATISFIED = "ALL_GATES_SATISFIED"


def _values(items: tuple[str, ...] | None) -> list[str] | None:
    return None if items is None else sorted(set(items))


@dataclass(frozen=True)
class TestResult:
    test_id: str
    status: TestResultStatus
    required: bool
    evidence_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"test_id": self.test_id, "status": self.status.value, "required": self.required, "evidence_ref": self.evidence_ref}


@dataclass(frozen=True)
class PatchVerificationInput:
    task_id: str
    issue_reproduction_required: bool
    reproduction_before: bool | None
    patch_applied: bool | None
    regression_results: tuple[TestResult, ...] | None
    reproduction_after: bool | None
    changed_files: tuple[str, ...] | None
    expected_scope: tuple[str, ...] | None
    evidence_refs: tuple[str, ...] | None
    schema_version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class PatchVerificationResult:
    task_id: str
    reproduces_issue: bool | None
    patch_applied: bool | None
    regression_tests_passed: bool | None
    reproduction_passed_after_patch: bool | None
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
            "reproduces_issue": self.reproduces_issue,
            "patch_applied": self.patch_applied,
            "regression_tests_passed": self.regression_tests_passed,
            "reproduction_passed_after_patch": self.reproduction_passed_after_patch,
            "scope_changed": self.scope_changed,
            "evidence_sufficient": self.evidence_sufficient,
            "status": self.status.value,
            "reason_codes": [code.value for code in self.reason_codes],
            "telemetry": self.telemetry,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def verify_patch(value: PatchVerificationInput) -> PatchVerificationResult:
    reasons: list[ReasonCode] = []
    if value.issue_reproduction_required and value.reproduction_before is None:
        return _result(value, PatchVerificationStatus.BLOCKED, None, None, None, None, None, [ReasonCode.REPRODUCTION_REQUIRED_MISSING])
    if value.issue_reproduction_required and value.reproduction_before is False:
        return _result(value, PatchVerificationStatus.REJECTED, False, value.patch_applied, None, None, None, [ReasonCode.ISSUE_NOT_REPRODUCED])
    if value.patch_applied is None or value.regression_results is None or value.reproduction_after is None or value.changed_files is None or value.expected_scope is None:
        return _result(value, PatchVerificationStatus.UNKNOWN, value.reproduction_before, value.patch_applied, None, value.reproduction_after, None, [ReasonCode.EVIDENCE_MISSING])
    if value.patch_applied is False:
        return _result(value, PatchVerificationStatus.REJECTED, value.reproduction_before, False, None, value.reproduction_after, False, [ReasonCode.PATCH_NOT_APPLIED])

    required = [test for test in value.regression_results if test.required]
    if any(test.status is TestResultStatus.FAILED for test in required):
        reasons.append(ReasonCode.REQUIRED_REGRESSION_FAILED)
        return _result(value, PatchVerificationStatus.REJECTED, value.reproduction_before, True, False, value.reproduction_after, None, reasons)
    if any(test.status in (TestResultStatus.NOT_EXECUTED, TestResultStatus.UNKNOWN) for test in required):
        return _result(value, PatchVerificationStatus.BLOCKED, value.reproduction_before, True, None, value.reproduction_after, None, [ReasonCode.REQUIRED_TEST_NOT_EXECUTED])
    if value.reproduction_after is True:
        return _result(value, PatchVerificationStatus.REJECTED, value.reproduction_before, True, True, True, None, [ReasonCode.POST_PATCH_REPRODUCTION_FAILED])

    scope_changed = bool(set(value.changed_files) - set(value.expected_scope))
    if scope_changed:
        return _result(value, PatchVerificationStatus.REJECTED, value.reproduction_before, True, True, False, True, [ReasonCode.SCOPE_CHANGED])
    evidence_sufficient = bool(value.evidence_refs)
    if not evidence_sufficient:
        return _result(value, PatchVerificationStatus.BLOCKED, value.reproduction_before, True, True, False, False, [ReasonCode.EVIDENCE_MISSING])
    reasons.append(ReasonCode.ALL_GATES_SATISFIED)
    return _result(value, PatchVerificationStatus.VERIFIED, value.reproduction_before, True, True, False, False, reasons)


def _result(value, status, reproduces, applied, regressions, after, scope_changed, reasons):
    return PatchVerificationResult(
        task_id=value.task_id,
        reproduces_issue=reproduces,
        patch_applied=applied,
        regression_tests_passed=regressions,
        reproduction_passed_after_patch=after,
        scope_changed=scope_changed,
        evidence_sufficient=(bool(value.evidence_refs) if value.evidence_refs is not None else None),
        status=status,
        reason_codes=tuple(reasons),
        telemetry={
            "patch_verification_status": status.value,
            "required_tests": None if value.regression_results is None else sum(test.required for test in value.regression_results),
            "passed_tests": None if value.regression_results is None else sum(test.status is TestResultStatus.PASSED for test in value.regression_results),
            "failed_tests": None if value.regression_results is None else sum(test.status is TestResultStatus.FAILED for test in value.regression_results),
            "scope_changed": scope_changed,
            "reproduction_required": value.issue_reproduction_required,
            "reproduction_passed": after,
        },
    )

