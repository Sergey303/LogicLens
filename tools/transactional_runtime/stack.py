from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.parse
import webbrowser
from pathlib import Path

from build_builder_staged_revision import run_request
from zero_epoch.processes import (
    ManagedProcess,
    RunFailure,
    executable_command,
    require_executable,
    run_checked,
    stop_all,
)
from zero_epoch.verification import (
    require_port_not_listening,
    validate_loopback_url,
    verify_vertical_slice,
    wait_for,
)

from .selection import default_contract_paths, resolve_selected_runtime


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run LogicLens API and web UI against the package selected by "
            "transactional deployment/current.json."
        )
    )
    parser.add_argument("--deployment-root", required=True, type=Path)
    parser.add_argument("--repository-root", type=Path)
    parser.add_argument("--work-directory", type=Path)
    parser.add_argument("--api-url", default="http://127.0.0.1:5080")
    parser.add_argument("--web-url", default="http://127.0.0.1:5173")
    parser.add_argument("--swipl", default="swipl")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = (
        args.repository_root.resolve()
        if args.repository_root is not None
        else find_repository_root()
    )
    require_repository(root)
    pointer_schema, journal_schema, attestation_schema = default_contract_paths(root)
    selected = resolve_selected_runtime(
        deployment_root=args.deployment_root,
        pointer_schema_path=pointer_schema,
        journal_schema_path=journal_schema,
        attestation_schema_path=attestation_schema,
    )

    api_origin = args.api_url.rstrip("/")
    web_origin = args.web_url.rstrip("/")
    api = validate_loopback_url(api_origin, "API URL")
    web = validate_loopback_url(web_origin, "web URL")
    if (api.hostname, api.port) == (web.hostname, web.port):
        raise RunFailure("API URL and web URL must use different loopback ports")
    require_port_not_listening(api, "API URL")
    require_port_not_listening(web, "web URL")

    work = (
        args.work_directory.resolve()
        if args.work_directory is not None
        else root / ".logiclens" / "selected-runtime"
    )
    reset_work_directory(root, selected.deployment_root, work)
    logs = work / "logs"

    dotnet = require_executable("dotnet")
    npm = require_executable("npm")
    swipl = require_executable(args.swipl)
    prepare_application(root, work, dotnet, npm)
    preflight_runtime(swipl, selected.package_root, selected.epoch, selected.revision)

    environment = os.environ.copy()
    environment.update(
        {
            "DOTNET_NOLOGO": "1",
            "ASPNETCORE_ENVIRONMENT": "Production",
            "ASPNETCORE_URLS": api_origin,
            "Prolog__ExecutablePath": swipl,
            "Prolog__EpochPath": str(selected.package_root),
            "Prolog__Epoch": str(selected.epoch),
            "Prolog__Revision": str(selected.revision),
            "UiDocument__SchemaPath": str(
                (root / "contracts" / "ui-document-v0.schema.json").resolve()
            ),
        }
    )
    api_process = ManagedProcess(
        "LogicLens.Api",
        [
            dotnet,
            "run",
            "--project",
            str(root / "src" / "LogicLens.Api" / "LogicLens.Api.csproj"),
            "--configuration",
            "Release",
            "--no-build",
            "--no-launch-profile",
        ],
        cwd=root,
        env=environment,
        log_path=logs / "api.log",
    )

    web_environment = os.environ.copy()
    web_environment.update({"LOGICLENS_API_URL": api_origin, "BROWSER": "none"})
    web_process = ManagedProcess(
        "LogicLens.Web",
        executable_command(
            npm,
            "run",
            "dev",
            "--",
            "--host",
            web.hostname or "127.0.0.1",
            "--port",
            str(web.port),
            "--strictPort",
        ),
        cwd=root / "src" / "LogicLens.Web",
        env=web_environment,
        log_path=logs / "web.log",
    )

    processes = [api_process, web_process]
    try:
        api_process.start()
        wait_for(
            "LogicLens API",
            f"{api_origin}/api/health",
            [api_process],
            lambda status, body, content_type: (
                status == 200
                and content_type == "application/json"
                and b'"kind":"health"' in body
            ),
        )
        web_process.start()
        wait_for(
            "LogicLens web renderer",
            web_origin,
            processes,
            lambda status, body, content_type: (
                status == 200
                and content_type == "text/html"
                and b'<div id="root"></div>' in body
            ),
        )
        verify_vertical_slice(
            api_origin,
            web_origin,
            expected_epoch=selected.epoch,
            expected_revision=selected.revision,
        )
        print("Transactional LogicLens verification passed.")
        print(
            "Selected: "
            f"generation {selected.generation}, "
            f"revision {selected.epoch}.{selected.revision}"
        )
        print(f"Pointer hash: {selected.pointer_hash}")
        print(f"Package: {selected.package_hash}")
        print(f"Web: {web_origin}/entities/urn%3Alogiclens%3Aperson%3Aalex")
        print(f"API health: {api_origin}/api/health")

        if args.verify_only:
            return 0
        if not args.no_browser:
            webbrowser.open(
                f"{web_origin}/entities/urn%3Alogiclens%3Aperson%3Aalex",
                new=2,
            )
        print("Press Ctrl+C to stop LogicLens.Api and LogicLens.Web.")
        while True:
            for process in processes:
                process.require_running()
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Stopping transactional LogicLens runtime.")
        return 0
    finally:
        stop_all(processes)


def preflight_runtime(swipl: str, package: Path, epoch: int, revision: int) -> None:
    request = {
        "protocolVersion": "0.1",
        "requestId": "transactional-launcher-preflight",
        "command": "health",
        "epoch": epoch,
        "revision": revision,
        "options": {},
    }
    code, response, stderr = run_request(swipl, package, request, 30.0)
    if (
        code != 0
        or response.get("status") != "ok"
        or response.get("epoch") != epoch
        or response.get("revision") != revision
    ):
        raise RunFailure(
            "selected runtime preflight failed: "
            + json.dumps(response, ensure_ascii=False, sort_keys=True)
            + (f"; stderr={stderr.strip()}" if stderr.strip() else "")
        )


def prepare_application(root: Path, work: Path, dotnet: str, npm: str) -> None:
    run_checked([dotnet, "restore", "LogicLens.sln"], cwd=root)
    run_checked(
        [
            dotnet,
            "build",
            "LogicLens.sln",
            "--configuration",
            "Release",
            "--no-restore",
        ],
        cwd=root,
    )
    web_root = root / "src" / "LogicLens.Web"
    run_checked(
        executable_command(
            npm,
            "ci",
            "--ignore-scripts",
            "--no-audit",
            "--no-fund",
        ),
        cwd=web_root,
    )
    run_checked(executable_command(npm, "run", "build"), cwd=web_root)
    if not (web_root / "dist" / "index.html").is_file():
        raise RunFailure("production web bundle was not produced")
    (work / "logs").mkdir(parents=True, exist_ok=True)


def reset_work_directory(root: Path, deployment: Path, work: Path) -> None:
    if work == root or work in root.parents:
        raise RunFailure(f"unsafe work directory: {work}")
    if work == deployment or deployment in work.parents or work in deployment.parents:
        raise RunFailure("work directory and deployment root must be separate")
    if work.exists():
        if not work.is_dir():
            raise RunFailure(f"work path exists and is not a directory: {work}")
        shutil.rmtree(work)
    work.mkdir(parents=True)


def require_repository(root: Path) -> None:
    required = (
        root / "LogicLens.sln",
        root / "contracts" / "active-pointer-v0.schema.json",
        root / "src" / "LogicLens.Api" / "LogicLens.Api.csproj",
        root / "src" / "LogicLens.Web" / "package-lock.json",
        root / "contracts" / "ui-document-v0.schema.json",
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RunFailure(f"repository inputs are missing: {missing}")


def find_repository_root() -> Path:
    for start in (Path.cwd(), Path(__file__).resolve().parent):
        for candidate in (start, *start.parents):
            if (
                (candidate / "LogicLens.sln").is_file()
                and (candidate / "contracts" / "active-pointer-v0.schema.json").is_file()
            ):
                return candidate.resolve()
    raise RunFailure("could not locate LogicLens repository root; pass --repository-root")


def run_entry() -> int:
    try:
        return main()
    except (RunFailure, OSError, subprocess.SubprocessError, RuntimeError) as exc:
        print(f"Transactional LogicLens run failed: {exc}", file=sys.stderr)
        return 1
