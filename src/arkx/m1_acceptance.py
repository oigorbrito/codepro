"""Evidence-only acceptance review for the frozen first CodePro M1 task."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .acceptance import AcceptanceDecision, AcceptanceReason, AcceptanceStatus


M1_TASK_REF = "github://oigorbrito/codepro/issues/57"
M1_REQUEST_ID = "m1-doctor-json-1"
M1_TASK_ID = "issue-57-doctor-json"
M1_BASE_SHA = "e401936979aea7f875508394aab1dac8f9e850d0"
M1_ACCEPTANCE_AUTHORITY = "acceptance://independent-pending"
M1_ACCEPTANCE_AUTHORITY_EVIDENCE = "codepro://policy/m1-doctor-json-evidence-review-v1"
M1_SCOPE = ("src/arkx/cli.py", "tests/test_cli.py")


def review_m1_doctor_json(evidence_root: str | Path) -> AcceptanceDecision:
    """Review persisted M1 evidence without re-executing the task or verifier."""

    root = Path(evidence_root).expanduser().resolve()
    summary_path = root / "m1-summary.json"
    summary = _load_json(summary_path)

    run_id = str(summary.get("vertical_result", {}).get("run_id") or "")
    refs: list[str] = [_file_ref(summary_path)]
    failures: list[str] = []

    _expect(summary.get("classification") == "M1_REAL_VERTICAL_VERIFIED", "m1 classification", failures)
    _expect(summary.get("task_ref") == M1_TASK_REF, "task_ref", failures)
    _expect(summary.get("request_id") == M1_REQUEST_ID, "request_id", failures)
    _expect(summary.get("task_id") == M1_TASK_ID, "task_id", failures)
    _expect(summary.get("target_base_sha") == M1_BASE_SHA, "target_base_sha", failures)
    _expect(summary.get("provider_called") is False, "provider_called=false", failures)
    _expect(summary.get("model_called") is False, "model_called=false", failures)
    _expect(summary.get("promotion") == "NOT_AUTHORIZED", "promotion not authorized", failures)

    executor = summary.get("executor") or {}
    _expect(executor.get("id") == "local-command", "executor identity", failures)
    _expect(executor.get("selection") == "EXPLICIT", "executor selection explicit", failures)
    _expect(executor.get("fallback_allowed") is False, "fallback disabled", failures)
    _expect(tuple(sorted(summary.get("observed_changed_files") or ())) == tuple(sorted(M1_SCOPE)), "observed scope exact", failures)

    steps = summary.get("steps") or {}
    before = steps.get("target_status_before") or {}
    after = steps.get("target_status_after") or {}
    diff_check = steps.get("diff_check") or {}
    head = steps.get("target_head") or {}
    _expect(before.get("returncode") == 0 and not str(before.get("stdout") or "").strip(), "target clean before execution", failures)
    _expect(head.get("returncode") == 0 and str(head.get("stdout") or "").strip() == M1_BASE_SHA, "target HEAD exact", failures)
    _expect(diff_check.get("returncode") == 0, "git diff --check", failures)
    _expect(after.get("returncode") == 0, "target status after available", failures)

    vertical = summary.get("vertical_result") or {}
    _expect(vertical.get("status") == "VERIFIED", "vertical VERIFIED", failures)
    _expect(vertical.get("reason") == "DECLARED_VERIFIER_PASSED", "vertical verifier reason", failures)
    _expect(tuple(sorted(vertical.get("changed_files") or ())) == tuple(sorted(M1_SCOPE)), "vertical scope exact", failures)
    _expect(bool(run_id), "run_id present", failures)

    run_root_raw = vertical.get("evidence_root")
    if not isinstance(run_root_raw, str) or not run_root_raw.strip():
        failures.append("run evidence root missing")
        return _blocked(run_id or "unknown-run", refs, failures)
    run_root = Path(run_root_raw).expanduser().resolve()
    if root != run_root and root not in run_root.parents:
        failures.append("run evidence root escapes M1 evidence root")
        return _blocked(run_id or "unknown-run", refs, failures)

    required = {
        "request": run_root / "request.json",
        "grant": run_root / "authority-grant.json",
        "execution": run_root / "execution.json",
        "changed": run_root / "changed-files.json",
        "patch": run_root / "workspace.patch",
        "verification": run_root / "verification-summary.json",
        "result": run_root / "result.json",
        "git_head": run_root / "git-head.json",
        "git_status": run_root / "git-status-before.json",
    }
    missing = [name for name, path in required.items() if not path.is_file()]
    if missing:
        failures.append("missing run evidence: " + ",".join(sorted(missing)))
        return _blocked(run_id or "unknown-run", refs, failures)

    for path in required.values():
        refs.append(_file_ref(path))

    request = _load_json(required["request"])
    grant = _load_json(required["grant"])
    execution = _load_json(required["execution"])
    changed = _load_json(required["changed"])
    verification = _load_json(required["verification"])
    result = _load_json(required["result"])
    git_head = _load_json(required["git_head"])
    git_status = _load_json(required["git_status"])
    patch = required["patch"].read_text(encoding="utf-8")

    _expect(request.get("request_id") == M1_REQUEST_ID, "request evidence request_id", failures)
    _expect(request.get("task_ref") == M1_TASK_ID, "request evidence task_ref", failures)
    _expect(tuple(sorted(request.get("requested_scope") or ())) == tuple(sorted(M1_SCOPE)), "request scope exact", failures)

    _expect(grant.get("request_id") == M1_REQUEST_ID, "grant request_id", failures)
    _expect(grant.get("acceptance_authority_ref") == M1_ACCEPTANCE_AUTHORITY, "acceptance authority binding", failures)
    _expect(tuple(sorted(grant.get("authorized_scope") or ())) == tuple(sorted(M1_SCOPE)), "grant scope exact", failures)
    _expect(grant.get("max_commands") == 1, "single-command budget", failures)

    _expect(execution.get("status") == "EXECUTED", "execution status EXECUTED", failures)
    _expect(execution.get("reason") == "EXECUTION_OBSERVED", "execution observed", failures)
    _expect(execution.get("invocation_state") == "OBSERVED", "invocation observed", failures)
    command = execution.get("command_result") or {}
    _expect(command.get("timed_out") is False, "execution not timed out", failures)
    _expect(command.get("environment_error") is None, "execution environment healthy", failures)
    _expect(command.get("exit_code") == 0, "executor command exit zero", failures)

    _expect(tuple(sorted(changed.get("changed_files") or ())) == tuple(sorted(M1_SCOPE)), "changed-files evidence exact", failures)

    _expect(verification.get("status") == "PASSED", "verification PASSED", failures)
    _expect(verification.get("returncode") == 0, "verification returncode zero", failures)
    _expect(verification.get("error_kind") is None, "verification no invocation error", failures)
    verification_ref = verification.get("evidence_ref")
    _expect(isinstance(verification_ref, str) and bool(verification_ref.strip()), "verification evidence ref", failures)

    _expect(result.get("run_id") == run_id, "result run_id", failures)
    _expect(result.get("status") == "VERIFIED", "result VERIFIED", failures)
    _expect(result.get("reason") == "DECLARED_VERIFIER_PASSED", "result verifier passed", failures)

    _expect(git_head.get("returncode") == 0 and str(git_head.get("stdout") or "").strip() == M1_BASE_SHA, "run git HEAD exact", failures)
    _expect(git_status.get("returncode") == 0 and not str(git_status.get("stdout") or "").strip(), "run git status initially clean", failures)

    _expect(bool(patch.strip()), "workspace patch non-empty", failures)
    _expect("diff --git a/src/arkx/cli.py b/src/arkx/cli.py" in patch, "cli patch present", failures)
    _expect("diff --git a/tests/test_cli.py b/tests/test_cli.py" in patch, "CLI test patch present", failures)
    _expect('doctor_parser.add_argument("--json"' in patch, "doctor --json implementation present", failures)
    _expect("test_doctor_json_output_is_canonical" in patch, "doctor JSON acceptance test present", failures)
    _expect('json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))' in patch, "canonical JSON serialization present", failures)

    raw_verification = tuple((run_root / "verification").rglob("verification-*.json"))
    _expect(len(raw_verification) == 1, "exactly one raw verifier observation", failures)
    if len(raw_verification) == 1:
        refs.append(_file_ref(raw_verification[0]))
        raw = _load_json(raw_verification[0])
        raw_result = raw.get("result") or {}
        _expect(raw.get("run_id") == run_id, "raw verifier run_id", failures)
        _expect(raw_result.get("status") == "PASSED", "raw verifier PASSED", failures)
        _expect(raw_result.get("exit_code") == 0, "raw verifier exit zero", failures)
        _expect(raw.get("error_kind") is None, "raw verifier no invocation error", failures)

    if failures:
        return _blocked(run_id or "unknown-run", refs, failures)

    rationale = (
        "Independent evidence-only review confirmed the frozen Issue #57 criteria, "
        "exact base and scope, observed bounded execution, persisted verifier PASS, "
        "canonical doctor --json implementation/test patch, and no provider/model/fallback."
    )
    return AcceptanceDecision(
        AcceptanceStatus.ACCEPTED,
        AcceptanceReason.VERIFIED,
        M1_ACCEPTANCE_AUTHORITY,
        run_id,
        _file_ref(required["execution"]),
        str(verification_ref),
        tuple(sorted(set(refs + [M1_ACCEPTANCE_AUTHORITY_EVIDENCE]))),
        rationale,
    )


def persist_acceptance(evidence_root: str | Path, decision: AcceptanceDecision) -> Path:
    root = Path(evidence_root).expanduser().resolve()
    target = root / "acceptance.json"
    if target.exists():
        raise FileExistsError(f"acceptance evidence already exists: {target}")
    payload = {
        "schema_version": 1,
        "authority_identity_evidence_ref": M1_ACCEPTANCE_AUTHORITY_EVIDENCE,
        "independent_of_executor": True,
        "decision": decision.to_dict(),
        "promotion": "NOT_AUTHORIZED",
    }
    content = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    temporary = target.with_name(target.name + f".tmp-{os.getpid()}")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    try:
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()
    return target


def _blocked(run_id: str, refs: list[str], failures: list[str]) -> AcceptanceDecision:
    return AcceptanceDecision(
        AcceptanceStatus.BLOCKED,
        AcceptanceReason.EVIDENCE_REQUIRED,
        M1_ACCEPTANCE_AUTHORITY,
        run_id,
        None,
        None,
        tuple(sorted(set(refs))),
        "Evidence review failed closed: " + "; ".join(failures),
    )


def _expect(condition: bool, label: str, failures: list[str]) -> None:
    if not condition:
        failures.append(label)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _file_ref(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"file+sha256://{digest}/{path.name}"
