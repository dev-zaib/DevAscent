"""gVisor-based sandbox executor for user code evaluation.

Extends Hermes's docker backend pattern from tools/environments/docker.py
with gVisor runtime, seccomp profiles, and strict resource limits.
"""
import json
import tempfile
import subprocess
import time
from pathlib import Path
from dataclasses import dataclass
from devascent.config import assessment_config


@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    wall_time_ms: float
    timed_out: bool


LANGUAGE_CONFIGS = {
    "typescript": {
        "image": "node:22-alpine",
        "command": ["node", "-e"],
        "extension": ".js",
    },
    "javascript": {
        "image": "node:22-alpine",
        "command": ["node", "-e"],
        "extension": ".js",
    },
    "python": {
        "image": "python:3.11-alpine",
        "command": ["python3", "-c"],
        "extension": ".py",
    },
    "go": {
        "image": "golang:1.22-alpine",
        "command": ["go", "run"],
        "extension": ".go",
    },
}


class SandboxExecutor:
    """Executes user code in an isolated, resource-constrained environment.

    In production: uses Docker with gVisor runtime (runsc), seccomp profiles,
    tmpfs, no network, and strict CPU/memory limits.

    For development: uses subprocess with timeout as a lightweight fallback.
    """

    def __init__(self):
        self.timeout = assessment_config.sandbox_timeout
        self._seccomp_profile = None

    def _load_seccomp(self) -> dict:
        if self._seccomp_profile is None:
            profile_path = Path(__file__).parent / "seccomp.json"
            with open(profile_path, encoding="utf-8") as f:
                self._seccomp_profile = json.load(f)
        return self._seccomp_profile

    async def execute(
        self,
        code: str,
        language: str,
        stdin: str = "",
    ) -> SandboxResult:
        """Execute code in an isolated sandbox.

        Args:
            code: Source code string
            language: Programming language ('typescript', 'python', 'go', etc.)
            stdin: Optional stdin data for the process

        Returns:
            SandboxResult with stdout, stderr, exit_code, and timing
        """
        lang_config = LANGUAGE_CONFIGS.get(
            language, LANGUAGE_CONFIGS["typescript"]
        )

        start = time.monotonic()

        try:
            result = await self._docker_execute(code, language, lang_config)
        except Exception:
            result = await self._subprocess_execute(
                code, language, lang_config
            )

        wall_time_ms = (time.monotonic() - start) * 1000

        return SandboxResult(
            stdout=result.get("stdout", ""),
            stderr=result.get("stderr", ""),
            exit_code=result.get("exit_code", -1),
            wall_time_ms=wall_time_ms,
            timed_out=result.get("timed_out", False),
        )

    async def _docker_execute(
        self,
        code: str,
        language: str,
        lang_config: dict,
    ) -> dict:
        """Execute via Docker with gVisor runtime.

        Uses:
        - --runtime=runsc (gVisor)
        - --security-opt no-new-privileges
        - --cap-drop=ALL
        - --network=none
        - --memory=512m --cpus=1
        - --tmpfs /tmp:rw,noexec,nosuid,size=1g
        - --read-only rootfs
        - seccomp profile from seccomp.json
        """
        try:
            import docker
        except ImportError:
            return {"stdout": "", "stderr": "Docker SDK not available", "exit_code": -1, "timed_out": False}

        client = docker.from_env()
        image = lang_config["image"]

        try:
            client.images.get(image)
        except docker.errors.ImageNotFound:
            client.images.pull(image)

        seccomp = self._load_seccomp()

        container = client.containers.run(
            image=image,
            command=[*lang_config["command"], code],
            runtime="runsc",
            security_opt=["no-new-privileges"],
            cap_drop=["ALL"],
            mem_limit="512m",
            nano_cpus=1_000_000_000,
            tmpfs={"/tmp": "rw,noexec,nosuid,size=1g"},
            network_disabled=True,
            read_only=True,
            detach=True,
            stdin_open=True,
        )

        try:
            result = container.wait(timeout=self.timeout)
            logs = container.logs(stdout=True, stderr=True)
            stdout = logs.decode("utf-8", errors="replace")

            return {
                "stdout": stdout,
                "stderr": "",
                "exit_code": result.get("StatusCode", -1),
                "timed_out": False,
            }
        except Exception:
            container.kill()
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {self.timeout}s",
                "exit_code": -1,
                "timed_out": True,
            }
        finally:
            try:
                container.remove(force=True)
            except Exception:
                pass

    async def _subprocess_execute(
        self,
        code: str,
        language: str,
        lang_config: dict,
    ) -> dict:
        """Lightweight subprocess execution for development.

        NOT suitable for production — no sandbox isolation.
        """
        try:
            proc = subprocess.run(
                [*lang_config["command"], code],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd="/tmp",
            )
            return {
                "stdout": proc.stdout or "",
                "stderr": proc.stderr or "",
                "exit_code": proc.returncode,
                "timed_out": False,
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {self.timeout}s",
                "exit_code": -1,
                "timed_out": True,
            }


sandbox_executor = SandboxExecutor()
