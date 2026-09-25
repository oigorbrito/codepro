#!/usr/bin/env python3
"""Validate the CodePro vertical journey without claiming an MVP real-task pass."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).parents[1].resolve()
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def run(argv: list[str], *, cwd: Path | None = None, timeout: int = 120) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            argv,
            cwd=None if cwd is None else str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            check=False,
            timeout=timeout,
        )
        return {
            "argv": argv,
            "cwd": None if cwd is None else str(cwd),
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "timeout": False,
            "error": None,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": argv,
            "cwd": None if cwd is None else str(cwd),
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timeout": True,
            "error": "TIMEOUT",
        }
    except OSError as exc:
        return {
            "argv": argv,
            "cwd": None if cwd is None else str(cwd),
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "timeout": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> int:
    report: dict[str, Any] = {
        "schema_version": 1,
        "classification": "BLOCKED",
        "m1_real_task": "NOT_EXECUTED",
        "provider_called": False,
        "codepro_root": str(ROOT),
        "python": {
            "executable": sys.executable,
            "version": ".".join(map(str, sys.version_info[:3])),
            "supported": (3, 12) <= sys.version_info[:2] <= (3, 14),
        },
        "steps": {},
    }

    if not report["python"]["supported"]:
        report["classification"] = "BLOCKED_UNSUPPORTED_PYTHON"
        return finish(report, 2)

    tests = run(
        [
            sys.executable,
            "-m",
            "unittest",
            "-v",
            "tests.test_vertical",
            "tests.test_cli",
        ],
        cwd=ROOT,
        timeout=180,
    )
    report["steps"]["focused_tests"] = tests
    if tests["returncode"] != 0:
        report["classification"] = "BLOCKED_VERTICAL_CONTRACT_TESTS"
        return finish(report, 2)

    from arkx.vertical import VerticalRunStatus, run_vertical

    with tempfile.TemporaryDirectory(prefix="codepro-vertical-validation-") as tmp:
        base = Path(tmp)
        repo = base / "repo"
        evidence = base / "evidence"
        repo.mkdir()

        for argv in (
            ["git", "init"],
            ["git", "config", "user.email", "validation@example.invalid"],
            ["git", "config", "user.name", "CodePro Validation"],
        ):
            result = run(argv, cwd=repo)
            report["steps"].setdefault("fixture_git", []).append(result)
            if result["returncode"] != 0:
                report["classification"] = "BLOCKED_FIXTURE_GIT"
                return finish(report, 2)

        (repo / "src").mkdir()
        (repo / "src" / "value.txt").write_text("before\n", encoding="utf-8")
        for argv in (["git", "add", "."], ["git", "commit", "-m", "base"]):
            result = run(argv, cwd=repo)
            report["steps"]["fixture_git"].append(result)
            if result["returncode"] != 0:
                report["classification"] = "BLOCKED_FIXTURE_GIT"
                return finish(report, 2)

        revision = run(["git", "rev-parse", "HEAD"], cwd=repo)
        report["steps"]["fixture_revision"] = revision
        if revision["returncode"] != 0:
            report["classification"] = "BLOCKED_FIXTURE_GIT"
            return finish(report, 2)

        result = run_vertical(
            workspace=repo,
            revision=revision["stdout"].strip(),
            request_id="implementation-validation-1",
            task_id="fixture-edit-1",
            requester_ref="user://implementation-validation",
            authority_ref="authority://implementation-validation",
            acceptance_authority_ref="acceptance://implementation-validation",
            scope=("src",),
            executor_argv=(
                sys.executable,
                "-c",
                "from pathlib import Path; Path('src/value.txt').write_text('after\\n', encoding='utf-8')",
            ),
            verifier_argv=(
                sys.executable,
                "-c",
                "from pathlib import Path; raise SystemExit(0 if Path('src/value.txt').read_text(encoding='utf-8') == 'after\\n' else 1)",
            ),
            evidence_dir=evidence,
            max_wall_time_seconds=30,
        )
        report["steps"]["controlled_vertical"] = result.to_dict()
        report["steps"]["controlled_vertical"]["evidence_files"] = sorted(
            str(path.relative_to(Path(result.evidence_root)))
            for path in Path(result.evidence_root).rglob("*")
            if path.is_file()
        )

        if result.status is not VerticalRunStatus.VERIFIED:
            report["classification"] = "BLOCKED_CONTROLLED_VERTICAL"
            return finish(report, 2)

    report["classification"] = "VERTICAL_IMPLEMENTATION_VALIDATED"
    return finish(report, 0)


def finish(report: dict[str, Any], code: int) -> int:
    output_root = ROOT / "logs" / "architecture" / "vertical-implementation-validation"
    output_root.mkdir(parents=True, exist_ok=True)
    output = output_root / "validation-summary.json"
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    output.write_text(rendered, encoding="utf-8", newline="\n")
    sys.stdout.write(rendered)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
