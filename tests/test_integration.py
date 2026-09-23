import unittest

from arkx.integration import AdapterIdentity, CapabilityProvenance, DependencyObservation, IntegrationKind, PreflightStatus, assess_preflight, exception_error_envelope, preflight_error, process_error_envelope, provider_error_envelope
from arkx.harness import ErrorDomain, Retryability


class IntegrationContractTests(unittest.TestCase):
    def test_ready_preflight_is_deterministic_and_evidence_bearing(self):
        identity = AdapterIdentity(IntegrationKind.PROVIDER, "openrouter", "1", "cfg")
        dependencies = (DependencyObservation("runtime", True, "3.11"),)
        first = assess_preflight(identity, dependencies, capabilities=("completion",), evidence_refs=("evidence://preflight",))
        second = assess_preflight(identity, dependencies, capabilities=("completion",), evidence_refs=("evidence://preflight",))
        self.assertEqual(first.status, PreflightStatus.READY)
        self.assertEqual(first.to_json(), second.to_json())
        self.assertTrue(first.reference.startswith("preflight://"))

    def test_preflight_carries_capability_identity_and_provenance(self):
        identity = AdapterIdentity(IntegrationKind.EXECUTOR, "executor", "1", "cfg")
        result = assess_preflight(
            identity,
            (DependencyObservation("runtime", True, "1"),),
            capabilities=("patch",),
            capability_digest="capability-digest",
            capability_provenance=CapabilityProvenance.OBSERVED,
        )
        self.assertEqual(result.capability_digest, "capability-digest")
        self.assertEqual(result.capability_provenance, CapabilityProvenance.OBSERVED)
        with self.assertRaises(ValueError):
            assess_preflight(
                identity,
                (DependencyObservation("runtime", True, "1"),),
                capabilities=("patch",),
                capability_provenance=CapabilityProvenance.QUALIFIED,
            )

    def test_missing_dependency_blocks_without_fallback(self):
        identity = AdapterIdentity(IntegrationKind.SANDBOX, "docker")
        result = assess_preflight(identity, (DependencyObservation("daemon", False, reason="permission denied"),))
        self.assertEqual(result.status, PreflightStatus.BLOCKED)
        self.assertEqual(result.dependencies[0].reason, "permission denied")

    def test_missing_identity_or_unknown_dependency_stays_unknown(self):
        unknown_identity = AdapterIdentity(IntegrationKind.EXECUTOR, "runner")
        self.assertEqual(assess_preflight(unknown_identity, ()).status, PreflightStatus.UNKNOWN)
        identity = AdapterIdentity(IntegrationKind.EVALUATOR, "swebench", "1", "cfg")
        self.assertEqual(assess_preflight(identity, (DependencyObservation("docker", None),)).status, PreflightStatus.UNKNOWN)

    def test_preflight_error_preserves_boundary_and_unknown_retryability(self):
        identity = AdapterIdentity(IntegrationKind.PROVIDER, "openrouter")
        preflight = assess_preflight(identity, (DependencyObservation("minisweagent", False),))
        error = preflight_error(preflight)
        self.assertEqual(error.domain, ErrorDomain.PROVIDER)
        self.assertEqual(error.code, "PREFLIGHT_BLOCKED")
        self.assertEqual(error.retryability, Retryability.UNKNOWN)
        self.assertEqual(error.raw_evidence_refs, (preflight.reference,))

    def test_provider_payload_normalization_preserves_raw_reference(self):
        error = provider_error_envelope(
            {"error": {"code": 503, "message": "overloaded", "metadata": {"error_type": "busy"}}},
            raw_evidence_refs=("artifact://provider.json",),
        )
        self.assertEqual(error.domain, ErrorDomain.PROVIDER)
        self.assertEqual(error.code, "PROVIDER_503")
        self.assertEqual(error.retryability, Retryability.UNKNOWN)
        self.assertEqual(error.raw_evidence_refs, ("artifact://provider.json",))

    def test_process_and_exception_normalization_preserve_boundary(self):
        process = process_error_envelope(
            IntegrationKind.SANDBOX,
            returncode=126,
            message="permission denied",
            raw_evidence_refs=("artifact://sandbox.log",),
        )
        exception = exception_error_envelope(IntegrationKind.EVALUATOR, RuntimeError("daemon unavailable"))
        self.assertEqual(process.code, "SANDBOX_PROCESS_126")
        self.assertEqual(process.domain, ErrorDomain.SANDBOX)
        self.assertEqual(exception.domain, ErrorDomain.VERIFICATION)
        self.assertEqual(exception.retryability, Retryability.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
