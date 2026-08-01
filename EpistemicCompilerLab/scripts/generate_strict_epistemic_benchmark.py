#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from strict_epistemic_benchmark_build import build_benchmark
from strict_epistemic_benchmark_data import SEED


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lab-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--swipl", required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
                for item in records),
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    lab = args.lab_root.resolve()
    output = args.output_root.resolve()
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    output.mkdir(parents=True)

    cases, catalog = build_benchmark(args.swipl, lab)
    case_path = output / "strict-epistemic-benchmark-v0.candidate.jsonl"
    source_path = output / "strict-epistemic-source-v0.candidate.jsonl"
    write_jsonl(case_path, cases)
    write_jsonl(source_path, catalog)
    commit = subprocess.check_output(
        ["git", "-C", str(lab.parent), "rev-parse", "HEAD"],
        text=True, encoding="utf-8",
    ).strip()
    primary = [case for case in cases if case["caseKind"] == "epistemic"]
    manifest = {
        "schemaVersion": 2,
        "kind": "strict-epistemic-benchmark-candidate",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "commit": commit,
        "seed": SEED,
        "caseCount": len(cases),
        "primaryCaseCount": len(primary),
        "clarificationCaseCount": len(cases) - len(primary),
        "uniquePrimaryPropositions": len({
            case["annotation"]["uniqueProposition"] for case in primary
        }),
        "sourceAssertionCount": len(catalog),
        "splitCounts": dict(Counter(case["split"] for case in cases)),
        "statusCounts": dict(Counter(case["expected"]["status"] for case in primary)),
        "casesSha256": sha256(case_path),
        "sourceCatalogSha256": sha256(source_path),
        "caseOracleSha256": sha256(lab / "prolog" / "strict_epistemic_case.pl"),
        "generatorSha256": sha256(Path(__file__)),
        "status": "candidate_requires_review_and_freeze",
        "qwenEvaluated": False,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    shutil.make_archive(str(output), "zip", root_dir=output)
    print(json.dumps(manifest, ensure_ascii=False))
    print("[CGR_ARTIFACT_TITLE] Strict epistemic benchmark candidate v2")
    print(f"[CGR_ARTIFACT] {output}.zip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
