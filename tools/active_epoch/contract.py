from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any


UTF8 = "utf-8"
SOURCE_EPOCH = PurePosixPath("epochs/epoch-000")
DATA_PROJECT = PurePosixPath(
    "tools/LogicLens.EpochCompiler/LogicLens.EpochCompiler.csproj"
)
ONTOLOGY_PROJECT = PurePosixPath(
    "tools/LogicLens.OntologyCompiler/LogicLens.OntologyCompiler.csproj"
)
CLI_SCHEMA = PurePosixPath("contracts/prolog-cli-v0.schema.json")

RUNTIME_FILES = (
    PurePosixPath("entry.pl"),
    PurePosixPath("data/epoch_data.pl"),
    PurePosixPath("ontology/ontology_data.pl"),
    PurePosixPath("rules/cli_runtime.pl"),
    PurePosixPath("rules/generic_view.pl"),
    PurePosixPath("rules/label_rules.pl"),
    PurePosixPath("rules/subgraph.pl"),
    PurePosixPath("rules/traversal_policy.pl"),
    PurePosixPath("rules/view_policy.pl"),
)

SMOKE_REQUESTS: tuple[tuple[str, dict[str, Any]], ...] = (
    (
        "health.request.json",
        {
            "protocolVersion": "0.1",
            "requestId": "epoch-000-health",
            "command": "health",
            "epoch": 0,
            "revision": 0,
            "options": {},
        },
    ),
    (
        "entity-view.request.json",
        {
            "protocolVersion": "0.1",
            "requestId": "epoch-000-entity-view",
            "command": "entity-view",
            "epoch": 0,
            "revision": 0,
            "options": {
                "entityId": "urn:logiclens:person:alex",
                "language": "ru",
            },
        },
    ),
    (
        "subgraph.request.json",
        {
            "protocolVersion": "0.1",
            "requestId": "epoch-000-subgraph",
            "command": "subgraph",
            "epoch": 0,
            "revision": 0,
            "options": {
                "rootId": "urn:logiclens:person:alex",
                "depth": 2,
                "direction": "both",
                "language": "ru",
            },
        },
    ),
)
