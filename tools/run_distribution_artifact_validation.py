#!/usr/bin/env python3
"""Validate local distribution artifacts without publishing them."""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
from typing import Any


ROOT = Path(__file__).parents[1].resolve()
EXPECTED_VERSION = "0.3.0.dev1"


def run(
    argv: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 300,
    text: bool = True,
) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            argv,
            cwd=str(cwd or ROOT),
            env=env,
            capture_output=True,
            text=text,
            encoding="utf-8" if text else None,
            errors="replace" if text else None,
            shell=False,
            check=False,
            timeout=timeout,
        )
        return {
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "timeout": False,
            "error": None,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": argv,
            "returncode": None,
            "stdout": exc.stdout or ("" if text else b""),
            "stderr": exc.stderr or ("" if text else b""),
            "timeout": True,
            "error": "TIMEOUT",
        }
    except OSError as exc:
        return {
            "argv": argv,
            "returncode": None,
            "stdout": "" if text else b"",
            "stderr": "" if text else b"",
            "timeout": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    report: dict[str, Any] = {
        "schema_version": 1,
        "classification": "BLOCKED_DISTRIBUTION_ARTIFACT_VALIDATION",
        "release_baseline": "v0.3.0.dev0",
        "release": "UNCHANGED",
        "package_index_publication": "NOT_AUTHORIZED",
        "activation": "NOT_AUTHORIZED",
        "executor_promotion": "NOT_AUTHORIZED",
        "provider_called": False,
        "model_called": False,
        "expected_version": EXPECTED_VERSION,
        "steps": {},
    }

    head = run(["git", "rev-parse", "HEAD"])
    status_before = run(["git", "status", "--porcelain=v1", "--untracked-files=no"])
    untracked_before = run(["git", "ls-files", "--others", "--exclude-standard"])
    report["steps"]["head"] = head
    report["steps"]["status_before"] = status_before
    report["steps"]["untracked_before"] = untracked_before
    if (
        head["returncode"] != 0
        or status_before["returncode"] != 0
        or untracked_before["returncode"] != 0
        or status_before["stdout"].strip()
    ):
        report["classification"] = "BLOCKED_SOURCE_IDENTITY_OR_TRACKED_WORKTREE_CHANGE"
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    archive = run(["git", "archive", "--format=tar", "HEAD"], text=False)
    report["steps"]["git_archive"] = {
        "argv": archive["argv"],
        "returncode": archive["returncode"],
        "stderr": (
            archive["stderr"].decode("utf-8", errors="replace")
            if isinstance(archive["stderr"], bytes)
            else archive["stderr"]
        ),
        "timeout": archive["timeout"],
        "error": archive["error"],
    }
    if archive["returncode"] != 0 or not isinstance(archive["stdout"], bytes):
        report["classification"] = "BLOCKED_GIT_ARCHIVE"
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    with tempfile.TemporaryDirectory(prefix="codepro-dist-") as tmp:
        temp_root = Path(tmp)
        source = temp_root / "source"
        dist = temp_root / "dist"
        source.mkdir()
        dist.mkdir()

        with tarfile.open(fileobj=io.BytesIO(archive["stdout"]), mode="r:") as bundle:
            bundle.extractall(source, filter="fully_trusted")

        build_venv = temp_root / "build-venv"
        create_build_venv = run(
            [sys.executable, "-m", "venv", str(build_venv)],
            cwd=temp_root,
            timeout=180,
        )
        report["steps"]["create_build_venv"] = create_build_venv
        if create_build_venv["returncode"] != 0:
            report["classification"] = "BLOCKED_BUILD_ENVIRONMENT_CREATION"
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 2

        if os.name == "nt":
            build_python = build_venv / "Scripts" / "python.exe"
        else:
            build_python = build_venv / "bin" / "python"

        install_build_requirements = run(
            [
                str(build_python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "setuptools>=68",
            ],
            cwd=temp_root,
            timeout=300,
        )
        report["steps"]["install_build_requirements"] = install_build_requirements
        if install_build_requirements["returncode"] != 0:
            report["classification"] = "BLOCKED_BUILD_REQUIREMENTS_INSTALL"
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 2

        build_code = (
            "from pathlib import Path;"
            "from setuptools.build_meta import build_sdist,build_wheel;"
            "d=str(Path(r'" + str(dist).replace("\\", "\\\\") + "'));"
            "build_wheel(d);"
            "build_sdist(d)"
        )
        build = run([str(build_python), "-c", build_code], cwd=source, timeout=300)
        report["steps"]["build"] = build
        if build["returncode"] != 0:
            report["classification"] = "BLOCKED_ARTIFACT_BUILD"
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 2

        wheels = sorted(dist.glob("*.whl"))
        sdists = sorted(dist.glob("*.tar.gz"))
        if len(wheels) != 1 or len(sdists) != 1:
            report["classification"] = "BLOCKED_ARTIFACT_SET"
            report["artifacts_observed"] = sorted(path.name for path in dist.iterdir())
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 2

        wheel, sdist = wheels[0], sdists[0]
        normalized_version = EXPECTED_VERSION.replace("-", "_")
        if EXPECTED_VERSION not in wheel.name and normalized_version not in wheel.name:
            report["classification"] = "BLOCKED_WHEEL_VERSION_IDENTITY"
            report["wheel_name"] = wheel.name
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 2
        if EXPECTED_VERSION not in sdist.name and normalized_version not in sdist.name:
            report["classification"] = "BLOCKED_SDIST_VERSION_IDENTITY"
            report["sdist_name"] = sdist.name
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 2

        artifacts = {
            "wheel": {
                "name": wheel.name,
                "sha256": sha256_file(wheel),
                "size_bytes": wheel.stat().st_size,
            },
            "sdist": {
                "name": sdist.name,
                "sha256": sha256_file(sdist),
                "size_bytes": sdist.stat().st_size,
            },
        }
        report["artifacts"] = artifacts

        venv_dir = temp_root / "venv"
        create_venv = run([sys.executable, "-m", "venv", str(venv_dir)], timeout=180)
        report["steps"]["create_venv"] = create_venv
        if create_venv["returncode"] != 0:
            report["classification"] = "BLOCKED_CLEAN_ENVIRONMENT_CREATION"
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 2

        if os.name == "nt":
            python_exe = venv_dir / "Scripts" / "python.exe"
        else:
            python_exe = venv_dir / "bin" / "python"

        install = run(
            [
                str(python_exe),
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--disable-pip-version-check",
                str(wheel),
            ],
            cwd=temp_root,
            timeout=300,
        )
        report["steps"]["install_wheel"] = install
        if install["returncode"] != 0:
            report["classification"] = "BLOCKED_WHEEL_INSTALL"
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 2

        smoke_code = (
            "import json,subprocess,sys;"
            "import arkx;"
            "p=subprocess.run([sys.executable,'-m','arkx','doctor'],capture_output=True,text=True);"
            "print(json.dumps({'version':arkx.__version__,'doctor_returncode':p.returncode,"
            "'doctor_stdout':p.stdout,'doctor_stderr':p.stderr},sort_keys=True))"
        )
        smoke = run([str(python_exe), "-c", smoke_code], cwd=temp_root)
        report["steps"]["clean_install_smoke"] = smoke
        if smoke["returncode"] != 0:
            report["classification"] = "BLOCKED_CLEAN_INSTALL_SMOKE"
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 2
        try:
            smoke_payload = json.loads(smoke["stdout"].strip())
        except json.JSONDecodeError:
            report["classification"] = "BLOCKED_CLEAN_INSTALL_SMOKE_PARSE"
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 2

        report["clean_install"] = smoke_payload
        if (
            smoke_payload.get("version") != EXPECTED_VERSION
            or smoke_payload.get("doctor_returncode") != 0
            or "status: PASS" not in smoke_payload.get("doctor_stdout", "")
        ):
            report["classification"] = "BLOCKED_CLEAN_INSTALL_CONTRACT"
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 2

    status_after = run(["git", "status", "--porcelain=v1", "--untracked-files=no"])
    untracked_after = run(["git", "ls-files", "--others", "--exclude-standard"])
    report["steps"]["status_after"] = status_after
    report["steps"]["untracked_after"] = untracked_after
    if status_after["returncode"] != 0 or status_after["stdout"].strip():
        report["classification"] = "BLOCKED_TRACKED_WORKTREE_MUTATED_BY_VALIDATION"
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    if untracked_after["returncode"] != 0:
        report["classification"] = "BLOCKED_UNTRACKED_STATE_UNAVAILABLE_AFTER_VALIDATION"
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    if untracked_after["stdout"] != untracked_before["stdout"]:
        report["classification"] = "BLOCKED_UNTRACKED_WORKTREE_MUTATED_BY_VALIDATION"
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    report["classification"] = "DISTRIBUTION_ARTIFACTS_VALIDATED"
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
