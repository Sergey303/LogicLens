import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES_PATH = ROOT / "general_regression_dev.jsonl"


def normalize(text):
    return str(text).replace("\r\n", "\n").strip()


def load_jsonl(path):
    rows = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at line {line_number}") from exc
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    args = parser.parse_args()

    cases = load_jsonl(CASES_PATH)
    predictions = load_jsonl(args.predictions)

    by_id = {row["id"]: row for row in cases}
    if len(by_id) != len(cases):
        raise ValueError("duplicate case id")
    pred_by_id = {}
    for row in predictions:
        if set(row) != {"id", "output"}:
            raise ValueError("prediction rows must contain exactly id/output")
        if row["id"] in pred_by_id:
            raise ValueError("duplicate prediction id")
        pred_by_id[row["id"]] = row["output"]

    if set(pred_by_id) != set(by_id):
        missing = sorted(set(by_id) - set(pred_by_id))
        extra = sorted(set(pred_by_id) - set(by_id))
        raise ValueError(f"prediction id mismatch missing={missing} extra={extra}")

    family_correct = defaultdict(int)
    family_total = defaultdict(int)
    per_case = []
    for case_id in sorted(by_id):
        case = by_id[case_id]
        correct = normalize(pred_by_id[case_id]) == normalize(case["expected"])
        family_total[case["family"]] += 1
        family_correct[case["family"]] += int(correct)
        per_case.append({"id": case_id, "family": case["family"], "correct": correct})

    total_correct = sum(int(row["correct"]) for row in per_case)
    report = {
        "schema_version": "1.0.0",
        "cases": len(per_case),
        "correct": total_correct,
        "accuracy": total_correct / len(per_case),
        "families": {
            family: {
                "correct": family_correct[family],
                "total": family_total[family],
                "accuracy": family_correct[family] / family_total[family],
            }
            for family in sorted(family_total)
        },
        "per_case": per_case,
    }
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
