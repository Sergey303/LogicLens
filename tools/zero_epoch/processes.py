from __future__ import annotations

import os
import shutil
import signal
import subprocess
import time
from pathlib import Path
from typing import Mapping, Sequence


class RunFailure(RuntimeError):
    """Raised when preparation or a managed service fails."""


def require_executable(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise RunFailure(f"Required executable is unavailable: {name}")
    return path


def run_checked(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str] | None = None,
) -> None:
    printable = " ".join(command)
    print(f"> {printable}")
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        env=None if env is None else dict(env),
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RunFailure(
            f"Command failed with exit code {completed.returncode}: {printable}"
        )


class ManagedProcess:
    def __init__(
        self,
        name: str,
        command: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        log_path: Path,
    ) -> None:
        self.name = name
        self.command = list(command)
        self.cwd = cwd
        self.env = dict(env)
        self.log_path = log_path
        self._stream = None
        self.process: subprocess.Popen[str] | None = None

    def start(self) -> None:
        if self.process is not None:
            raise RunFailure(f"Process is already started: {self.name}")

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._stream = self.log_path.open("w", encoding="utf-8", buffering=1)
        kwargs: dict[str, object] = {}
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True

        print(f"Starting {self.name}; log: {self.log_path}")
        self.process = subprocess.Popen(
            self.command,
            cwd=self.cwd,
            env=self.env,
            text=True,
            stdout=self._stream,
            stderr=subprocess.STDOUT,
            **kwargs,
        )

    def require_running(self) -> None:
        process = self._required_process()
        return_code = process.poll()
        if return_code is not None:
            raise RunFailure(
                f"{self.name} exited with code {return_code}.\n"
                f"Last log lines:\n{self.tail()}"
            )

    def stop(self) -> None:
        process = self.process
        if process is None:
            self._close_stream()
            return

        if process.poll() is None:
            self._terminate_tree(process)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._kill_tree(process)
                process.wait(timeout=10)

        self._close_stream()

    def tail(self, lines: int = 40) -> str:
        if self._stream is not None:
            self._stream.flush()
        if not self.log_path.is_file():
            return "<log is unavailable>"
        content = self.log_path.read_text(encoding="utf-8", errors="replace")
        return "\n".join(content.splitlines()[-lines:])

    def _required_process(self) -> subprocess.Popen[str]:
        if self.process is None:
            raise RunFailure(f"Process is not started: {self.name}")
        return self.process

    def _close_stream(self) -> None:
        if self._stream is not None:
            self._stream.flush()
            self._stream.close()
            self._stream = None

    @staticmethod
    def _terminate_tree(process: subprocess.Popen[str]) -> None:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            return
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return

    @staticmethod
    def _kill_tree(process: subprocess.Popen[str]) -> None:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            return
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return


def stop_all(processes: Sequence[ManagedProcess]) -> None:
    for process in reversed(processes):
        try:
            process.stop()
        except (OSError, subprocess.SubprocessError) as exc:
            print(f"Failed to stop {process.name}: {exc}")
    time.sleep(0.05)
