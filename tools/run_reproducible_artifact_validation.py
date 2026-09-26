#!/usr/bin/env python3
"""Validate reproducible local distribution artifacts without publication."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tarfile
import tempfile
from typing import Any


ROOT = Path(__file__).parents[1].resolve()
EXPECTED_VERSION = "0.3.0.dev1"
BUILD_REQUIREMENT = "setuptools>=68"


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


def artifact_record(path: Path) -> dict[str, Any]:
    return {
        "name": path.name,
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
    }


def extract_archive(archive_bytes: bytes, destination: Path) -> None:
    destination.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:") as bundle:
        bundle.extractall(destination, filter="fully_trusted")


def sdist_logical_manifest(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with tarfile.open(path, mode="r:gz") as bundle:
        for member in sorted(bundle.getmembers(), key=lambda item: item.name):
            record: dict[str, Any] = {
                "name": member.name,
                "type": member.type.decode("ascii", errors="replace")
                if isinstance(member.type, bytes)
                else str(member.type),
                "mode": member.mode,
                "linkname": member.linkname,
                "size": member.size,
            }
            if member.isfile():
                extracted = bundle.extractfile(member)
                if extracted is None:
                    raise RuntimeError(f"unable to read sdist member: {member.name}")
                record["sha256"] = hashlib.sha256(extracted.read()).hexdigest()
            records.append(record)
    return records


def canonicalize_sdist(path: Path, epoch: int) -> None:
    with tarfile.open(path, mode="r:gz") as source:
        members = sorted(source.getmembers(), key=lambda item: item.name)
        payloads: dict[str, bytes] = {}
        for member in members:
            if member.isfile():
                extracted = source.extractfile(member)
                if extracted is None:
                    raise RuntimeError(f"unable to read sdist member: {member.name}")
                payloads[member.name] = extracted.read()

        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.PAX_FORMAT) as target:
            for member in members:
                normalized = tarfile.TarInfo(member.name)
                normalized.type = member.type
                normalized.mode = member.mode
                normalized.size = member.size
                normalized.linkname = member.linkname
                normalized.uid = 0
                normalized.gid = 0
                normalized.uname = ""
                normalized.gname = ""
                normalized.mtime = epoch
                normalized.pax_headers = {}
                data = io.BytesIO(payloads[member.name]) if member.isfile() else None
                target.addfile(normalized, data)

    gzip_buffer = io.BytesIO()
    with gzip.GzipFile(
        filename="",
        mode="wb",
        fileobj=gzip_buffer,
        compresslevel=9,
        mtime=epoch,
    ) as compressed:
        compressed.write(tar_buffer.getvalue())
    path.write_bytes(gzip_buffer.getvalue())


def normalize_tree_mtime(root: Path, epoch: int) -> None:
    for path in sorted(root.rglob("*")):
        try:
            os.utime(path, (epoch, epoch))
        except OSError:
            pass
    os.utime(root, (epoch, epoch))


def build_once(
    *,
    build_python: Path,
    archive_bytes: bytes,
    root: Path,
    label: str,
    build_env: dict[str, str],
    source_date_epoch: int,
) -> dict[str, Any]:
    source = root / f"source-{label}"
    dist = root / f"dist-{label}"
    extract_archive(archive_bytes, source)
    dist.mkdir()

    build_code = (
        "import os;"
        "from pathlib import Path;"
        "from setuptools.build_meta import build_sdist,build_wheel;"
        "d=str(Path(r'" + str(dist).replace("\\", "\\\\") + "'));"
        "build_wheel(d);"
        "epoch=int(os.environ['SOURCE_DATE_EPOCH']);"
        "paths=[Path('.')]+sorted(Path('.').rglob('*'));"
        "[(os.utime(p,(epoch,epoch)) if p.exists() else None) for p in paths];"
        "build_sdist(d)"
    )
    observation = run(
        [str(build_python), "-c", build_code],
        cwd=source,
        env=build_env,
        timeout=300,
    )
    result: dict[str, Any] = {"observation": observation}
    if observation["returncode"] != 0:
        return result

    wheels = sorted(dist.glob("*.whl"))
    sdists = sorted(dist.glob("*.tar.gz"))
    result["artifact_names"] = sorted(path.name for path in dist.iterdir())
    if len(wheels) != 1 or len(sdists) != 1:
        return result

    result["wheel"] = artifact_record(wheels[0])
    result["raw_sdist"] = artifact_record(sdists[0])
    result["sdist_logical_manifest"] = sdist_logical_manifest(sdists[0])
    canonicalize_sdist(sdists[0], source_date_epoch)
    result["sdist"] = artifact_record(sdists[0])
    return result


def main() -> int:
    report: dict[str, Any] = {
        "schema_version": 1,
        "classification": "BLOCKED_REPRODUCIBLE_ARTIFACT_VALIDATION",
        "release_baseline": "v0.3.0.dev0",
        "release": "UNCHANGED",
        "package_index_publication": "NOT_AUTHORIZED",
        "release_asset_upload": "NOT_AUTHORIZED",
        "activation": "NOT_AUTHORIZED",
        "executor_promotion": "NOT_AUTHORIZED",
        "provider_called": False,
        "model_called": False,
        "expected_version": EXPECTED_VERSION,
        "steps": {},
    }

    head = run(["git", "rev-parse", "HEAD"])
    commit_epoch = run(["git", "show", "-s", "--format=%ct", "HEAD"])
    status_before = run(["git", "status", "--porcelain=v1", "--untracked-files=no"])
    untracked_before = run(["git", "ls-files", "--others", "--exclude-standard"])
    report["steps"]["head"] = head
    report["steps"]["commit_epoch"] = commit_epoch
    report["steps"]["status_before"] = status_before
    report["steps"]["untracked_before"] = untracked_before
    if (
        head["returncode"] != 0
        or commit_epoch["returncode"] != 0
        or status_before["returncode"] != 0
        or untracked_before["returncode"] != 0
        or status_before["stdout"].strip()
    ):
        report["classification"] = "BLOCKED_SOURCE_IDENTITY_OR_TRACKED_WORKTREE_CHANGE"
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    source_revision = head["stdout"].strip()
    source_date_epoch = commit_epoch["stdout"].strip()
    if not source_revision or not source_date_epoch.isdigit():
        report["classification"] = "BLOCKED_SOURCE_IDENTITY"
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

    with tempfile.TemporaryDirectory(prefix="codepro-repro-") as tmp:
        temp_root = Path(tmp)
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

        build_python = (
            build_venv / "Scripts" / "python.exe"
            if os.name == "nt"
            else build_venv / "bin" / "python"
        )
        install_backend = run(
            [
                str(build_python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                BUILD_REQUIREMENT,
            ],
            cwd=temp_root,
            timeout=300,
        )
        report["steps"]["install_build_backend"] = install_backend
        if install_backend["returncode"] != 0:
            report["classification"] = "BLOCKED_BUILD_REQUIREMENTS_INSTALL"
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 2

        backend_version = run(
            [str(build_python), "-c", "import setuptools;print(setuptools.__version__)"],
            cwd=temp_root,
        )
        report["steps"]["backend_version"] = backend_version
        if backend_version["returncode"] != 0 or not backend_version["stdout"].strip():
            report["classification"] = "BLOCKED_BUILD_BACKEND_IDENTITY"
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 2

        build_env = os.environ.copy()
        build_env["SOURCE_DATE_EPOCH"] = source_date_epoch
        build_env["PYTHONHASHSEED"] = "0"
        build_env["TZ"] = "UTC"
        build_env["SETUPTOOLS_SCM_PRETEND_VERSION"] = EXPECTED_VERSION

        first = build_once(
            build_python=build_python,
            archive_bytes=archive["stdout"],
            root=temp_root,
            label="a",
            build_env=build_env,
            source_date_epoch=int(source_date_epoch),
        )
        second = build_once(
            build_python=build_python,
            archive_bytes=archive["stdout"],
            root=temp_root,
            label="b",
            build_env=build_env,
            source_date_epoch=int(source_date_epoch),
        )
        report["steps"]["build_a"] = first
        report["steps"]["build_b"] = second

        for label, built in (("a", first), ("b", second)):
            if built["observation"]["returncode"] != 0:
                report["classification"] = f"BLOCKED_ARTIFACT_BUILD_{label.upper()}"
                print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
                return 2
            if "wheel" not in built or "sdist" not in built:
                report["classification"] = f"BLOCKED_ARTIFACT_SET_{label.upper()}"
                print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
                return 2

        reproducible = {
            "wheel": first["wheel"] == second["wheel"],
            "sdist_logical_content": (
                first["sdist_logical_manifest"] == second["sdist_logical_manifest"]
            ),
            "sdist": first["sdist"] == second["sdist"],
        }
        report["reproducibility"] = reproducible
        report["manifest"] = {
            "schema_version": 1,
            "source_revision": source_revision,
            "source_date_epoch": source_date_epoch,
            "python_version": platform.python_version(),
            "build_backend": "setuptools.build_meta",
            "build_backend_version": backend_version["stdout"].strip(),
            "artifacts": {
                "wheel": first["wheel"],
                "sdist": first["sdist"],
            },
        }
        manifest_canonical = json.dumps(
            report["manifest"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        report["manifest_sha256"] = hashlib.sha256(
            manifest_canonical.encode("utf-8")
        ).hexdigest()

        if (
            not reproducible["wheel"]
            or not reproducible["sdist_logical_content"]
            or not reproducible["sdist"]
        ):
            report["classification"] = "BLOCKED_ARTIFACTS_NOT_REPRODUCIBLE"
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
    if (
        untracked_after["returncode"] != 0
        or untracked_after["stdout"] != untracked_before["stdout"]
    ):
        report["classification"] = "BLOCKED_UNTRACKED_WORKTREE_MUTATED_BY_VALIDATION"
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    report["classification"] = "REPRODUCIBLE_ARTIFACTS_VALIDATED"
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
