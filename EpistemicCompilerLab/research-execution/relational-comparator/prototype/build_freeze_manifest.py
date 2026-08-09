from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
REPO = PACKAGE.parents[2]
MANIFEST = PACKAGE / "ENG-197_FREEZE_MANIFEST.json"

FILES = [
    "EpistemicCompilerLab/research-execution/relational-comparator/README.md",
    "EpistemicCompilerLab/research-execution/relational-comparator/contract.json",
    "EpistemicCompilerLab/research-execution/relational-comparator/call.schema.json",
    "EpistemicCompilerLab/research-execution/relational-comparator/result.schema.json",
    "EpistemicCompilerLab/research-execution/relational-comparator/FEASIBILITY_INPUT.json",
    "EpistemicCompilerLab/research-execution/relational-comparator/M15_IDENTIFIER_VISIBILITY_CONTRACT.md",
    "EpistemicCompilerLab/research-execution/relational-comparator/RELATIONAL_STRICT_SUBSET_MAPPING.md",
    "EpistemicCompilerLab/research-execution/relational-comparator/RELATIONAL_SUBSET_CONTRACT.json",
    "EpistemicCompilerLab/research-execution/relational-comparator/RUNTIME_DEPENDENCIES.json",
    "EpistemicCompilerLab/research-execution/relational-comparator/LIVE_POSTGRES_SMOKE_CONTRACT.md",
    "EpistemicCompilerLab/research-execution/relational-comparator/requirements-eng197.txt",
    "EpistemicCompilerLab/research-execution/relational-comparator/prototype/source.prototype.json",
    "EpistemicCompilerLab/research-execution/relational-comparator/prototype/query-registry.prototype.json",
    "EpistemicCompilerLab/research-execution/relational-comparator/prototype/evaluator/expected.prototype.json",
    "EpistemicCompilerLab/research-execution/relational-comparator/prototype/generate_package.py",
    "EpistemicCompilerLab/research-execution/relational-comparator/prototype/adapter.py",
    "EpistemicCompilerLab/research-execution/relational-comparator/prototype/reference_oracle.py",
    "EpistemicCompilerLab/research-execution/relational-comparator/prototype/subset_eligibility.py",
    "EpistemicCompilerLab/research-execution/relational-comparator/prototype/db_executor.py",
    "EpistemicCompilerLab/research-execution/relational-comparator/prototype/live_postgres_smoke.py",
    "EpistemicCompilerLab/research-execution/relational-comparator/prototype/build_subset_equivalence_report.py",
    "EpistemicCompilerLab/research-execution/relational-comparator/prototype/verify.py",
    "EpistemicCompilerLab/research-execution/relational-comparator/prototype/build_freeze_manifest.py",
    "EpistemicCompilerLab/research-execution/relational-comparator/prototype/generated/schema.sql",
    "EpistemicCompilerLab/research-execution/relational-comparator/prototype/generated/seed.sql",
    "EpistemicCompilerLab/research-execution/relational-comparator/prototype/generated/permissions.sql",
    "EpistemicCompilerLab/research-execution/relational-comparator/prototype/generated/catalogue.json",
    "EpistemicCompilerLab/research-execution/relational-comparator/prototype/generated/query-guide.md",
    "EpistemicCompilerLab/research-execution/relational-comparator/prototype/generated/package-manifest.json",
    "EpistemicCompilerLab/scripts/run-relational-comparator-tests.ps1",
    "EpistemicCompilerLab/scripts/run-relational-postgres-smoke.ps1"
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build() -> dict:
    missing = [path for path in FILES if not (REPO / path).is_file()]
    if missing:
        raise RuntimeError(f"ENG-197 freeze closure missing files: {missing}")
    return {
        "schema_version": "1.0.0",
        "linear_issue": "ENG-197",
        "scope": "TRAIN_DEV_ONLY",
        "manifest_self_excluded": True,
        "manifest_path": "EpistemicCompilerLab/research-execution/relational-comparator/ENG-197_FREEZE_MANIFEST.json",
        "file_count": len(FILES),
        "files": {path: sha256(REPO / path) for path in sorted(FILES)},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = build()
    text = json.dumps(expected, indent=2, sort_keys=True) + "\n"
    if args.check:
        actual = MANIFEST.read_text(encoding="utf-8") if MANIFEST.exists() else ""
        if actual != text:
            print("ENG-197 freeze manifest drift detected")
            print(text)
            return 1
        print(f"PASS ENG-197 freeze manifest: {expected['file_count']} files")
        return 0
    MANIFEST.write_text(text, encoding="utf-8", newline="\n")
    print(MANIFEST)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
