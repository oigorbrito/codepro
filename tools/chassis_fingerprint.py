"""Deterministic semantic fingerprint for the executor-agnostic Arkx chassis."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from arkx.environment import EnvironmentManifest, freeze_environment_manifest
from arkx.promotion import PromotionGate, freeze_promotion_gate
from arkx.provenance import RunManifest, freeze_run_manifest
from arkx.study import StudySpec, freeze_study_spec
from arkx.treatment import TreatmentConfiguration, freeze_treatment_configuration
from arkx.workload import WorkloadManifest, freeze_workload_manifest


ROOT = Path(__file__).parents[1]
EXPERIMENTS = ROOT / "experiments"


def _fixture(name: str, key: str) -> dict:
    payload = json.loads((EXPERIMENTS / name).read_text(encoding="utf-8"))
    return payload[key]


def components() -> dict[str, str]:
    return {
        "environment": freeze_environment_manifest(
            EnvironmentManifest.from_dict(
                _fixture("environment-manifest-fixture.json", "environment")
            )
        ).content_hash,
        "promotion_gate": freeze_promotion_gate(
            PromotionGate.from_dict(
                _fixture("promotion-gate-fixture.json", "gate")
            )
        ).content_hash,
        "run_manifest": freeze_run_manifest(
            RunManifest.from_dict(
                _fixture("run-manifest-fixture.json", "run_manifest")
            )
        ).content_hash,
        "study": freeze_study_spec(
            StudySpec.from_dict(
                _fixture("study-spec-fixture.json", "study_spec")
            )
        ).content_hash,
        "treatment": freeze_treatment_configuration(
            TreatmentConfiguration.from_dict(
                _fixture("treatment-configuration-fixture.json", "configuration")
            )
        ).content_hash,
        "workload": freeze_workload_manifest(
            WorkloadManifest.from_dict(
                _fixture("workload-manifest-fixture.json", "workload")
            )
        ).content_hash,
    }


def fingerprint() -> str:
    payload = json.dumps(
        components(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> int:
    result = {"components": components(), "fingerprint": fingerprint()}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
