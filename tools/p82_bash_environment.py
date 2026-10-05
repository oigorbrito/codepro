"""Git Bash environment for the P8.2a Windows runner-v3 preflight."""

from __future__ import annotations

import os
import signal
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


class DockerExecEnvironmentConfig(LocalEnvironmentConfig):
    container: str


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
        process = None
        try:
            process = subprocess.Popen(
                [bash_executable, "-lc", command],
                cwd=cwd,
                env=os.environ | self.config.env,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            stdout, _ = process.communicate(timeout=timeout or self.config.timeout)
            output = {"output": stdout, "returncode": process.returncode, "exception_info": ""}
        except subprocess.TimeoutExpired as error:
            if process is not None:
                if os.name == "nt":
                    try:
                        subprocess.run(
                            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            check=False,
                            timeout=5,
                        )
                    except (OSError, subprocess.TimeoutExpired):
                        process.kill()
                    # Descendants can retain the pipe after the shell dies.
                    # Do not wait for EOF on Windows; the timeout boundary is
                    # already authoritative and partial output is sufficient.
                    stdout = error.output or ""
                else:
                    os.killpg(process.pid, signal.SIGKILL)
                    stdout, _ = process.communicate()
            else:
                stdout = error.output or ""
            output = {
                "output": stdout,
                "returncode": -1,
                "exception_info": f"An error occurred while executing the command: {error}",
                "extra": {"exception_type": type(error).__name__, "exception": str(error)},
            }
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


class DockerExecEnvironment(LocalEnvironment):
    """Execute agent actions inside an already-qualified Docker task container."""

    def __init__(self, *, config_class: type = DockerExecEnvironmentConfig, **kwargs):
        super().__init__(config_class=config_class, **kwargs)

    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict[str, Any]:
        command = action.get("command", "")
        container = self.config.container
        cwd = cwd or self.config.cwd or "/testbed"
        process = None
        try:
            process = subprocess.Popen(
                ["docker", "exec", "-w", cwd, container, "bash", "-lc", command],
                text=True, encoding="utf-8", errors="replace",
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            stdout, _ = process.communicate(timeout=timeout or self.config.timeout)
            output = {"output": stdout, "returncode": process.returncode, "exception_info": ""}
        except subprocess.TimeoutExpired as error:
            if process is not None:
                if os.name == "nt":
                    subprocess.run(["docker", "kill", container], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=5)
                    stdout = error.output or ""
                else:
                    os.killpg(process.pid, signal.SIGKILL)
                    stdout, _ = process.communicate()
            else:
                stdout = error.output or ""
            output = {"output": stdout, "returncode": -1, "exception_info": f"An error occurred while executing the command: {error}", "extra": {"exception_type": type(error).__name__, "exception": str(error)}}
        except Exception as error:
            raw_output = getattr(error, "output", None)
            raw_output = raw_output.decode("utf-8", errors="replace") if isinstance(raw_output, bytes) else (raw_output or "")
            output = {"output": raw_output, "returncode": -1, "exception_info": f"An error occurred while executing the command: {error}", "extra": {"exception_type": type(error).__name__, "exception": str(error)}}
        self._check_finished(output)
        return output
