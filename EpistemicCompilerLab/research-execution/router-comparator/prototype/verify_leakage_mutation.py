from __future__ import annotations
import copy
import json
from pathlib import Path
import yaml

from verify import scan_visible_registry

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT.parent
CASES = json.loads((ROOT / "cases.train_dev.json").read_text(encoding="utf-8"))["cases"]
REGISTRY = yaml.safe_load((PACKAGE / "ROUTING_CAPABILITY_REGISTRY.yaml").read_text(encoding="utf-8"))


def expect_rejected(name: str, registry) -> None:
    try:
        scan_visible_registry(registry, CASES)
    except Exception:
        print(f"PASS {name}")
        return
    raise RuntimeError(f"{name} was not detected")


def main() -> int:
    scan_visible_registry(REGISTRY, CASES)

    case_leak = copy.deepcopy(REGISTRY)
    case_leak["capabilities"][0]["neutral_surface"]["description"] += " train-route-001"
    expect_rejected("case-id leakage mutation", case_leak)

    canonical_id_leak = copy.deepcopy(REGISTRY)
    canonical_id_leak["capabilities"][0]["neutral_surface"]["description"] += " " + REGISTRY["capabilities"][1]["canonical_id"]
    expect_rejected("canonical capability-id leakage mutation", canonical_id_leak)

    print("PASS leakage mutation detection")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
