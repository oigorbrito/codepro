"""Minimal dependency-free CodePro command-line interface."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from collections.abc import Sequence

from . import __version__
from .project import inspect_project
from .vertical import VerticalRunStatus, run_vertical


_SUPPORTED_MIN = (3, 10)
_SUPPORTED_MAX = (3, 14)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="codepro",
        description="Deterministic CLI boundary for the CodePro software-engineering chassis.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "doctor",
        help="Check whether the local Python runtime can execute the current chassis.",
        description="Check the local runtime and core package import boundary.",
    )

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect the current project without changing it.",
        description="Inspect Git context, project markers, tests, and known executor binaries.",
    )
    inspect_parser.add_argument("path", nargs="?", default=".")
    inspect_parser.add_argument("--json", action="store_true", dest="as_json")

    run_parser = subparsers.add_parser(
        "run",
        help="Run one authorized, bounded executor command and declared verifier.",
        description=(
            "Execute one explicit command against one exact clean Git revision, "
            "enforce authorized changed-file scope, run one declared verifier, "
            "and persist run evidence."
        ),
    )
    run_parser.add_argument("--workspace", required=True)
    run_parser.add_argument("--revision", required=True)
    run_parser.add_argument("--request-id", required=True)
    run_parser.add_argument("--task-id", required=True)
    run_parser.add_argument("--requester", required=True)
    run_parser.add_argument("--authority", required=True)
    run_parser.add_argument("--acceptance-authority", required=True)
    run_parser.add_argument("--scope", action="append", required=True)
    run_parser.add_argument(
        "--candidate-file",
        action="append",
        required=True,
        help="Explicit characterization candidate file; does not expand authorized scope.",
    )
    run_parser.add_argument(
        "--affected-component",
        action="append",
        required=True,
        help="Explicit characterized component; separate from authorization scope.",
    )
    run_parser.add_argument(
        "--characterization-source-ref",
        required=True,
        help="Evidence/provenance reference for the explicit characterization inputs.",
    )
    run_parser.add_argument("--max-wall-time", type=float, default=300.0)
    run_parser.add_argument(
        "--attempt-id",
        default="attempt-1",
        help="Explicit attempt identity used in the persisted run identity.",
    )
    run_parser.add_argument(
        "--evidence-dir",
        required=True,
        help="Evidence root outside the target workspace; existing run identities are never overwritten.",
    )
    run_parser.add_argument(
        "--verifier-argv-json",
        required=True,
        help='JSON array argv for the verifier, e.g. ["python","-m","pytest","-q"].',
    )
    run_parser.add_argument(
        "executor_argv",
        nargs=argparse.REMAINDER,
        help="Executor argv after --. No shell interpretation is used.",
    )

    baseline_parser = subparsers.add_parser(
        "baseline-cost",
        help="Measure local overhead without changing behavior.",
    )
    baseline_parser.add_argument("--workspace", default=".")
    baseline_parser.add_argument("--output", required=True)
    baseline_parser.add_argument("--samples", type=int, default=5)
    return parser


def _doctor() -> int:
    version = sys.version_info[:2]
    supported = _SUPPORTED_MIN <= version <= _SUPPORTED_MAX

    checks = (
        ("python", supported, platform.python_version()),
        ("core", True, "importable"),
    )
    for name, ok, detail in checks:
        state = "PASS" if ok else "FAIL"
        print(f"{name}: {state} ({detail})")

    overall = all(ok for _, ok, _ in checks)
    print(f"status: {'PASS' if overall else 'FAIL'}")
    return 0 if overall else 1


def _inspect(path: str, *, as_json: bool) -> int:
    try:
        inspection = inspect_project(path)
    except ValueError as exc:
        print(f"codepro: error: {exc}", file=sys.stderr)
        return 2

    if as_json:
        print(inspection.to_json())
        return 0

    print(f"Project: {inspection.project_name}")
    print(f"Root: {inspection.project_root}")
    print(f"Git: {'yes' if inspection.git_available else 'no'}")
    print(f"Repository: {'yes' if inspection.git_repository else 'no'}")
    print(f"Branch: {inspection.branch or 'n/a'}")
    print("Languages: " + (", ".join(inspection.languages) if inspection.languages else "none"))
    print(
        "Test surfaces: "
        + (", ".join(inspection.test_surfaces) if inspection.test_surfaces else "none")
    )
    print("Executors:")
    for name, command, available in inspection.executors:
        print(f"  {name}: {'available' if available else 'unavailable'} ({command})")
    return 0


def _run(args: argparse.Namespace) -> int:
    try:
        verifier_argv = json.loads(args.verifier_argv_json)
    except json.JSONDecodeError as exc:
        print(f"codepro: error: verifier argv is not valid JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(verifier_argv, list) or not verifier_argv or any(
        not isinstance(item, str) or not item for item in verifier_argv
    ):
        print("codepro: error: verifier argv must be a non-empty JSON string array", file=sys.stderr)
        return 2

    executor_argv = list(args.executor_argv)
    if executor_argv and executor_argv[0] == "--":
        executor_argv = executor_argv[1:]
    if not executor_argv:
        print("codepro: error: executor argv must be provided after --", file=sys.stderr)
        return 2

    try:
        result = run_vertical(
            workspace=args.workspace,
            revision=args.revision,
            request_id=args.request_id,
            task_id=args.task_id,
            requester_ref=args.requester,
            authority_ref=args.authority,
            acceptance_authority_ref=args.acceptance_authority,
            scope=tuple(args.scope),
            executor_argv=tuple(executor_argv),
            verifier_argv=tuple(verifier_argv),
            evidence_dir=args.evidence_dir,
            candidate_files=tuple(args.candidate_file),
            affected_components=tuple(args.affected_component),
            characterization_source_ref=args.characterization_source_ref,
            max_wall_time_seconds=args.max_wall_time,
            attempt_id=args.attempt_id,
        )
    except (ValueError, OSError, FileExistsError) as exc:
        print(f"codepro: error: {exc}", file=sys.stderr)
        return 2

    print(result.to_json())
    return 0 if result.status is VerticalRunStatus.VERIFIED else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "doctor":
        return _doctor()
    if args.command == "inspect":
        return _inspect(args.path, as_json=args.as_json)
    if args.command == "run":
        return _run(args)
    if args.command == "baseline-cost":
        from .performance_baseline import main as performance_baseline_main

        return performance_baseline_main(
            [
                "--workspace", args.workspace,
                "--output", args.output,
                "--samples", str(args.samples),
            ]
        )

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
