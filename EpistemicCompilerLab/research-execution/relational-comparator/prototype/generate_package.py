from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
GENERATOR_ID = "eng197-relational-generator-v0"
GENERATED_FILES = (
    "schema.sql",
    "seed.sql",
    "permissions.sql",
    "catalogue.json",
    "query-guide.md",
)


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def load_source(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("scope") != "TRAIN_DEV_ONLY_SYNTHETIC":
        raise ValueError("prototype generator refuses non TRAIN/DEV synthetic source")
    return data


def schema_sql() -> str:
    return """CREATE SCHEMA IF NOT EXISTS relational_cmp;

CREATE TABLE relational_cmp.proposition (
    proposition_id text PRIMARY KEY,
    subject_text text NOT NULL,
    predicate_text text NOT NULL,
    object_text text NOT NULL
);

CREATE TABLE relational_cmp.source_assertion (
    assertion_id text PRIMARY KEY,
    proposition_id text NOT NULL REFERENCES relational_cmp.proposition(proposition_id),
    polarity text NOT NULL CHECK (polarity IN ('positive', 'negative')),
    scope_id text NOT NULL,
    version_text text NOT NULL,
    source_id text NOT NULL
);

CREATE TABLE relational_cmp.strict_implication (
    rule_id text PRIMARY KEY,
    antecedent_proposition_id text NOT NULL REFERENCES relational_cmp.proposition(proposition_id),
    consequent_proposition_id text NOT NULL REFERENCES relational_cmp.proposition(proposition_id),
    scope_id text NOT NULL,
    version_text text NOT NULL
);

CREATE OR REPLACE FUNCTION relational_cmp.resolve_claim(
    p_proposition_id text,
    p_scope_id text,
    p_version text
)
RETURNS TABLE (
    status_code text,
    action_code text,
    evidence text[],
    provenance text[]
)
LANGUAGE sql
STABLE
SECURITY INVOKER
AS $$
WITH RECURSIVE positive_reach(proposition_id, assertion_id, source_id, rule_path) AS (
    SELECT a.proposition_id, a.assertion_id, a.source_id, ARRAY[]::text[]
    FROM relational_cmp.source_assertion a
    WHERE a.polarity = 'positive'
      AND a.scope_id = p_scope_id
      AND a.version_text = p_version
    UNION
    SELECT r.consequent_proposition_id, pr.assertion_id, pr.source_id, pr.rule_path || r.rule_id
    FROM positive_reach pr
    JOIN relational_cmp.strict_implication r
      ON r.antecedent_proposition_id = pr.proposition_id
     AND r.scope_id = p_scope_id
     AND r.version_text = p_version
    WHERE NOT r.rule_id = ANY(pr.rule_path)
),
pos AS (
    SELECT DISTINCT assertion_id, source_id
    FROM positive_reach
    WHERE proposition_id = p_proposition_id
),
neg AS (
    SELECT DISTINCT a.assertion_id, a.source_id
    FROM relational_cmp.source_assertion a
    WHERE a.proposition_id = p_proposition_id
      AND a.polarity = 'negative'
      AND a.scope_id = p_scope_id
      AND a.version_text = p_version
),
flags AS (
    SELECT EXISTS (SELECT 1 FROM pos) AS has_positive,
           EXISTS (SELECT 1 FROM neg) AS has_negative
),
classified AS (
    SELECT CASE
             WHEN has_positive AND has_negative THEN 'conflicting'
             WHEN has_positive THEN 'supported'
             WHEN has_negative THEN 'refuted'
             ELSE 'unknown'
           END AS status_code
    FROM flags
),
evidence_rows AS (
    SELECT assertion_id, source_id FROM pos
    UNION
    SELECT assertion_id, source_id FROM neg
)
SELECT c.status_code,
       CASE c.status_code
         WHEN 'supported' THEN 'accept'
         WHEN 'refuted' THEN 'reject'
         ELSE 'review'
       END AS action_code,
       COALESCE((SELECT array_agg(assertion_id ORDER BY assertion_id) FROM evidence_rows), ARRAY[]::text[]) AS evidence,
       COALESCE((SELECT array_agg(DISTINCT source_id ORDER BY source_id) FROM evidence_rows), ARRAY[]::text[]) AS provenance
FROM classified c;
$$;
"""


def seed_sql(source: dict[str, Any]) -> str:
    lines = ["BEGIN;"]
    for p in sorted(source["propositions"], key=lambda item: item["id"]):
        values = [p["id"], p["subject"], p["predicate"], p["object"]]
        lines.append(
            "INSERT INTO relational_cmp.proposition "
            "(proposition_id, subject_text, predicate_text, object_text) VALUES ("
            + ", ".join(sql_literal(v) for v in values)
            + ");"
        )
    for a in sorted(source["assertions"], key=lambda item: item["id"]):
        values = [a["id"], a["proposition_id"], a["polarity"], a["scope_id"], a["version"], a["source_id"]]
        lines.append(
            "INSERT INTO relational_cmp.source_assertion "
            "(assertion_id, proposition_id, polarity, scope_id, version_text, source_id) VALUES ("
            + ", ".join(sql_literal(v) for v in values)
            + ");"
        )
    for r in sorted(source["implications"], key=lambda item: item["id"]):
        values = [r["id"], r["antecedent_proposition_id"], r["consequent_proposition_id"], r["scope_id"], r["version"]]
        lines.append(
            "INSERT INTO relational_cmp.strict_implication "
            "(rule_id, antecedent_proposition_id, consequent_proposition_id, scope_id, version_text) VALUES ("
            + ", ".join(sql_literal(v) for v in values)
            + ");"
        )
    lines.extend(["COMMIT;", ""])
    return "\n".join(lines)


def permissions_sql() -> str:
    return """DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'relational_cmp_reader') THEN
        CREATE ROLE relational_cmp_reader NOLOGIN;
    END IF;
END
$$;

REVOKE ALL ON SCHEMA relational_cmp FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA relational_cmp FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA relational_cmp FROM PUBLIC;
GRANT USAGE ON SCHEMA relational_cmp TO relational_cmp_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA relational_cmp TO relational_cmp_reader;
GRANT EXECUTE ON FUNCTION relational_cmp.resolve_claim(text, text, text) TO relational_cmp_reader;
"""


def catalogue() -> dict[str, Any]:
    return {
        "catalogue_version": "1.0.0",
        "free_sql": False,
        "endpoints": [
            {
                "name": "resolve_claim",
                "database_function": "relational_cmp.resolve_claim",
                "read_only": True,
                "arguments": [
                    {"name": "proposition_id", "type": "string"},
                    {"name": "scope_id", "type": "string"},
                    {"name": "version", "type": "string"},
                ],
                "result": {
                    "maximum_rows": 1,
                    "columns": {
                        "status_code": "status_enum",
                        "action_code": "action_enum",
                        "evidence": "string_array",
                        "provenance": "string_array",
                    },
                },
            }
        ],
    }


def guide() -> str:
    return """# Frozen Qwen guide — relational comparator v0

Use only the typed catalogue. Never write SQL.

For a question about whether one declared proposition holds in a scope/version, call `resolve_claim` with the proposition identifier, scope identifier and version supplied by the experiment adapter. Do not invent identifiers and do not substitute another endpoint.

The returned row is authoritative for the relational comparator. Preserve `supported`, `refuted`, `unknown` and `conflicting` as distinct states. Preserve the returned action. Use evidence/provenance only to explain the result; do not repair, override or infer a different database result.

If a typed call cannot be formed from the visible inputs, emit the frozen query-formation failure object rather than free SQL or a guessed answer.
"""


def build(source_path: Path, output_dir: Path) -> dict[str, Any]:
    source = load_source(source_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    payloads: dict[str, bytes] = {
        "schema.sql": schema_sql().encode("utf-8"),
        "seed.sql": seed_sql(source).encode("utf-8"),
        "permissions.sql": permissions_sql().encode("utf-8"),
        "catalogue.json": canonical_json(catalogue()),
        "query-guide.md": guide().encode("utf-8"),
    }
    for name, payload in payloads.items():
        (output_dir / name).write_bytes(payload)

    manifest = {
        "manifest_version": "1.0.0",
        "generator_id": GENERATOR_ID,
        "generator_sha256": sha256_file(Path(__file__).resolve()),
        "source_path": source_path.name,
        "source_sha256": sha256_file(source_path),
        "source_package_id": source["package_id"],
        "scope": source["scope"],
        "semantic_ownership": {
            "retrieval": "postgresql",
            "recursive_closure": "postgresql",
            "epistemic_status": "postgresql",
            "decision_policy": "postgresql",
            "rendering": "qwen",
        },
        "generated_sha256": {name: sha256_bytes(payloads[name]) for name in sorted(payloads)},
    }
    (output_dir / "package-manifest.json").write_bytes(canonical_json(manifest))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT / "source.prototype.json")
    parser.add_argument("--output", type=Path, default=ROOT / "generated")
    args = parser.parse_args()
    build(args.source.resolve(), args.output.resolve())
    print(f"generated relational package: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
