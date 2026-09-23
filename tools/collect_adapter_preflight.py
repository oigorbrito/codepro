"""Read-only runtime preflight collector for concrete external boundaries."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
from typing import Iterable

from arkx.integration import AdapterIdentity, AdapterPreflight, DependencyObservation, IntegrationKind, assess_preflight


def _version(executable: str) -> str | None:
    try:
        result = subprocess.run([executable, "--version"], capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    output = (result.stdout or result.stderr).strip().replace("\x00", " ")
    return output or None


def _docker_daemon() -> DependencyObservation:
    if not shutil.which("docker"):
        return DependencyObservation("docker-daemon", False, reason="docker executable missing")
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=15, check=False)
    except (OSError, subprocess.SubprocessError) as error:
        return DependencyObservation("docker-daemon", None, reason=f"diagnostic error: {type(error).__name__}")
    if result.returncode == 0:
        return DependencyObservation("docker-daemon", True, _version("docker"))
    return DependencyObservation("docker-daemon", False, reason=(result.stderr or result.stdout).strip()[:240])


def collect_preflights() -> tuple[AdapterPreflight, ...]:
    minisweagent = importlib.util.find_spec("minisweagent") is not None
    docker = shutil.which("docker")
    bash = shutil.which("bash")
    ollama = shutil.which("ollama")
    records: list[AdapterPreflight] = []
    records.append(assess_preflight(
        AdapterIdentity(IntegrationKind.PROVIDER, "openrouter", os.getenv("ARKX_MINISWEAGENT_VERSION"), os.getenv("ARKX_OPENROUTER_CONFIG_DIGEST")),
        (DependencyObservation("minisweagent", minisweagent, reason=None if minisweagent else "python module unavailable"),),
        capabilities=("completion",),
    ))
    records.append(assess_preflight(
        AdapterIdentity(IntegrationKind.SANDBOX, "git-bash", os.getenv("ARKX_GIT_BASH_VERSION"), os.getenv("ARKX_GIT_BASH_CONFIG_DIGEST")),
        (DependencyObservation("bash", bool(bash and _version(bash)), _version(bash) if bash else None, None if bash and _version(bash) else "executable unavailable or access denied"),),
        capabilities=("command-execution",),
    ))
    records.append(assess_preflight(
        AdapterIdentity(IntegrationKind.EVALUATOR, "docker-swebench", _version("docker") if docker else None, os.getenv("ARKX_DOCKER_CONFIG_DIGEST")),
        (_docker_daemon(),),
        capabilities=("container-evaluation",),
    ))
    records.append(assess_preflight(
        AdapterIdentity(IntegrationKind.PROVIDER, "ollama", _version("ollama") if ollama else None, os.getenv("ARKX_OLLAMA_CONFIG_DIGEST")),
        (DependencyObservation("ollama", ollama is not None, _version(ollama) if ollama else None, None if ollama else "executable unavailable"),),
        capabilities=("completion",),
    ))
    return tuple(records)


def main() -> int:
    import json
    print(json.dumps([record.to_dict() | {"reference": record.reference} for record in collect_preflights()], ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
