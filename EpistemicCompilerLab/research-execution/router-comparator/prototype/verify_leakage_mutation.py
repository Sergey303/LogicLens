from __future__ import annotations
import copy
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT.parent
CASES = json.loads((ROOT / "cases.train_dev.json").read_text(encoding="utf-8"))["cases"]
REGISTRY = yaml.safe_load((PACKAGE / "ROUTING_CAPABILITY_REGISTRY.yaml").read_text(encoding="utf-8"))
EXPLANATION = (ROOT / "policy-explanation.neutral.md").read_text(encoding="utf-8")


def visible_text(registry) -> str:
    chunks = [EXPLANATION]
    for item in registry["capabilities"]:
        chunks.extend([
            item["handle"],
            item["neutral_surface"]["label"],
            item["neutral_surface"]["description"],
            item["schema_adapted_dev_surface"]["label"],
            item["schema_adapted_dev_surface"]["description"],
        ])
    return "\n".join(chunks)


def scan(registry) -> None:
    text = visible_text(registry)
    for case in CASES:
        if case["case_id"] in text or case["question"] in text:
            raise RuntimeError(f"visible benchmark leak: {case['case_id']}")
    for item in registry["capabilities"]:
        if item["canonical_id"] in text:
            raise RuntimeError(f"internal canonical ID leak: {item['canonical_id']}")


def main() -> int:
    scan(REGISTRY)
    mutated = copy.deepcopy(REGISTRY)
    mutated["capabilities"][0]["neutral_surface"]["description"] += " train-route-001"
    try:
        scan(mutated)
    except RuntimeError as exc:
        if "train-route-001" not in str(exc):
            raise
    else:
        raise RuntimeError("injected visible case leak was not detected")
    print("PASS leakage mutation detection")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
