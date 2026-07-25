#!/usr/bin/env python3
"""Process-level verification for LogicLens API and UI Document v0."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

from jsonschema import Draft202012Validator


PERSON = "urn:logiclens:person:alex"


class ApiFailure(AssertionError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--epoch", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--url", default="http://127.0.0.1:5080")
    return parser.parse_args()


def get(url: str) -> tuple[int, bytes, str]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json, text/plain"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return (
                response.status,
                response.read(),
                response.headers.get_content_type(),
            )
    except urllib.error.HTTPError as error:
        return (
            error.code,
            error.read(),
            error.headers.get_content_type(),
        )


def parse_json(data: bytes, context: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ApiFailure(f"{context} is not valid UTF-8 JSON: {data!r}") from exc
    if not isinstance(value, dict):
        raise ApiFailure(f"{context} must be a JSON object: {value!r}")
    return value


def entity_url(base_url: str, suffix: str, **query: Any) -> str:
    entity = urllib.parse.quote(PERSON, safe="")
    url = f"{base_url}/api/entities/{entity}/{suffix}"
    if query:
        url += "?" + urllib.parse.urlencode(query)
    return url


def iter_components(document: dict[str, Any]) -> Iterator[dict[str, Any]]:
    def visit(component: dict[str, Any]) -> Iterator[dict[str, Any]]:
        yield component
        if component.get("kind") == "section":
            for child in component.get("components", []):
                if isinstance(child, dict):
                    yield from visit(child)

    page = document.get("page")
    if not isinstance(page, dict):
        return
    for section in page.get("sections", []):
        if isinstance(section, dict):
            yield from visit(section)


def base_fact_ids(document: dict[str, Any]) -> list[str]:
    fact_ids: list[str] = []
    for component in iter_components(document):
        if component.get("kind") != "property":
            continue
        for value in component.get("values", []):
            if not isinstance(value, dict):
                continue
            source = value.get("source")
            if not isinstance(source, dict) or source.get("kind") != "base":
                continue
            fact = source.get("fact")
            if not isinstance(fact, dict) or not isinstance(fact.get("factId"), str):
                raise ApiFailure(f"base value has no complete source fact: {value!r}")
            fact_ids.append(fact["factId"])
    return fact_ids


def wait_until_ready(base_url: str, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 30
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate(timeout=5)
            raise ApiFailure(
                f"API exited before becoming ready: exit={process.returncode}, "
                f"stdout={stdout!r}, stderr={stderr!r}"
            )
        try:
            status, body, _ = get(f"{base_url}/api/health")
            if status == 200:
                health = parse_json(body, "health response")
                if health.get("kind") == "health":
                    return
        except (OSError, ApiFailure) as exc:
            last_error = exc
        time.sleep(0.25)
    raise ApiFailure(f"API did not become ready: {last_error}")


def stop_process(process: subprocess.Popen[str]) -> tuple[str, str]:
    if process.poll() is None:
        process.terminate()
        try:
            return process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
    return process.communicate(timeout=10)


def main() -> int:
    args = parse_args()
    root = args.repository_root.resolve()
    epoch = args.epoch.resolve()
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    env = os.environ.copy()
    env.update(
        {
            "ASPNETCORE_URLS": args.url,
            "ASPNETCORE_ENVIRONMENT": "Production",
            "Prolog__EpochPath": str(epoch),
            "UiDocument__SchemaPath": str(args.schema.resolve()),
            "DOTNET_NOLOGO": "1",
        }
    )
    command = [
        "dotnet",
        "run",
        "--project",
        str(root / "src/LogicLens.Api/LogicLens.Api.csproj"),
        "--configuration",
        "Release",
        "--no-build",
        "--no-launch-profile",
    ]
    process = subprocess.Popen(
        command,
        cwd=root,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        wait_until_ready(args.url, process)

        status, health_bytes, content_type = get(f"{args.url}/api/health")
        assert status == 200
        assert content_type == "application/json"
        health = parse_json(health_bytes, "health response")
        assert health["kind"] == "health"
        assert health["availableCommands"] == [
            "health",
            "inspect-facts",
            "entity-view",
            "subgraph",
        ]

        status, facts_bytes, content_type = get(entity_url(args.url, "facts"))
        assert status == 200
        assert content_type == "application/json"
        facts_result = parse_json(facts_bytes, "facts response")
        facts = facts_result.get("facts")
        assert isinstance(facts, list)
        assert len(facts) == 8
        authoritative_ids = [fact["factId"] for fact in facts]
        assert authoritative_ids == sorted(authoritative_ids)
        assert len(authoritative_ids) == len(set(authoritative_ids))

        view_url = entity_url(
            args.url,
            "view",
            language="ru",
            includeProlog="true",
        )
        status, first_view_bytes, content_type = get(view_url)
        assert status == 200
        assert content_type == "application/json"
        status, second_view_bytes, _ = get(view_url)
        assert status == 200
        assert first_view_bytes == second_view_bytes, "view response must be byte-identical"

        document = parse_json(first_view_bytes, "UI Document response")
        validator.validate(document)
        assert document["schemaVersion"] == "0.1"
        assert document["epoch"] == 0
        assert document["revision"] == 0
        assert document["context"] == {"kind": "entity", "entityId": PERSON}
        assert document["page"]["title"] == "Алексей Ветров"

        displayed = base_fact_ids(document)
        counts = Counter(displayed)
        assert set(counts) == set(authoritative_ids)
        assert all(count == 1 for count in counts.values()), counts

        properties = [
            component
            for component in iter_components(document)
            if component.get("kind") == "property"
        ]
        directions = {component["direction"] for component in properties}
        assert {"outgoing", "incoming"}.issubset(directions)
        assert any(
            section.get("presentation") == "technical"
            for section in document["page"]["sections"]
        )
        assert any(
            component.get("kind") == "rawProlog"
            and "fact(" in component.get("code", "")
            for component in iter_components(document)
        )

        status, prolog_bytes, content_type = get(entity_url(args.url, "prolog"))
        assert status == 200
        assert content_type == "text/plain"
        prolog = prolog_bytes.decode("utf-8")
        assert prolog.count("fact(") == 8
        assert "Алексей Ветров" in prolog

        long_id = urllib.parse.quote("x" * 1025, safe="")
        status, error_bytes, content_type = get(
            f"{args.url}/api/entities/{long_id}/facts"
        )
        assert status == 400
        assert content_type == "application/problem+json"
        problem = parse_json(error_bytes, "problem response")
        assert problem["code"] == "invalid_request"
        text = error_bytes.decode("utf-8")
        assert "System." not in text
        assert " at " not in text
        assert "stack" not in text.lower()

        print("LogicLens API contract verification passed.")
        return 0
    finally:
        stdout, stderr = stop_process(process)
        log_path = Path(os.environ.get("LOGICLENS_API_LOG", "/tmp/logiclens-api.log"))
        log_path.write_text(
            "--- stdout ---\n"
            + stdout
            + "\n--- stderr ---\n"
            + stderr,
            encoding="utf-8",
        )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        ApiFailure,
        AssertionError,
        OSError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
    ) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
