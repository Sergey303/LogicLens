from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT.parent
REPO = PACKAGE.parents[2]
MANIFEST = PACKAGE / "ENG-200_FREEZE_MANIFEST.json"

FILES = [
    ".github/workflows/eng-200-router-validation.yml",
    "EpistemicCompilerLab/scripts/run-router-comparator-tests.ps1",
    "EpistemicCompilerLab/research-execution/router-comparator/README.md",
    "EpistemicCompilerLab/research-execution/router-comparator/ROUTING_FEATURE_CONTRACT.json",
    "EpistemicCompilerLab/research-execution/router-comparator/ROUTING_CAPABILITY_REGISTRY.yaml",
    "EpistemicCompilerLab/research-execution/router-comparator/ROUTING_CAPABILITY_REGISTRY.schema.json",
    "EpistemicCompilerLab/research-execution/router-comparator/CAPABILITY_IO_SCHEMAS.json",
    "EpistemicCompilerLab/research-execution/router-comparator/ROUTING_MODE_CONTRACTS.yaml",
    "EpistemicCompilerLab/research-execution/router-comparator/ARGUMENT_BINDING_CONTRACT.md",
    "EpistemicCompilerLab/research-execution/router-comparator/TEACHER_ROUTING_IR.schema.json",
    "EpistemicCompilerLab/research-execution/router-comparator/TEACHER_POLICY_GENERATION_CONTRACT.md",
    "EpistemicCompilerLab/research-execution/router-comparator/DECISION_GRAPH_CONTRACT.md",
    "EpistemicCompilerLab/research-execution/router-comparator/PROLOG_ROUTER_CONTRACT.md",
    "EpistemicCompilerLab/research-execution/router-comparator/ROUTING_EQUIVALENCE_TESTS.md",
    "EpistemicCompilerLab/research-execution/router-comparator/FEASIBILITY_INPUT.json",
    "EpistemicCompilerLab/research-execution/router-comparator/RUNTIME_DEPENDENCIES.yaml",
    "EpistemicCompilerLab/research-execution/router-comparator/requirements-eng200.txt",
    "EpistemicCompilerLab/research-execution/router-comparator/prototype/policy.ir.json",
    "EpistemicCompilerLab/research-execution/router-comparator/prototype/cases.train_dev.json",
    "EpistemicCompilerLab/research-execution/router-comparator/prototype/feature_adapter.py",
    "EpistemicCompilerLab/research-execution/router-comparator/prototype/decision_graph.py",
    "EpistemicCompilerLab/research-execution/router-comparator/prototype/generate_policy.py",
    "EpistemicCompilerLab/research-execution/router-comparator/prototype/generate_visible_catalogue.py",
    "EpistemicCompilerLab/research-execution/router-comparator/prototype/build_freeze_manifest.py",
    "EpistemicCompilerLab/research-execution/router-comparator/prototype/generated/policy.pl",
    "EpistemicCompilerLab/research-execution/router-comparator/prototype/generated/qwen-catalogue.neutral.json",
    "EpistemicCompilerLab/research-execution/router-comparator/prototype/generated/qwen-catalogue.adapted.json",
    "EpistemicCompilerLab/research-execution/router-comparator/prototype/policy-explanation.neutral.md",
    "EpistemicCompilerLab/research-execution/router-comparator/prototype/verify.py",
    "EpistemicCompilerLab/research-execution/router-comparator/prototype/verify_leakage_mutation.py",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict:
    missing = [path for path in FILES if not (REPO / path).is_file()]
    if missing:
        raise RuntimeError(f"freeze manifest missing files: {missing}")
    return {
        "schema_version": "1.0.0",
        "linear_issue": "ENG-200",
        "scope": "TRAIN_DEV_ONLY",
        "manifest_self_excluded": True,
        "manifest_path": "EpistemicCompilerLab/research-execution/router-comparator/ENG-200_FREEZE_MANIFEST.json",
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
            print("ENG-200 freeze manifest drift detected")
            print(text)
            return 1
        print(f"PASS freeze manifest: {expected['file_count']} files")
        return 0
    MANIFEST.write_text(text, encoding="utf-8", newline="\n")
    print(MANIFEST)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
