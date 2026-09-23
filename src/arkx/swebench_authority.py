"""Official SWE-bench Verified acquisition and acceptance adapter.

The dataset loader is the only source of task metadata.  The gold ``patch``
field is retained only in a provenance record and is never included in the
executor payload or prediction produced by this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
from typing import Any, Callable, Iterable

from .harness import ErrorDomain, ErrorEnvelope, Retryability
from .outcomes import AcceptanceDecision, AcceptanceResult, VerificationResult, VerificationState


DATASET_IDENTITY = "SWE-bench/SWE-bench_Verified"
DATASET_SPLIT = "test"
AUTHORITY_IDENTITY = "swebench.harness.run_evaluation"


class OfficialEvaluationStatus(str, Enum):
    RESOLVED = "RESOLVED"
    TESTS_FAILED = "TESTS_FAILED"
    INFRASTRUCTURE_ERROR = "INFRASTRUCTURE_ERROR"
    AMBIGUOUS = "AMBIGUOUS"
    NOT_EXECUTED = "NOT_EXECUTED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class SWEbenchRecord:
    instance_id: str
    repo: str
    base_commit: str
    problem_statement: str
    version: str
    environment_setup_commit: str | None
    fail_to_pass: tuple[str, ...]
    pass_to_pass: tuple[str, ...]
    test_patch: str
    gold_patch: str | None
    dataset_revision: str | None
    retrieved_at: str

    @classmethod
    def from_row(cls, row: dict[str, Any], *, revision: str | None, retrieved_at: str) -> "SWEbenchRecord":
        required = ("instance_id", "repo", "base_commit", "problem_statement", "version", "test_patch")
        missing = [name for name in required if row.get(name) is None]
        if missing:
            raise ValueError(f"SWE-bench record missing fields: {','.join(missing)}")
        return cls(
            instance_id=row["instance_id"], repo=row["repo"], base_commit=row["base_commit"],
            problem_statement=row["problem_statement"], version=row["version"],
            environment_setup_commit=row.get("environment_setup_commit"),
            fail_to_pass=tuple(row.get("FAIL_TO_PASS") or ()),
            pass_to_pass=tuple(row.get("PASS_TO_PASS") or ()), test_patch=row["test_patch"],
            gold_patch=row.get("patch"), dataset_revision=revision, retrieved_at=retrieved_at,
        )

    def executor_payload(self) -> dict[str, Any]:
        """Return inference input; gold patch and grading labels are excluded."""
        return {"instance_id": self.instance_id, "repo": self.repo, "base_commit": self.base_commit,
                "problem_statement": self.problem_statement, "version": self.version,
                "environment_setup_commit": self.environment_setup_commit}

    def to_dict(self, include_gold_provenance: bool = True) -> dict[str, Any]:
        value = {"instance_id": self.instance_id, "repo": self.repo, "base_commit": self.base_commit,
                 "problem_statement": self.problem_statement, "version": self.version,
                 "environment_setup_commit": self.environment_setup_commit,
                 "FAIL_TO_PASS": list(self.fail_to_pass), "PASS_TO_PASS": list(self.pass_to_pass),
                 "test_patch": self.test_patch, "dataset_revision": self.dataset_revision,
                 "retrieved_at": self.retrieved_at}
        if include_gold_provenance:
            value["gold_patch_sha256"] = None if self.gold_patch is None else _sha256(self.gold_patch)
        return value


def _sha256(value: str) -> str:
    import hashlib
    return hashlib.sha256(value.encode()).hexdigest()


def load_verified_records(instance_ids: Iterable[str], *, revision: str | None = None) -> tuple[SWEbenchRecord, ...]:
    """Load exact public records from Hugging Face; no local dataset is invented."""
    from datasets import load_dataset
    wanted = set(instance_ids)
    if not wanted:
        raise ValueError("at least one instance_id is required")
    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    found: list[SWEbenchRecord] = []
    for row in load_dataset(DATASET_IDENTITY, split=DATASET_SPLIT, streaming=True):
        if row["instance_id"] in wanted:
            found.append(SWEbenchRecord.from_row(row, revision=revision, retrieved_at=retrieved_at))
        if len(found) == len(wanted):
            break
    if {item.instance_id for item in found} != wanted:
        raise LookupError("requested instance_ids were not all found in official test split")
    return tuple(sorted(found, key=lambda item: item.instance_id))


@dataclass(frozen=True)
class SWEbenchPrediction:
    instance_id: str
    model_name_or_path: str
    model_patch: str

    def to_dict(self) -> dict[str, str]:
        return {"instance_id": self.instance_id, "model_name_or_path": self.model_name_or_path,
                "model_patch": self.model_patch}


@dataclass(frozen=True)
class OfficialEvaluationResult:
    status: OfficialEvaluationStatus
    authority: str
    run_id: str
    instance_id: str
    raw_outcome: str | None
    report_path: str | None
    log_paths: tuple[str, ...]
    error: str | None = None

    def verification_result(self) -> VerificationResult:
        """Convert the evaluator observation into a neutral verification outcome."""
        mapping = {
            OfficialEvaluationStatus.RESOLVED: VerificationState.PASS,
            OfficialEvaluationStatus.TESTS_FAILED: VerificationState.FAIL,
            OfficialEvaluationStatus.INFRASTRUCTURE_ERROR: VerificationState.INDETERMINATE,
            OfficialEvaluationStatus.AMBIGUOUS: VerificationState.INDETERMINATE,
            OfficialEvaluationStatus.NOT_EXECUTED: VerificationState.NOT_EXECUTED,
            OfficialEvaluationStatus.BLOCKED: VerificationState.BLOCKED,
        }
        evidence = tuple(sorted(path for path in (self.report_path, *self.log_paths) if path))
        outcomes = tuple(value for value in (self.raw_outcome, self.error) if value)
        return VerificationResult(
            mapping[self.status],
            self.authority,
            ("swebench.harness.run_evaluation",),
            outcomes or (self.status.value,),
            evidence,
        )

    def error_envelope(self) -> ErrorEnvelope | None:
        """Expose evaluator/infrastructure failure without turning test failure into an error."""
        if self.status in (OfficialEvaluationStatus.RESOLVED, OfficialEvaluationStatus.TESTS_FAILED):
            return None
        references = tuple(path for path in (self.report_path, *self.log_paths) if path)
        message = self.error or self.raw_outcome or f"official evaluation status: {self.status.value}"
        return ErrorEnvelope(
            ErrorDomain.VERIFICATION,
            f"EVALUATOR_{self.status.value}",
            message,
            Retryability.UNKNOWN,
            references,
        )

    def acceptance(self) -> AcceptanceResult:
        mapping = {
            OfficialEvaluationStatus.RESOLVED: AcceptanceDecision.ACCEPTED,
            OfficialEvaluationStatus.TESTS_FAILED: AcceptanceDecision.REJECTED,
            OfficialEvaluationStatus.INFRASTRUCTURE_ERROR: AcceptanceDecision.INDETERMINATE,
            OfficialEvaluationStatus.AMBIGUOUS: AcceptanceDecision.INDETERMINATE,
            OfficialEvaluationStatus.NOT_EXECUTED: AcceptanceDecision.NOT_EXECUTED,
            OfficialEvaluationStatus.BLOCKED: AcceptanceDecision.BLOCKED,
        }
        return AcceptanceResult(mapping[self.status], self.authority, self.raw_outcome,
                                tuple(path for path in (self.report_path, *self.log_paths) if path))

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status.value, "authority": self.authority, "run_id": self.run_id,
                "instance_id": self.instance_id, "raw_outcome": self.raw_outcome,
                "report_path": self.report_path, "log_paths": list(self.log_paths), "error": self.error}


OfficialEvaluator = Callable[[dict[str, Any]], OfficialEvaluationResult]


class SWEbenchOfficialAuthority:
    """Adapter boundary around the official harness, with explicit run identity."""

    def __init__(self, artifact_root: str, evaluator: OfficialEvaluator | None = None) -> None:
        self.artifact_root = Path(artifact_root)
        self.evaluator = evaluator or self._invoke_harness
        self.identity = AUTHORITY_IDENTITY

    def evaluate(self, *, record: SWEbenchRecord, model_name_or_path: str, model_patch: str, run_id: str) -> OfficialEvaluationResult:
        if not model_name_or_path or not run_id:
            return OfficialEvaluationResult(OfficialEvaluationStatus.BLOCKED, self.identity, run_id,
                                            record.instance_id, None, None, (), "model and run_id are required")
        root = self.artifact_root / run_id / record.instance_id
        if root.exists():
            return OfficialEvaluationResult(OfficialEvaluationStatus.BLOCKED, self.identity, run_id,
                                            record.instance_id, None, None, (), "evaluation artifact already exists")
        root.mkdir(parents=True)
        prediction = SWEbenchPrediction(record.instance_id, model_name_or_path, model_patch)
        prediction_path = root / "prediction.jsonl"
        prediction_path.write_text(json.dumps(prediction.to_dict(), ensure_ascii=False) + "\n", encoding="utf-8")
        payload = {"dataset_name": DATASET_IDENTITY, "split": DATASET_SPLIT, "instance_ids": [record.instance_id],
                   "predictions_path": str(prediction_path), "run_id": run_id, "artifact_root": str(root)}
        try:
            result = self.evaluator(payload)
            if result.authority != self.identity or result.run_id != run_id:
                raise ValueError("official evaluation identity mismatch")
            return result
        except Exception as error:
            return OfficialEvaluationResult(OfficialEvaluationStatus.INFRASTRUCTURE_ERROR, self.identity, run_id,
                                            record.instance_id, None, None, (), f"{type(error).__name__}: {error}")

    def evaluate_gold(self, *, record: SWEbenchRecord, run_id: str) -> OfficialEvaluationResult:
        """Run the harness' supported ``predictions_path=gold`` qualification."""
        if not run_id:
            return OfficialEvaluationResult(OfficialEvaluationStatus.BLOCKED, self.identity, run_id,
                                            record.instance_id, None, None, (), "run_id is required")
        root = self.artifact_root / run_id / record.instance_id
        if root.exists():
            return OfficialEvaluationResult(OfficialEvaluationStatus.BLOCKED, self.identity, run_id,
                                            record.instance_id, None, None, (), "evaluation artifact already exists")
        root.mkdir(parents=True)
        payload = {"dataset_name": DATASET_IDENTITY, "split": DATASET_SPLIT, "instance_ids": [record.instance_id],
                   "predictions_path": "gold", "run_id": run_id, "artifact_root": str(root)}
        try:
            result = self.evaluator(payload)
            if result.authority != self.identity or result.run_id != run_id:
                raise ValueError("official evaluation identity mismatch")
            return result
        except Exception as error:
            return OfficialEvaluationResult(OfficialEvaluationStatus.INFRASTRUCTURE_ERROR, self.identity, run_id,
                                            record.instance_id, None, None, (), f"{type(error).__name__}: {error}")

    @staticmethod
    def _invoke_harness(payload: dict[str, Any]) -> OfficialEvaluationResult:
        from swebench.harness.run_evaluation import main
        main(dataset_name=payload["dataset_name"], split=payload["split"], instance_ids=payload["instance_ids"],
             predictions_path=payload["predictions_path"], max_workers=1, open_file_limit=4096,
             run_id=payload["run_id"], timeout=1800, rewrite_reports=True, modal=False)
        report = Path("logs") / "evaluation" / payload["run_id"] / "results.json"
        if not report.exists():
            return OfficialEvaluationResult(OfficialEvaluationStatus.AMBIGUOUS, AUTHORITY_IDENTITY, payload["run_id"],
                                            payload["instance_ids"][0], None, str(report), ())
        data = json.loads(report.read_text(encoding="utf-8"))
        outcome = str(data.get(payload["instance_ids"][0], data.get("resolved", "UNKNOWN")))
        status = OfficialEvaluationStatus.RESOLVED if outcome.lower() in {"true", "resolved", "pass"} else OfficialEvaluationStatus.TESTS_FAILED
        return OfficialEvaluationResult(status, AUTHORITY_IDENTITY, payload["run_id"], payload["instance_ids"][0], outcome, str(report), ())


def qualify_gold(*, instance_id: str, run_id: str, artifact_root: str) -> OfficialEvaluationResult:
    """Describe the official gold qualification call; caller must have swebench + Docker."""
    authority = SWEbenchOfficialAuthority(artifact_root)
    record = load_verified_records((instance_id,))[0]
    return authority.evaluate_gold(record=record, run_id=run_id)
