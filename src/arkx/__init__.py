"""Stable CodePro package boundary with lazy legacy compatibility.

The neutral result contracts are loaded eagerly. Older root-level exports are
resolved only when explicitly requested, preserving existing imports without
reintroducing the eager experimental import graph.
"""

from __future__ import annotations

from importlib import import_module

__version__ = "0.3.0.dev0"

from .execution import ExecutionResult
from .orchestration_result import ExecutionResult as OrchestrationExecutionResult

_LEGACY_MODULES = (
    "contracts", "configuration", "event_log", "integration", "execution",
    "harness", "outcomes", "verifier", "request", "selection",
    "p82_localization", "p82_editing", "orchestration", "recovery",
    "acceptance", "promotion", "characterization", "progress", "routing",
    "planning", "verification", "handoff", "composition",
    "executor_qualification", "p82", "p82_baseline", "swebench_authority",
)


def __getattr__(name: str):
    """Resolve a legacy root export without eager subsystem imports."""
    if name == "OrchestrationExecutionResult":
        return OrchestrationExecutionResult
    if name == "compare_qualification_trials":
        value = getattr(import_module(f"{__name__}.executor_qualification"), "compare_trials")
        globals()[name] = value
        return value
    for module_name in _LEGACY_MODULES:
        module = import_module(f"{__name__}.{module_name}")
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | {"OrchestrationExecutionResult"})


# Keep wildcard imports compatible with the pre-lazy public boundary.  The
# values remain lazy; this is only the stable name manifest.
__all__ = tuple("""
Event EventType ExecutionRecord ExecutionStatus ConfigurationSnapshot EventLog
AdapterIdentity AdapterPreflight CapabilityProvenance DependencyObservation
IntegrationKind PreflightStatus assess_preflight exception_error_envelope
preflight_error process_error_envelope provider_error_envelope ReplayState
RestoredChainAudit append_promotion_decision ReplayChain ReferenceReport
ChainIntegrity assess_chain_integrity replay_chain classify_chain_references
classify_snapshot_chain_references replay_events audit_restored_chain
validate_attempt_lineage_chain validate_replay_against_manifest
validate_replay_outcomes validate_replay_telemetry validate_final_chain
validate_outcome_chain ExecutionRequest ExecutionPlan CapabilityProfile
CapabilityRegistry ExecutionBudgetSpec BudgetConsumption BudgetLedger RetryDecision
RetryPolicy RetryAttemptPlan plan_retry_attempt execution_reference
validate_execution_chain ExecutionResult ContractRun Executor Provider Sandbox
ProviderRequest ProviderResponse validate_provider_identity
validate_sandbox_identity SandboxRequest FakeExecutor FakeProvider FakeSandbox
ErrorDomain ArtifactStore AuditedComparison ArtifactRecord ArtifactStatus
AttemptSnapshot AttemptStore AttemptComparison AttemptEvidence VerificationEvidence
AcceptanceEvidence ExperimentRecord ExperimentSnapshot validate_experiment_record
validate_experiment_record_audited write_experiment_record load_experiment_record
ComparabilityStatus compare_attempts ComparisonReport PairComparison
compare_attempt_collection evidence_from_snapshot LifecycleEvent ErrorEnvelope
Retryability RetryLineage RecoveryLineage RunManifest RunState derive_attempt_id
derive_experiment_identity_digest validate_transition
validate_execution_artifact_consistency load_attempt ArkxRequest GovernanceDecision
GovernancePolicy GovernanceReason GovernanceStatus RequestBudget RequestEnvironment
authorize_request characterize_authorized_request ExecutorBinding ExecutorRegistry
SelectionDecision SelectionReason SelectionStatus TreatmentCatalog
TreatmentDefinition select_executor select_treatment ExecutionOutcome
BudgetEnforcedExecutorRunner ContractExecutorRunner OrchestrationExecutionResult
OrchestrationReason OrchestrationResult OrchestrationStatus
orchestration_status_for_acceptance orchestration_status_for_execution
run_routed_pipeline RecoveryAction RecoveryBudget RecoveryDecision RecoveryPlan
RecoveryAttemptPlan RecoveryReason decide_recovery build_recovery_plan
plan_recovery_attempt validate_recovery_reference AcceptancePolicy
decide_independent_acceptance PromotionCandidate PromotionDecision PromotionPolicy
PromotionReason PromotionStatus decide_outcome_promotion decide_promotion
CharacterizationConfig Confidence RecommendedPath Scope TaskCharacterization
TaskSignals characterize characterize_timed ProgressAssessment ProgressConfig
ProgressEvidence ProgressSnapshot ProgressStatus assess_progress assess_progress_timed
BudgetState CapabilityPolicyDecision CapabilityPolicyReason EscalationAction
EscalationDecision EvidenceSufficiency RoutingBudget RoutingDecision
RoutingDecisionType assess_escalation assess_capability_policy route_characterization
PlanStep ReplanRequest ReplanResult ReplanTrigger RepositoryPlan RepositoryState
StepStatus build_plan plan_repository PatchVerificationInput PatchVerificationResult
PatchVerificationStatus TestResult TestResultStatus verify_patch HandoffBudgetStatus
HandoffPolicy HandoffRecord HandoffSummary summarize_handoffs ExperimentIdentity
ComparabilityStatus ExperimentManifest ExperimentSummary Mechanism Treatment TrialObservation
compare_trials initial_manifest summarize_trials ComparisonAxis ExecutionEnvironment
ExecutionOutcome ExecutionBudget ExecutorIdentity ExecutorObservation ExecutorTrial
QualificationExperiment QualificationStatus PairedQualificationReport
validate_paired_executor_experiment QualificationSummary QualificationTask
assess_trial compare_qualification_trials summarize_experiment P82ExperimentConfig
P82ExperimentPlan P82Comparability P82Criteria P82Observation P82ObservationRecord
P82RunManifest P82RunStatus P82Treatment P82TreatmentSummary P82TrialPlan
TaskSampleManifest TaskSampleTask TaskStratum build_p82_plan compare_run_manifests
p82_manifest plan_is_comparable summarize_p82 AcceptanceDecision AcceptanceResult
BaselineExecutionState BaselineRunConfig BaselineSampleManifest
ExplicitVerificationAcceptance ExecutionArtifact MiniSweAgentHeadlessRunner
ProspectiveTask RunnerFailureCategory VerificationResult VerificationState
validate_outcome_references baseline_observation AUTHORITY_IDENTITY
DATASET_IDENTITY DATASET_SPLIT OfficialEvaluationResult OfficialEvaluationStatus
SWEbenchOfficialAuthority SWEbenchPrediction SWEbenchRecord load_verified_records
qualify_gold
""".split())
