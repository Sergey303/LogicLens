#!/usr/bin/env python3
from __future__ import annotations

import os
import socket
import sys
import unittest
from pathlib import Path
from unittest import mock

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.zero_epoch.processes import RunFailure, executable_command
from tools.zero_epoch.verification import (
    require_port_not_listening,
    validate_loopback_url,
)


class ExecutableCommandTests(unittest.TestCase):
    def test_direct_executable_stays_shell_free(self) -> None:
        self.assertEqual(
            ["/usr/bin/npm", "ci"],
            executable_command("/usr/bin/npm", "ci", windows=False),
        )

    def test_windows_cmd_uses_command_processor_without_shell_true(self) -> None:
        with mock.patch.dict(os.environ, {"COMSPEC": "C:\\Windows\\cmd.exe"}):
            self.assertEqual(
                [
                    "C:\\Windows\\cmd.exe",
                    "/d",
                    "/s",
                    "/c",
                    "C:\\Program Files\\nodejs\\npm.cmd",
                    "run",
                    "dev",
                ],
                executable_command(
                    "C:\\Program Files\\nodejs\\npm.cmd",
                    "run",
                    "dev",
                    windows=True,
                ),
            )


class LoopbackValidationTests(unittest.TestCase):
    def test_accepts_explicit_loopback_port(self) -> None:
        parsed = validate_loopback_url("http://127.0.0.1:5080", "API URL")
        self.assertEqual("127.0.0.1", parsed.hostname)
        self.assertEqual(5080, parsed.port)

    def test_rejects_non_loopback_origin(self) -> None:
        with self.assertRaises(RunFailure):
            validate_loopback_url("http://0.0.0.0:5080", "API URL")

    def test_rejects_path_on_origin(self) -> None:
        with self.assertRaises(RunFailure):
            validate_loopback_url("http://127.0.0.1:5080/api", "API URL")

    def test_detects_existing_listener(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            port = listener.getsockname()[1]
            parsed = validate_loopback_url(
                f"http://127.0.0.1:{port}",
                "API URL",
            )
            with self.assertRaises(RunFailure):
                require_port_not_listening(parsed, "API URL")


if __name__ == "__main__":
    unittest.main()
