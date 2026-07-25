from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
import urllib.parse
import webbrowser
from pathlib import Path

from .processes import (
    ManagedProcess,
    RunFailure,
    executable_command,
    require_executable,
    run_checked,
    stop_all,
)
from .verification import (
    require_port_not_listening,
    validate_loopback_url,
    verify_vertical_slice,
    wait_for,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare and run the LogicLens zero-epoch vertical slice: "
            "portable epoch, ASP.NET API, Vite React renderer and SWI-Prolog."
        )
    )
    parser.add_argument("--repository-root", type=Path)
    parser.add_argument("--work-directory", type=Path)
    parser.add_argument("--api-url", default="http://127.0.0.1:5080")
    parser.add_argument("--web-url", default="http://127.0.0.1:5173")
    parser.add_argument("--swipl", default="swipl")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Prepare, start, verify and stop instead of keeping services running.",
    )
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

    api_origin = normalize_origin(args.api_url)
    web_origin = normalize_origin(args.web_url)
    api = validate_loopback_url(api_origin, "API URL")
    web = validate_loopback_url(web_origin, "web URL")
    if (api.hostname, api.port) == (web.hostname, web.port):
        raise RunFailure("API URL and web URL must use different loopback ports")
    require_port_not_listening(api, "API URL")
    require_port_not_listening(web, "web URL")

    work = (
        args.work_directory.resolve()
        if args.work_directory is not None
        else root / ".logiclens" / "zero-epoch"
    )
    reset_work_directory(root, work)
    epoch = work / "active-epoch-000"
    logs = work / "logs"

    dotnet = require_executable("dotnet")
    npm = require_executable("npm")
    swipl = require_executable(args.swipl)
    git = require_executable("git")

    prepare(root, work, epoch, dotnet, npm, swipl, git)

    environment = os.environ.copy()
    environment.update(
        {
            "DOTNET_NOLOGO": "1",
            "ASPNETCORE_ENVIRONMENT": "Production",
            "ASPNETCORE_URLS": api_origin,
            "Prolog__ExecutablePath": swipl,
            "Prolog__EpochPath": str(epoch),
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
    web_environment.update(
        {
            "LOGICLENS_API_URL": api_origin,
            "BROWSER": "none",
        }
    )
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

        verify_vertical_slice(api_origin, web_origin)
        print("Zero-epoch vertical slice verification passed.")
        print(f"Web: {web_origin}/entities/urn%3Alogiclens%3Aperson%3Aalex")
        print(f"API health: {api_origin}/api/health")
        print(f"Prepared runtime: {work}")

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
        print("Stopping zero-epoch vertical slice.")
        return 0
    finally:
        stop_all(processes)


def prepare(
    root: Path,
    work: Path,
    epoch: Path,
    dotnet: str,
    npm: str,
    swipl: str,
    git: str,
) -> None:
    print("Preparing LogicLens zero-epoch vertical slice.")
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

    completed = subprocess.run(
        [git, "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout.strip():
        raise RunFailure(f"Could not resolve repository commit: {completed.stderr}")
    engine_commit = completed.stdout.strip()

    epoch.mkdir(parents=True)
    run_checked(
        [
            sys.executable,
            str(root / "tools" / "build_active_epoch.py"),
            "--repository-root",
            str(root),
            "--output",
            str(epoch),
            "--engine-commit",
            engine_commit,
            "--no-build",
        ],
        cwd=root,
    )
    run_checked([swipl, "--version"], cwd=root)

    manifest = epoch / "manifest.json"
    web_index = web_root / "dist" / "index.html"
    if not manifest.is_file():
        raise RunFailure(f"Active epoch manifest was not produced: {manifest}")
    if not web_index.is_file():
        raise RunFailure(f"Production web bundle was not produced: {web_index}")
    (work / "logs").mkdir(parents=True, exist_ok=True)


def normalize_origin(value: str) -> str:
    return value.rstrip("/")


def reset_work_directory(root: Path, work: Path) -> None:
    if work == root or work in root.parents:
        raise RunFailure(f"Unsafe work directory: {work}")
    source_epoch = (root / "epochs" / "epoch-000").resolve()
    if work == source_epoch or source_epoch in work.parents:
        raise RunFailure("Work directory cannot be the reviewed source epoch")
    if work.exists():
        if not work.is_dir():
            raise RunFailure(f"Work path exists and is not a directory: {work}")
        shutil.rmtree(work)
    work.mkdir(parents=True)


def require_repository(root: Path) -> None:
    required = (
        root / "LogicLens.sln",
        root / "tools" / "build_active_epoch.py",
        root / "src" / "LogicLens.Api" / "LogicLens.Api.csproj",
        root / "src" / "LogicLens.Web" / "package-lock.json",
        root / "contracts" / "ui-document-v0.schema.json",
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RunFailure(f"Repository inputs are missing: {missing}")


def find_repository_root() -> Path:
    for start in (Path.cwd(), Path(__file__).resolve().parent):
        for candidate in (start, *start.parents):
            if (candidate / "LogicLens.sln").is_file() and (
                candidate / "src" / "LogicLens.Web" / "package.json"
            ).is_file():
                return candidate.resolve()
    raise RunFailure(
        "Could not locate the LogicLens repository root; pass --repository-root."
    )


def run_entry() -> int:
    try:
        return main()
    except (RunFailure, OSError, subprocess.SubprocessError) as exc:
        print(f"Zero-epoch run failed: {exc}", file=sys.stderr)
        return 1
