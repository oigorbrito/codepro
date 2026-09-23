"""Git Bash environment for the P8.2a Windows runner-v3 preflight."""

from __future__ import annotations

import os
import subprocess
from typing import Any

try:
    from minisweagent.environments.local import LocalEnvironment, LocalEnvironmentConfig
    MINISWEAGENT_AVAILABLE = True
except ModuleNotFoundError:  # dependency boundary; execution remains unavailable
    MINISWEAGENT_AVAILABLE = False

    class LocalEnvironmentConfig:  # type: ignore[no-redef]
        pass

    class LocalEnvironment:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            raise RuntimeError("minisweagent is required for BashLocalEnvironment execution")


class BashLocalEnvironmentConfig(LocalEnvironmentConfig):
    bash_executable: str


class BashLocalEnvironment(LocalEnvironment):
    """Execute mini-SWE-agent bash actions through an explicit Git Bash binary."""

    def __init__(self, *, config_class: type = BashLocalEnvironmentConfig, **kwargs):
        if not MINISWEAGENT_AVAILABLE:
            raise RuntimeError("minisweagent is required for BashLocalEnvironment execution")
        super().__init__(config_class=config_class, **kwargs)

    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict[str, Any]:
        command = action.get("command", "")
        cwd = cwd or self.config.cwd or os.getcwd()
        bash_executable = self.config.bash_executable
        try:
            result = subprocess.run(
                [bash_executable, "-lc", command],
                cwd=cwd,
                env=os.environ | self.config.env,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=timeout or self.config.timeout,
                check=False,
            )
            output = {"output": result.stdout, "returncode": result.returncode, "exception_info": ""}
        except Exception as error:
            raw_output = getattr(error, "output", None)
            raw_output = raw_output.decode("utf-8", errors="replace") if isinstance(raw_output, bytes) else (raw_output or "")
            output = {
                "output": raw_output,
                "returncode": -1,
                "exception_info": f"An error occurred while executing the command: {error}",
                "extra": {"exception_type": type(error).__name__, "exception": str(error)},
            }
        self._check_finished(output)
        return output
