from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    record = json.loads(
        args.decision.resolve().read_text(encoding="utf-8")
    )

    expected = record.get("decisionHash")

    payload = dict(record)
    payload.pop("decisionHash", None)

    canonical = (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            separators=(",", ": "),
        )
        + "\n"
    ).encode("utf-8")

    digest = hashlib.sha256()
    digest.update(b"LogicLensActivationDecision\0")
    digest.update(bytes((1,)))
    digest.update(canonical)

    computed = "sha256:" + digest.hexdigest()

    if computed != expected:
        raise RuntimeError(
            "decisionHash differs: "
            f"expected={expected}; computed={computed}"
        )

    report = {
        "schemaVersion": "0.1",
        "stage": "activation-decision-hash-verification",
        "expectedDecisionHash": expected,
        "computedDecisionHash": computed,
        "passed": True,
    }

    args.output.resolve().write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(f"Independent decisionHash: {computed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
