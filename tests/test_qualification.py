import json
import unittest

from arkx.qualification import (
    BindingReason,
    BindingStatus,
    CapabilityRequirement,
    ExecutorBinding,
    ExecutorQualification,
    ExecutorRuntime,
    QualificationStatus,
    bind_executor,
)


def requirement(capability="repository-edit"):
    return CapabilityRequirement(
        requirement_id="req-1",
        capability_id=capability,
        source_ref="route://decision/1",
    )


def runtime(
    executor_id="fixture-a",
    *,
    version="1.0",
    adapter="adapter-a",
    adapter_version="1.0",
    available=True,
):
    return ExecutorRuntime(
        executor_id=executor_id,
        executor_version=version,
        adapter_id=adapter,
        adapter_version=adapter_version,
        available=available,
        evidence_ref=f"probe://{executor_id}/{version}/{available}",
    )


def qualification(
    executor_id="fixture-a",
    *,
    version="1.0",
    adapter="adapter-a",
    adapter_version="1.0",
    capability="repository-edit",
    status=QualificationStatus.QUALIFIED,
):
    return ExecutorQualification(
        executor_id=executor_id,
        executor_version=version,
        adapter_id=adapter,
        adapter_version=adapter_version,
        capability_id=capability,
        status=status,
        evidence_refs=(f"qualification://{executor_id}/{version}/{capability}",),
    )


class BindingTests(unittest.TestCase):
    def test_single_available_qualified_identity_binds(self):
        result = bind_executor(
            requirement(),
            (runtime(),),
            (qualification(),),
        )
        self.assertEqual(result.status, BindingStatus.BOUND)
        self.assertEqual(result.reason, BindingReason.SINGLE_QUALIFIED_EXECUTOR)
        self.assertEqual(result.executor_id, "fixture-a")
        self.assertEqual(result.executor_version, "1.0")
        self.assertEqual(result.adapter_id, "adapter-a")
        self.assertTrue(result.availability_evidence_ref)
        self.assertTrue(result.qualification_evidence_refs)

    def test_binary_availability_alone_never_counts_as_qualification(self):
        result = bind_executor(requirement(), (runtime(),), ())
        self.assertEqual(result.status, BindingStatus.REQUIRE_QUALIFICATION)
        self.assertEqual(
            result.reason,
            BindingReason.NO_QUALIFICATION_FOR_AVAILABLE_EXECUTOR,
        )
        self.assertIsNone(result.executor_id)

    def test_qualification_is_bound_to_exact_executor_and_adapter_versions(self):
        result = bind_executor(
            requirement(),
            (runtime(version="2.0"),),
            (qualification(version="1.0"),),
        )
        self.assertEqual(result.status, BindingStatus.REQUIRE_QUALIFICATION)
        self.assertEqual(
            result.reason,
            BindingReason.NO_QUALIFICATION_FOR_AVAILABLE_EXECUTOR,
        )

        adapter_changed = bind_executor(
            requirement(),
            (runtime(adapter_version="2.0"),),
            (qualification(adapter_version="1.0"),),
        )
        self.assertEqual(adapter_changed.status, BindingStatus.REQUIRE_QUALIFICATION)

    def test_explicit_not_qualified_identity_requires_qualification(self):
        result = bind_executor(
            requirement(),
            (runtime(),),
            (qualification(status=QualificationStatus.NOT_QUALIFIED),),
        )
        self.assertEqual(result.status, BindingStatus.REQUIRE_QUALIFICATION)
        self.assertEqual(
            result.reason,
            BindingReason.AVAILABLE_IDENTITY_NOT_QUALIFIED,
        )

    def test_qualified_but_unavailable_is_blocked(self):
        result = bind_executor(
            requirement(),
            (runtime(available=False),),
            (qualification(),),
        )
        self.assertEqual(result.status, BindingStatus.BLOCKED)
        self.assertEqual(
            result.reason,
            BindingReason.QUALIFIED_EXECUTOR_UNAVAILABLE,
        )

    def test_no_available_executor_is_blocked(self):
        result = bind_executor(
            requirement(),
            (runtime(available=False),),
            (),
        )
        self.assertEqual(result.status, BindingStatus.BLOCKED)
        self.assertEqual(result.reason, BindingReason.NO_EXECUTOR_AVAILABLE)

    def test_qualification_for_other_capability_does_not_leak(self):
        result = bind_executor(
            requirement("repository-edit"),
            (runtime(),),
            (qualification(capability="read-only-inspection"),),
        )
        self.assertEqual(result.status, BindingStatus.REQUIRE_QUALIFICATION)

    def test_multiple_available_qualified_executors_block_instead_of_ranking(self):
        result = bind_executor(
            requirement(),
            (
                runtime("fixture-a", adapter="adapter-a"),
                runtime("fixture-b", adapter="adapter-b"),
            ),
            (
                qualification("fixture-a", adapter="adapter-a"),
                qualification("fixture-b", adapter="adapter-b"),
            ),
        )
        self.assertEqual(result.status, BindingStatus.BLOCKED)
        self.assertEqual(
            result.reason,
            BindingReason.AMBIGUOUS_QUALIFIED_EXECUTORS,
        )
        self.assertIsNone(result.executor_id)

    def test_candidate_order_does_not_create_a_hidden_preference(self):
        runtimes = (
            runtime("fixture-a", adapter="adapter-a"),
            runtime("fixture-b", adapter="adapter-b"),
        )
        qualifications = (
            qualification("fixture-a", adapter="adapter-a"),
            qualification("fixture-b", adapter="adapter-b"),
        )
        first = bind_executor(requirement(), runtimes, qualifications)
        second = bind_executor(
            requirement(),
            tuple(reversed(runtimes)),
            tuple(reversed(qualifications)),
        )
        self.assertEqual(first.to_json(), second.to_json())

    def test_duplicate_runtime_or_qualification_identity_is_rejected(self):
        with self.assertRaises(ValueError):
            bind_executor(
                requirement(),
                (runtime(), runtime()),
                (qualification(),),
            )
        with self.assertRaises(ValueError):
            bind_executor(
                requirement(),
                (runtime(),),
                (qualification(), qualification()),
            )


class ContractIntegrityTests(unittest.TestCase):
    def test_qualification_requires_substantive_evidence(self):
        with self.assertRaises(ValueError):
            ExecutorQualification(
                executor_id="fixture",
                executor_version="1",
                adapter_id="adapter",
                adapter_version="1",
                capability_id="edit",
                status=QualificationStatus.QUALIFIED,
                evidence_refs=(),
            )
        with self.assertRaises(ValueError):
            ExecutorQualification(
                executor_id="fixture",
                executor_version="1",
                adapter_id="adapter",
                adapter_version="1",
                capability_id="edit",
                status=QualificationStatus.QUALIFIED,
                evidence_refs=("   ",),
            )

    def test_evidence_refs_are_canonicalized(self):
        value = ExecutorQualification(
            executor_id="fixture",
            executor_version="1",
            adapter_id="adapter",
            adapter_version="1",
            capability_id="edit",
            status=QualificationStatus.QUALIFIED,
            evidence_refs=("z://2", "a://1", "z://2"),
        )
        self.assertEqual(value.evidence_refs, ("a://1", "z://2"))

    def test_bound_result_requires_complete_identity_and_evidence(self):
        with self.assertRaises(ValueError):
            ExecutorBinding(
                requirement_id="req",
                capability_id="edit",
                status=BindingStatus.BOUND,
                reason=BindingReason.SINGLE_QUALIFIED_EXECUTOR,
                executor_id="fixture",
            )

    def test_non_bound_result_cannot_smuggle_executor_identity(self):
        with self.assertRaises(ValueError):
            ExecutorBinding(
                requirement_id="req",
                capability_id="edit",
                status=BindingStatus.BLOCKED,
                reason=BindingReason.NO_EXECUTOR_AVAILABLE,
                executor_id="fixture",
            )

    def test_binding_json_is_deterministic_and_contains_no_ranking_score(self):
        result = bind_executor(
            requirement(),
            (runtime(),),
            (qualification(),),
        )
        self.assertEqual(result.to_json(), result.to_json())
        payload = json.loads(result.to_json())
        self.assertEqual(payload["status"], "BOUND")
        self.assertNotIn("score", payload)
        self.assertNotIn("rank", payload)
        self.assertNotIn("priority", payload)


if __name__ == "__main__":
    unittest.main()
