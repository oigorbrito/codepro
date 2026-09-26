#!/usr/bin/env python3
"""Validate the complete local supply-chain baseline without publication."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from typing import Any

import run_reproducible_artifact_validation as repro


ROOT = Path(__file__).parents[1].resolve()
EXPECTED_VERSION = "0.3.0.dev1"
REPO_URI = "https://github.com/oigorbrito/codepro"


def canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return repro.sha256_file(path)


def spdx_sbom(
    *,
    source_revision: str,
    source_epoch: int,
    wheel: dict[str, Any],
    sdist: dict[str, Any],
) -> dict[str, Any]:
    created = datetime.fromtimestamp(source_epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    namespace = f"https://codepro.local/spdx/codepro-{EXPECTED_VERSION}-{source_revision}"
    packages = []
    relationships = []
    for kind, artifact in (("wheel", wheel), ("sdist", sdist)):
        spdx_id = f"SPDXRef-Package-codepro-{kind}"
        packages.append(
            {
                "SPDXID": spdx_id,
                "name": "codepro",
                "versionInfo": EXPECTED_VERSION,
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "checksums": [
                    {
                        "algorithm": "SHA256",
                        "checksumValue": artifact["sha256"],
                    }
                ],
                "comment": f"Local reproducible {kind} artifact: {artifact['name']}",
            }
        )
        relationships.append(
            {
                "spdxElementId": "SPDXRef-DOCUMENT",
                "relationshipType": "DESCRIBES",
                "relatedSpdxElement": spdx_id,
            }
        )
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"codepro-{EXPECTED_VERSION}-local-build-sbom",
        "documentNamespace": namespace,
        "creationInfo": {
            "created": created,
            "creators": ["Tool: codepro-local-supply-chain"],
            "comment": "Build-context SBOM generated from locally reproduced artifacts.",
        },
        "packages": packages,
        "relationships": relationships,
    }


def provenance_statement(
    *,
    source_revision: str,
    source_epoch: int,
    backend_version: str,
    wheel: dict[str, Any],
    sdist: dict[str, Any],
    sbom_sha256: str,
) -> dict[str, Any]:
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [
            {"name": wheel["name"], "digest": {"sha256": wheel["sha256"]}},
            {"name": sdist["name"], "digest": {"sha256": sdist["sha256"]}},
        ],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": f"{REPO_URI}#local-reproducible-python-package-v1",
                "externalParameters": {
                    "sourceRevision": source_revision,
                    "expectedVersion": EXPECTED_VERSION,
                },
                "internalParameters": {
                    "sourceDateEpoch": str(source_epoch),
                    "pythonVersion": platform.python_version(),
                    "buildBackend": "setuptools.build_meta",
                    "buildBackendVersion": backend_version,
                    "pythonHashSeed": "0",
                    "timezone": "UTC",
                },
                "resolvedDependencies": [
                    {
                        "uri": f"git+{REPO_URI}",
                        "digest": {"gitCommit": source_revision},
                    }
                ],
            },
            "runDetails": {
                "builder": {
                    "id": f"{REPO_URI}/blob/{source_revision}/tools/run_local_supply_chain_validation.py",
                    "version": {"codepro": source_revision},
                },
                "byproducts": [
                    {
                        "name": "codepro.spdx.json",
                        "digest": {"sha256": sbom_sha256},
                        "mediaType": "application/spdx+json",
                    }
                ],
            },
        },
    }


def verify_bundle(
    *,
    source_revision: str,
    wheel_path: Path,
    sdist_path: Path,
    sbom: dict[str, Any],
    provenance: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    actual = {
        wheel_path.name: sha256_file(wheel_path),
        sdist_path.name: sha256_file(sdist_path),
    }

    package_hashes: dict[str, str] = {}
    for package in sbom.get("packages", []):
        checksums = package.get("checksums", [])
        sha = next(
            (
                item.get("checksumValue")
                for item in checksums
                if item.get("algorithm") == "SHA256"
            ),
            None,
        )
        comment = package.get("comment", "")
        matched_name = next((name for name in actual if name in comment), None)
        if matched_name and sha:
            package_hashes[matched_name] = sha

    if package_hashes != actual:
        failures.append("SBOM_ARTIFACT_HASH_MISMATCH")

    subjects = {
        item.get("name"): item.get("digest", {}).get("sha256")
        for item in provenance.get("subject", [])
    }
    if subjects != actual:
        failures.append("PROVENANCE_SUBJECT_HASH_MISMATCH")

    resolved = (
        provenance.get("predicate", {})
        .get("buildDefinition", {})
        .get("resolvedDependencies", [])
    )
    git_commits = {
        item.get("digest", {}).get("gitCommit")
        for item in resolved
        if item.get("digest", {}).get("gitCommit")
    }
    if source_revision not in git_commits:
        failures.append("PROVENANCE_SOURCE_REVISION_MISMATCH")

    expected_sbom_hash = sha256_bytes(canonical_json(sbom).encode("utf-8"))
    byproducts = (
        provenance.get("predicate", {})
        .get("runDetails", {})
        .get("byproducts", [])
    )
    sbom_hashes = {
        item.get("digest", {}).get("sha256")
        for item in byproducts
        if item.get("name") == "codepro.spdx.json"
    }
    if expected_sbom_hash not in sbom_hashes:
        failures.append("PROVENANCE_SBOM_HASH_MISMATCH")

    if sbom.get("spdxVersion") != "SPDX-2.3":
        failures.append("SBOM_SCHEMA_IDENTITY_MISMATCH")
    if provenance.get("_type") != "https://in-toto.io/Statement/v1":
        failures.append("PROVENANCE_STATEMENT_TYPE_MISMATCH")
    if provenance.get("predicateType") != "https://slsa.dev/provenance/v1":
        failures.append("PROVENANCE_PREDICATE_TYPE_MISMATCH")

    return failures


def main() -> int:
    report: dict[str, Any] = {
        "schema_version": 1,
        "classification": "BLOCKED_LOCAL_SUPPLY_CHAIN_BASELINE",
        "release_baseline": "v0.3.0.dev0",
        "release": "UNCHANGED",
        "package_index_publication": "NOT_AUTHORIZED",
        "release_asset_upload": "NOT_AUTHORIZED",
        "activation": "NOT_AUTHORIZED",
        "executor_promotion": "NOT_AUTHORIZED",
        "cryptographic_signing": "NOT_PERFORMED",
        "hosted_attestation": "NOT_PERFORMED",
        "provider_called": False,
        "model_called": False,
        "steps": {},
    }

    head = repro.run(["git", "rev-parse", "HEAD"])
    epoch_result = repro.run(["git", "show", "-s", "--format=%ct", "HEAD"])
    tracked = repro.run(["git", "status", "--porcelain=v1", "--untracked-files=no"])
    untracked_before = repro.run(["git", "ls-files", "--others", "--exclude-standard"])
    report["steps"]["head"] = head
    report["steps"]["commit_epoch"] = epoch_result
    report["steps"]["tracked_status_before"] = tracked
    report["steps"]["untracked_before"] = untracked_before
    if (
        head["returncode"] != 0
        or epoch_result["returncode"] != 0
        or tracked["returncode"] != 0
        or untracked_before["returncode"] != 0
        or tracked["stdout"].strip()
    ):
        report["classification"] = "BLOCKED_SOURCE_IDENTITY_OR_TRACKED_WORKTREE_CHANGE"
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    source_revision = head["stdout"].strip()
    source_epoch_text = epoch_result["stdout"].strip()
    if not source_revision or not source_epoch_text.isdigit():
        report["classification"] = "BLOCKED_SOURCE_IDENTITY"
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    source_epoch = int(source_epoch_text)

    archive = repro.run(["git", "archive", "--format=tar", "HEAD"], text=False)
    report["steps"]["git_archive"] = {
        "returncode": archive["returncode"],
        "timeout": archive["timeout"],
        "error": archive["error"],
        "stderr": (
            archive["stderr"].decode("utf-8", errors="replace")
            if isinstance(archive["stderr"], bytes)
            else archive["stderr"]
        ),
    }
    if archive["returncode"] != 0 or not isinstance(archive["stdout"], bytes):
        report["classification"] = "BLOCKED_GIT_ARCHIVE"
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    with tempfile.TemporaryDirectory(prefix="codepro-supply-chain-") as tmp:
        temp_root = Path(tmp)
        build_venv = temp_root / "build-venv"
        create_build_venv = repro.run(
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
        install_backend = repro.run(
            [
                str(build_python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                repro.BUILD_REQUIREMENT,
            ],
            cwd=temp_root,
            timeout=300,
        )
        report["steps"]["install_build_backend"] = install_backend
        if install_backend["returncode"] != 0:
            report["classification"] = "BLOCKED_BUILD_REQUIREMENTS_INSTALL"
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 2

        backend_version_result = repro.run(
            [str(build_python), "-c", "import setuptools;print(setuptools.__version__)"],
            cwd=temp_root,
        )
        report["steps"]["backend_version"] = backend_version_result
        if backend_version_result["returncode"] != 0:
            report["classification"] = "BLOCKED_BUILD_BACKEND_IDENTITY"
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 2
        backend_version = backend_version_result["stdout"].strip()

        build_env = os.environ.copy()
        build_env["SOURCE_DATE_EPOCH"] = str(source_epoch)
        build_env["PYTHONHASHSEED"] = "0"
        build_env["TZ"] = "UTC"
        build_env["SETUPTOOLS_SCM_PRETEND_VERSION"] = EXPECTED_VERSION

        first = repro.build_once(
            build_python=build_python,
            archive_bytes=archive["stdout"],
            root=temp_root,
            label="a",
            build_env=build_env,
            source_date_epoch=source_epoch,
        )
        second = repro.build_once(
            build_python=build_python,
            archive_bytes=archive["stdout"],
            root=temp_root,
            label="b",
            build_env=build_env,
            source_date_epoch=source_epoch,
        )
        report["reproducibility"] = {
            "wheel": first.get("wheel") == second.get("wheel"),
            "sdist_logical_content": (
                first.get("sdist_logical_manifest")
                == second.get("sdist_logical_manifest")
            ),
            "sdist": first.get("sdist") == second.get("sdist"),
        }
        if not all(report["reproducibility"].values()):
            report["classification"] = "BLOCKED_ARTIFACTS_NOT_REPRODUCIBLE"
            report["artifacts_a"] = {
                "wheel": first.get("wheel"),
                "sdist": first.get("sdist"),
                "raw_sdist": first.get("raw_sdist"),
            }
            report["artifacts_b"] = {
                "wheel": second.get("wheel"),
                "sdist": second.get("sdist"),
                "raw_sdist": second.get("raw_sdist"),
            }
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 2

        wheel = first["wheel"]
        sdist = first["sdist"]
        wheel_path = temp_root / "dist-a" / wheel["name"]
        sdist_path = temp_root / "dist-a" / sdist["name"]

        sbom = spdx_sbom(
            source_revision=source_revision,
            source_epoch=source_epoch,
            wheel=wheel,
            sdist=sdist,
        )
        sbom_text = canonical_json(sbom)
        sbom_sha256 = sha256_bytes(sbom_text.encode("utf-8"))

        provenance = provenance_statement(
            source_revision=source_revision,
            source_epoch=source_epoch,
            backend_version=backend_version,
            wheel=wheel,
            sdist=sdist,
            sbom_sha256=sbom_sha256,
        )
        provenance_text = canonical_json(provenance)
        provenance_sha256 = sha256_bytes(provenance_text.encode("utf-8"))

        bundle_dir = temp_root / "evidence"
        bundle_dir.mkdir()
        (bundle_dir / "codepro.spdx.json").write_text(
            sbom_text + "\n", encoding="utf-8", newline="\n"
        )
        (bundle_dir / "codepro.provenance.json").write_text(
            provenance_text + "\n", encoding="utf-8", newline="\n"
        )

        failures = verify_bundle(
            source_revision=source_revision,
            wheel_path=wheel_path,
            sdist_path=sdist_path,
            sbom=sbom,
            provenance=provenance,
        )
        report["offline_verification"] = {
            "failures": failures,
            "verified": not failures,
        }
        if failures:
            report["classification"] = "BLOCKED_SUPPLY_CHAIN_CONSISTENCY"
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 2

        clean_venv = temp_root / "clean-venv"
        create_clean_venv = repro.run(
            [sys.executable, "-m", "venv", str(clean_venv)],
            cwd=temp_root,
            timeout=180,
        )
        report["steps"]["create_clean_venv"] = create_clean_venv
        if create_clean_venv["returncode"] != 0:
            report["classification"] = "BLOCKED_CLEAN_ENVIRONMENT_CREATION"
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 2

        clean_python = (
            clean_venv / "Scripts" / "python.exe"
            if os.name == "nt"
            else clean_venv / "bin" / "python"
        )
        install_wheel = repro.run(
            [
                str(clean_python),
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--disable-pip-version-check",
                str(wheel_path),
            ],
            cwd=temp_root,
            timeout=300,
        )
        report["steps"]["install_wheel"] = install_wheel
        if install_wheel["returncode"] != 0:
            report["classification"] = "BLOCKED_WHEEL_INSTALL"
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 2

        smoke = repro.run(
            [
                str(clean_python),
                "-c",
                (
                    "import json,subprocess,sys,arkx;"
                    "p=subprocess.run([sys.executable,'-m','arkx','doctor'],"
                    "capture_output=True,text=True);"
                    "print(json.dumps({'version':arkx.__version__,"
                    "'doctor_returncode':p.returncode,'doctor_stdout':p.stdout},"
                    "sort_keys=True))"
                ),
            ],
            cwd=temp_root,
        )
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

        report["artifacts"] = {"wheel": wheel, "sdist": sdist}
        report["sbom"] = {
            "format": "SPDX-2.3",
            "sha256": sbom_sha256,
            "packages": len(sbom["packages"]),
        }
        report["provenance"] = {
            "statement_type": provenance["_type"],
            "predicate_type": provenance["predicateType"],
            "sha256": provenance_sha256,
            "signed": False,
        }
        report["source_revision"] = source_revision
        report["build_backend_version"] = backend_version

    tracked_after = repro.run(["git", "status", "--porcelain=v1", "--untracked-files=no"])
    untracked_after = repro.run(["git", "ls-files", "--others", "--exclude-standard"])
    report["steps"]["tracked_status_after"] = tracked_after
    report["steps"]["untracked_after"] = untracked_after
    if tracked_after["returncode"] != 0 or tracked_after["stdout"].strip():
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

    report["classification"] = "LOCAL_SUPPLY_CHAIN_BASELINE_VALIDATED"
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
