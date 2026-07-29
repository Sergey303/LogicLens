from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Sequence

from .processes import ManagedProcess, RunFailure


ENTITY_IDS = (
    "urn:logiclens:person:alex",
    "urn:logiclens:org:iis",
    "urn:logiclens:document:paper",
)


def get(url: str, accept: str = "*/*") -> tuple[int, bytes, str]:
    request = urllib.request.Request(
        url,
        headers={"Accept": accept},
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
        return error.code, error.read(), error.headers.get_content_type()


def wait_for(
    name: str,
    url: str,
    processes: Sequence[ManagedProcess],
    predicate: Callable[[int, bytes, str], bool],
    timeout_seconds: float = 45,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        for process in processes:
            process.require_running()
        try:
            response = get(url)
            if predicate(*response):
                return
        except (OSError, RunFailure) as exc:
            last_error = exc
        time.sleep(0.25)
    raise RunFailure(f"{name} did not become ready at {url}: {last_error}")


def verify_vertical_slice(
    api_url: str,
    web_url: str,
    *,
    expected_epoch: int = 0,
    expected_revision: int = 0,
) -> None:
    direct_health = require_json(f"{api_url}/api/health", "direct API health")
    require(direct_health.get("kind") == "health", "direct health kind is invalid")

    proxy_status, proxy_health_bytes, proxy_health_type = get(
        f"{web_url}/api/health",
        "application/json",
    )
    require(proxy_status == 200, "Vite proxy health must return HTTP 200")
    require(proxy_health_type == "application/json", "proxy health must be JSON")
    proxy_health = parse_json(proxy_health_bytes, "proxy health")
    require(proxy_health == direct_health, "proxy health differs from direct API health")

    index_status, index_bytes, index_type = get(web_url, "text/html")
    require(index_status == 200, "web root must return HTTP 200")
    require(index_type == "text/html", "web root must return HTML")
    index_text = index_bytes.decode("utf-8")
    require('<div id="root"></div>' in index_text, "React root element is missing")
    require("/src/main.tsx" in index_text, "Vite entry module is missing")

    entry_status, entry_bytes, _ = get(f"{web_url}/src/main.tsx")
    require(entry_status == 200, "Vite must serve the React entry module")
    require(b"createRoot" in entry_bytes, "served entry module is not the React app")

    for entity_id in ENTITY_IDS:
        encoded = urllib.parse.quote(entity_id, safe="")
        route_status, route_bytes, route_type = get(
            f"{web_url}/entities/{encoded}",
            "text/html",
        )
        require(route_status == 200, f"entity route failed for {entity_id}")
        require(route_type == "text/html", "entity route must return the React shell")
        require(
            b'<div id="root"></div>' in route_bytes,
            f"entity route has no React root for {entity_id}",
        )

        query = urllib.parse.urlencode(
            {"language": "ru", "includeProlog": "true"}
        )
        path = f"/api/entities/{encoded}/view?{query}"
        direct_status, direct_bytes, direct_type = get(
            api_url + path,
            "application/json",
        )
        proxy_status, proxy_bytes, proxy_type = get(
            web_url + path,
            "application/json",
        )
        require(direct_status == 200, f"direct entity view failed for {entity_id}")
        require(proxy_status == 200, f"proxied entity view failed for {entity_id}")
        require(direct_type == "application/json", "direct entity view must be JSON")
        require(proxy_type == "application/json", "proxied entity view must be JSON")
        require(
            direct_bytes == proxy_bytes,
            f"Vite proxy changed entity view bytes for {entity_id}",
        )
        second_status, second_bytes, _ = get(web_url + path, "application/json")
        require(second_status == 200, "repeated proxied view must succeed")
        require(
            second_bytes == proxy_bytes,
            f"entity view is not byte-identical for {entity_id}",
        )
        document = parse_json(proxy_bytes, f"UI Document for {entity_id}")
        require(document.get("schemaVersion") == "0.1", "schemaVersion mismatch")
        require(document.get("epoch") == expected_epoch, "epoch mismatch")
        require(document.get("revision") == expected_revision, "revision mismatch")
        require(
            document.get("context") == {"kind": "entity", "entityId": entity_id},
            f"entity context mismatch for {entity_id}",
        )
        page = document.get("page")
        require(isinstance(page, dict), f"page is missing for {entity_id}")
        require(isinstance(page.get("title"), str), f"title is missing for {entity_id}")
        require(bool(page.get("sections")), f"sections are missing for {entity_id}")

    unknown_status, _, unknown_type = get(f"{web_url}/api/not-a-command")
    require(unknown_status == 404, "unknown API route must remain HTTP 404")
    require(unknown_type != "text/html", "unknown API route must not return React HTML")


def require_json(url: str, context: str) -> dict[str, Any]:
    status, data, content_type = get(url, "application/json")
    require(status == 200, f"{context} must return HTTP 200")
    require(content_type == "application/json", f"{context} must return JSON")
    return parse_json(data, context)


def parse_json(data: bytes, context: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RunFailure(f"{context} is not UTF-8 JSON: {data[:200]!r}") from exc
    if not isinstance(value, dict):
        raise RunFailure(f"{context} must be a JSON object")
    return value


def validate_loopback_url(value: str, name: str) -> urllib.parse.ParseResult:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme != "http":
        raise RunFailure(f"{name} must use http for the local runner: {value}")
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise RunFailure(f"{name} must bind to a loopback host: {value}")
    if parsed.port is None:
        raise RunFailure(f"{name} must include an explicit port: {value}")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise RunFailure(f"{name} must be an origin without path/query/fragment: {value}")
    return parsed


def require_port_not_listening(
    parsed: urllib.parse.ParseResult,
    name: str,
) -> None:
    hostname = parsed.hostname
    port = parsed.port
    if hostname is None or port is None:
        raise RunFailure(f"{name} has no host or port")

    addresses = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    for family, socket_type, protocol, _, socket_address in addresses:
        with socket.socket(family, socket_type, protocol) as probe:
            probe.settimeout(0.2)
            if probe.connect_ex(socket_address) == 0:
                raise RunFailure(
                    f"{name} is already in use at {hostname}:{port}; "
                    "stop the previous local run or choose another port"
                )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RunFailure(message)
