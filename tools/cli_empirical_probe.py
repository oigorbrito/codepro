"""Empirical CLI baseline probe for Arkx.

The probe records actual process behavior without assuming that a CLI exists.
It exits successfully when the observations themselves are collected.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Sequence


ROOT = Path(__file__).parents[1]


def run(name: str, command: Sequence[str], *, env: dict[str, str] | None = None) -> dict:
    completed = subprocess.run(
        list(command),
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    return {
        "name": name,
        "command": list(command),
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main() -> int:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")

    observations = [
        run(
            "import_arkx",
            [sys.executable, "-c", "import arkx; print(arkx.__file__)"],
            env=env,
        ),
        run("module_root", [sys.executable, "-m", "arkx"], env=env),
        run("module_help", [sys.executable, "-m", "arkx", "--help"], env=env),
        run("module_version", [sys.executable, "-m", "arkx", "--version"], env=env),
        run("baseline_module", [sys.executable, "-m", "arkx.baseline"], env=env),
        run(
            "editable_install",
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-input",
                "--no-deps",
                "-e",
                ".",
            ],
        ),
    ]

    metadata = {
        "python": sys.version,
        "platform": sys.platform,
        "cwd": str(ROOT),
        "console_command_found": shutil.which("arkx"),
        "packaging_files": {
            name: (ROOT / name).exists()
            for name in ("pyproject.toml", "setup.py", "setup.cfg")
        },
        "module_main_exists": (ROOT / "src" / "arkx" / "__main__.py").exists(),
        "cli_module_exists": (ROOT / "src" / "arkx" / "cli.py").exists(),
    }

    result = {"metadata": metadata, "observations": observations}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))

    import_ok = observations[0]["exit_code"] == 0
    baseline_ok = observations[4]["exit_code"] == 0
    root_cli_ok = observations[1]["exit_code"] == 0
    help_ok = observations[2]["exit_code"] == 0
    version_ok = observations[3]["exit_code"] == 0
    install_ok = observations[5]["exit_code"] == 0

    summary = {
        "package_importable": import_ok,
        "baseline_module_runnable": baseline_ok,
        "python_m_arkx_runnable": root_cli_ok,
        "help_runnable": help_ok,
        "version_runnable": version_ok,
        "editable_installable": install_ok,
        "console_command_available": metadata["console_command_found"] is not None,
    }
    print("CLI_EMPIRICAL_SUMMARY " + json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
