import unittest

from arkx.characterization import TaskSignals
from arkx.command import (
    CommandEnvironmentError,
    CommandResult,
    EnvironmentErrorKind,
)
from arkx.governance import AuthorityGrant, TaskRequest
from arkx.progress import ProgressSnapshot
from arkx.qualification import (
    ExecutorQualification,
    ExecutorRuntime,
    QualificationStatus,
)
from arkx.spine import (
    InvocationState,
    SpineReason,
    SpineStatus,
    execute_governed,
    verify_observation,
)
from arkx.verification import (
    PatchVerificationInput,
    TestResult,
    TestResultStatus,
)


def request():
    return TaskRequest(
        request_id="request-1",
        requester_ref="user://fixture",
        task_ref="task-1",
        project_ref="git://repo@base",
        requested_scope=("src/a.py",),
        required_permissions=("edit", "test"),
    )


def grant(**overrides):
    values = {
        "grant_id": "grant-1",
        "request_id": "request-1",
        "authority_ref": "authority://fixture",
        "authorized_scope": ("src/a.py", "tests/test_a.py"),
        "permissions": ("edit", "test"),
        "max_commands": 10,
        "max_wall_time_seconds": 60,
        "environment_ref": "environment://fixture",
        "acceptance_authority_ref": "acceptance://reviewer",
        "evidence_refs": ("evidence://authority",),
    }
    values.update(overrides)
    return AuthorityGrant(**values)


def signals(**overrides):
    values = {
        "candidate_files": ("src/a.py",),
        "dependency_edges": (),
        "affected_components": ("a",),
        "known_tests": ("test_a",),
        "ambiguity_markers": (),
        "risk_markers": (),
        "acceptance_checks": ("tests pass",),
        "state_shared": False,
        "architectural_change": False,
    }
    values.update(overrides)
    return TaskSignals(**values)


def runtime(*, available=True):
    return ExecutorRuntime(
        "fixture",
        "1.0",
        "fixture-adapter",
        "1.0",
        available,
        "evidence://availability",
    )


def qualification():
    return ExecutorQualification(
        "fixture",
        "1.0",
        "fixture-adapter",
        "1.0",
        "repository-edit",
        QualificationStatus.QUALIFIED,
        ("evidence://qualification",),
    )


def command_result(*, exit_code=0, timed_out=False, error=None):
    return CommandResult(
        argv=("fixture",),
        cwd="/tmp/fixture",
        exit_code=exit_code,
        stdout="observation\n",
        stderr="",
        timed_out=timed_out,
        duration_ms=10,
        environment_error=error,
    )


class FixtureExecutor:
    def __init__(self, result=None, *, identity=None):
        self._result = result or command_result()
        self._identity = identity or (
            "fixture",
            "1.0",
            "fixture-adapter",
            "1.0",
        )
        self.calls = []

    @property
    def identity(self):
        return self._identity

    def invoke(self, **kwargs):
        self.calls.append(kwargs)
        return self._result


def execute_fixture(*, executor=None, grant_value=None, signals_value=None, runtimes=None, qualifications=None):
    executor = executor or FixtureExecutor()
    record = execute_governed(
        request(),
        grant() if grant_value is None else grant_value,
        signals() if signals_value is None else signals_value,
        capability_id="repository-edit",
        runtimes=(runtime(),) if runtimes is None else runtimes,
        qualifications=(qualification(),) if qualifications is None else qualifications,
        executor=executor,
    )
    return record, executor


def previous_progress():
    return ProgressSnapshot(
        useful_files=("src/a.py",),
        passing_tests=(),
        explained_failures=(),
        diff_distance=2,
        acceptance_distance=1,
        recent_actions=("inspect",),
        failure_signatures=("failure-a",),
    )


def current_progress():
    return ProgressSnapshot(
        useful_files=("src/a.py",),
        passing_tests=("test_a",),
        explained_failures=(),
        diff_distance=1,
        acceptance_distance=0,
        recent_actions=("patch", "test"),
        failure_signatures=(),
    )


def verification(**overrides):
    values = {
        "task_id": "task-1",
        "issue_reproduction_required": True,
        "issue_reproduced_before_patch": True,
        "patch_applied": True,
        "regression_results": (
            TestResult(
                "test_a",
                TestResultStatus.PASSED,
                True,
                "evidence://test-a",
            ),
        ),
        "issue_reproduces_after_patch": False,
        "changed_files": ("src/a.py",),
        "expected_scope": ("src/a.py",),
        "evidence_refs": ("evidence://verification",),
    }
    values.update(overrides)
    return PatchVerificationInput(**values)


class GateOrderingTests(unittest.TestCase):
    def test_nominal_execution_transports_authority_and_binding(self):
        record, executor = execute_fixture()

        self.assertEqual(record.status, SpineStatus.EXECUTED)
        self.assertEqual(record.reason, SpineReason.EXECUTION_OBSERVED)
        self.assertEqual(record.invocation_state, InvocationState.OBSERVED)
        self.assertEqual(record.acceptance_authority_ref, "acceptance://reviewer")
        self.assertEqual(record.binding.executor_id, "fixture")
        self.assertEqual(len(executor.calls), 1)
        self.assertEqual(executor.calls[0]["timeout_seconds"], 60.0)
        self.assertEqual(
            record.capability_requirement.source_ref,
            record.routing_ref,
        )

    def test_missing_governance_blocks_before_characterization_or_executor(self):
        executor = FixtureExecutor()
        record = execute_governed(
            request(),
            None,
            signals(),
            capability_id="repository-edit",
            runtimes=(runtime(),),
            qualifications=(qualification(),),
            executor=executor,
        )

        self.assertEqual(record.status, SpineStatus.BLOCKED)
        self.assertEqual(record.reason, SpineReason.GOVERNANCE_BLOCKED)
        self.assertEqual(record.invocation_state, InvocationState.NOT_EXECUTED)
        self.assertIsNone(record.characterization)
        self.assertIsNone(record.routing)
        self.assertIsNone(record.binding)
        self.assertEqual(executor.calls, [])

    def test_unknown_governance_does_not_call_executor(self):
        executor = FixtureExecutor()
        record = execute_governed(
            request(),
            grant(environment_ref=None),
            signals(),
            capability_id="repository-edit",
            runtimes=(runtime(),),
            qualifications=(qualification(),),
            executor=executor,
        )
        self.assertEqual(record.status, SpineStatus.UNKNOWN)
        self.assertEqual(record.reason, SpineReason.GOVERNANCE_UNKNOWN)
        self.assertEqual(executor.calls, [])

    def test_characterization_scope_cannot_expand_original_request(self):
        executor = FixtureExecutor()
        record, _ = execute_fixture(
            executor=executor,
            signals_value=signals(candidate_files=("src/b.py",)),
        )
        self.assertEqual(record.status, SpineStatus.BLOCKED)
        self.assertEqual(
            record.reason,
            SpineReason.CHARACTERIZATION_SCOPE_OUTSIDE_REQUEST,
        )
        self.assertEqual(executor.calls, [])

    def test_uncertain_characterization_requires_qualification_before_binding(self):
        executor = FixtureExecutor()
        record, _ = execute_fixture(
            executor=executor,
            signals_value=signals(candidate_files=None),
        )
        self.assertEqual(record.status, SpineStatus.REQUIRE_QUALIFICATION)
        self.assertEqual(record.reason, SpineReason.ROUTING_REQUIRES_QUALIFICATION)
        self.assertIsNone(record.binding)
        self.assertEqual(executor.calls, [])

    def test_missing_executor_qualification_does_not_call_executor(self):
        executor = FixtureExecutor()
        record, _ = execute_fixture(
            executor=executor,
            qualifications=(),
        )
        self.assertEqual(record.status, SpineStatus.REQUIRE_QUALIFICATION)
        self.assertEqual(record.reason, SpineReason.BINDING_REQUIRES_QUALIFICATION)
        self.assertEqual(executor.calls, [])

    def test_unavailable_bound_candidate_blocks_without_invocation(self):
        executor = FixtureExecutor()
        record, _ = execute_fixture(
            executor=executor,
            runtimes=(runtime(available=False),),
        )
        self.assertEqual(record.status, SpineStatus.BLOCKED)
        self.assertEqual(record.reason, SpineReason.BINDING_BLOCKED)
        self.assertEqual(executor.calls, [])

    def test_executor_identity_mismatch_blocks_without_invocation(self):
        executor = FixtureExecutor(
            identity=("other", "1.0", "fixture-adapter", "1.0")
        )
        record, _ = execute_fixture(executor=executor)
        self.assertEqual(record.status, SpineStatus.BLOCKED)
        self.assertEqual(record.reason, SpineReason.EXECUTOR_IDENTITY_MISMATCH)
        self.assertEqual(executor.calls, [])


class ExecutionObservationTests(unittest.TestCase):
    def test_nonzero_exit_remains_executed_observation(self):
        executor = FixtureExecutor(command_result(exit_code=7))
        record, _ = execute_fixture(executor=executor)

        self.assertEqual(record.status, SpineStatus.EXECUTED)
        self.assertEqual(record.command_result.exit_code, 7)
        self.assertEqual(record.reason, SpineReason.EXECUTION_OBSERVED)

    def test_launch_error_is_blocked_but_observation_is_preserved(self):
        error = CommandEnvironmentError(
            EnvironmentErrorKind.EXECUTABLE_NOT_FOUND,
            "missing fixture",
        )
        executor = FixtureExecutor(
            command_result(exit_code=None, error=error)
        )
        record, _ = execute_fixture(executor=executor)

        self.assertEqual(record.status, SpineStatus.BLOCKED)
        self.assertEqual(record.reason, SpineReason.ENVIRONMENT_ERROR)
        self.assertEqual(record.invocation_state, InvocationState.OBSERVED)
        self.assertEqual(
            record.command_result.environment_error.kind,
            EnvironmentErrorKind.EXECUTABLE_NOT_FOUND,
        )

    def test_timeout_is_blocked_as_timeout_not_task_failure(self):
        executor = FixtureExecutor(
            command_result(exit_code=-9, timed_out=True)
        )
        record, _ = execute_fixture(executor=executor)

        self.assertEqual(record.status, SpineStatus.BLOCKED)
        self.assertEqual(record.reason, SpineReason.COMMAND_TIMEOUT)
        self.assertTrue(record.command_result.timed_out)

    def test_timeout_with_cleanup_error_remains_timeout_primary(self):
        error = CommandEnvironmentError(
            EnvironmentErrorKind.TERMINATION_ERROR,
            "cleanup problem",
        )
        executor = FixtureExecutor(
            command_result(exit_code=-9, timed_out=True, error=error)
        )
        record, _ = execute_fixture(executor=executor)

        self.assertEqual(record.status, SpineStatus.BLOCKED)
        self.assertEqual(record.reason, SpineReason.COMMAND_TIMEOUT)
        self.assertIsNotNone(record.command_result.environment_error)


class VerificationPhaseTests(unittest.TestCase):
    def test_verified_execution_becomes_ready_for_acceptance_not_accepted(self):
        record, _ = execute_fixture()
        final = verify_observation(
            record,
            previous_progress(),
            current_progress(),
            verification(),
        )

        self.assertEqual(final.status, SpineStatus.READY_FOR_ACCEPTANCE)
        self.assertEqual(final.reason, SpineReason.VERIFICATION_VERIFIED)
        self.assertEqual(final.acceptance_authority_ref, "acceptance://reviewer")
        self.assertEqual(final.verification.status.value, "VERIFIED")
        payload = final.to_json()
        self.assertNotIn('"ACCEPTED"', payload)
        self.assertNotIn('"PROMOTED"', payload)

    def test_nonzero_exit_can_still_be_independently_verified(self):
        record, _ = execute_fixture(
            executor=FixtureExecutor(command_result(exit_code=7))
        )
        final = verify_observation(
            record,
            previous_progress(),
            current_progress(),
            verification(),
        )
        self.assertEqual(record.command_result.exit_code, 7)
        self.assertEqual(final.status, SpineStatus.READY_FOR_ACCEPTANCE)

    def test_rejected_verification_stays_rejected(self):
        record, _ = execute_fixture()
        final = verify_observation(
            record,
            previous_progress(),
            current_progress(),
            verification(issue_reproduces_after_patch=True),
        )
        self.assertEqual(final.status, SpineStatus.REJECTED)
        self.assertEqual(final.reason, SpineReason.VERIFICATION_REJECTED)

    def test_blocked_verification_stays_blocked(self):
        record, _ = execute_fixture()
        final = verify_observation(
            record,
            previous_progress(),
            current_progress(),
            verification(regression_results=()),
        )
        self.assertEqual(final.status, SpineStatus.BLOCKED)
        self.assertEqual(final.reason, SpineReason.VERIFICATION_BLOCKED)

    def test_unknown_verification_stays_unknown(self):
        record, _ = execute_fixture()
        final = verify_observation(
            record,
            previous_progress(),
            current_progress(),
            verification(changed_files=None),
        )
        self.assertEqual(final.status, SpineStatus.UNKNOWN)
        self.assertEqual(final.reason, SpineReason.VERIFICATION_UNKNOWN)

    def test_progress_is_recorded_but_does_not_self_accept(self):
        record, _ = execute_fixture()
        final = verify_observation(
            record,
            None,
            current_progress(),
            verification(),
        )
        self.assertEqual(final.progress.status.value, "UNKNOWN")
        self.assertEqual(final.status, SpineStatus.READY_FOR_ACCEPTANCE)

    def test_verification_before_execution_is_rejected(self):
        executor = FixtureExecutor()
        blocked = execute_governed(
            request(),
            None,
            signals(),
            capability_id="repository-edit",
            runtimes=(runtime(),),
            qualifications=(qualification(),),
            executor=executor,
        )
        with self.assertRaises(ValueError):
            verify_observation(
                blocked,
                previous_progress(),
                current_progress(),
                verification(),
            )

    def test_verification_expected_scope_cannot_expand_original_request(self):
        record, _ = execute_fixture()
        with self.assertRaises(ValueError):
            verify_observation(
                record,
                previous_progress(),
                current_progress(),
                verification(expected_scope=("src/a.py", "src/b.py")),
            )

    def test_changed_files_outside_request_are_rejected_even_with_verification_phase(self):
        record, _ = execute_fixture()
        final = verify_observation(
            record,
            previous_progress(),
            current_progress(),
            verification(changed_files=("src/a.py", "src/b.py")),
        )
        self.assertEqual(final.status, SpineStatus.REJECTED)
        self.assertEqual(final.reason, SpineReason.VERIFICATION_REJECTED)

    def test_verification_task_identity_must_match(self):
        record, _ = execute_fixture()
        with self.assertRaises(ValueError):
            verify_observation(
                record,
                previous_progress(),
                current_progress(),
                verification(task_id="other-task"),
            )

    def test_record_serialization_is_deterministic(self):
        record, _ = execute_fixture()
        first = record.to_json()
        second = record.to_json()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
