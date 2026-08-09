#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROTO = ROOT / "prototype"
FIXTURES = PROTO / "fixtures"
BASE_VALIDATOR = PROTO / "validate_wp006_contract.py"
GATE = PROTO / "evaluate_power_gate.py"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def run_json(args):
    completed = subprocess.run(args, text=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed rc={completed.returncode}: {' '.join(map(str,args))}\n"
            f"stdout={completed.stdout}\nstderr={completed.stderr}"
        )
    try:
        return json.loads(completed.stdout.strip().splitlines()[-1])
    except Exception as exc:
        raise RuntimeError(f"command did not emit final JSON: {completed.stdout}") from exc


def validate_gate_schema():
    schema = json.loads((ROOT / "POWER_GATE_INPUT.schema.json").read_text(encoding="utf-8"))
    require(schema["properties"]["schema_version"]["const"] == "1.0.0", "gate schema version drift")
    required = set(schema["required"])
    require(required == {"schema_version", "wp004_arm_binding", "wp005_scorer", "inventory", "nuisance", "evidence", "sealed_access"}, "gate top-level required fields drift")
    sealed = schema["properties"]["sealed_access"]["properties"]
    require(sealed["holdout_accessed"]["const"] is False, "gate schema permits HOLDOUT access")
    require(sealed["replication_accessed"]["const"] is False, "gate schema permits REPLICATION access")
    require(sealed["directional_confirmatory_effect_seen_by_power_analyst"]["const"] is False, "gate schema permits directional effect leakage")
    nuisance = schema["properties"]["nuisance"]["properties"]
    require(set(nuisance["source"]["enum"]) == {"frozen_primary_planning", "single_blinded_nuisance_update"}, "nuisance source vocabulary drift")


def validate_gate_fixtures():
    passing = run_json([sys.executable, str(GATE), "--input", str(FIXTURES / "power_gate_pass.json")])
    fail_n = run_json([sys.executable, str(GATE), "--input", str(FIXTURES / "power_gate_fail_n.json")])
    fail_clusters = run_json([sys.executable, str(GATE), "--input", str(FIXTURES / "power_gate_fail_clusters.json")])

    require(passing["decision"] == "POWER_GATE_PASS", "N=802 sufficient-cluster fixture must PASS")
    require(passing["required_eligible_n"] == 802, "PASS fixture required N drift")
    require(passing["available_eligible_n"] == 802, "PASS fixture available N drift")
    require(passing["n_gate_pass"] is True and passing["cluster_gate_pass"] is True, "PASS fixture component gate failed")

    require(fail_n["decision"] == "POWER_GATE_FAIL", "N=801 fixture must FAIL")
    require(fail_n["required_eligible_n"] == 802, "N-negative fixture required N drift")
    require(fail_n["available_eligible_n"] == 801, "N-negative fixture available N drift")
    require(fail_n["n_gate_pass"] is False and fail_n["cluster_gate_pass"] is True, "N-negative fixture wrong failure mode")

    require(fail_clusters["decision"] == "POWER_GATE_FAIL", "29-cluster fixture must FAIL")
    require(fail_clusters["available_independent_clusters"] == 29, "cluster-negative fixture cluster count drift")
    require(fail_clusters["n_gate_pass"] is True and fail_clusters["cluster_gate_pass"] is False, "cluster-negative fixture wrong failure mode")
    return passing, fail_n, fail_clusters


def main():
    base = run_json([sys.executable, str(BASE_VALIDATOR)])
    require(base["contract"] == "PASS", "base WP-006 contract validator did not PASS")
    require(base["required_eligible_n"] == 802, "base required N drift")

    for path in [
        ROOT / "POWER_GATE_INPUT.schema.json",
        GATE,
        FIXTURES / "power_gate_pass.json",
        FIXTURES / "power_gate_fail_n.json",
        FIXTURES / "power_gate_fail_clusters.json",
    ]:
        require(path.is_file(), f"missing complete WP-006 artifact: {path}")

    validate_gate_schema()
    passing, fail_n, fail_clusters = validate_gate_fixtures()

    print(json.dumps({
        "work_package": "WP-006",
        "complete_contract": "PASS",
        "required_eligible_n": 802,
        "fixture_PASS_decision": passing["decision"],
        "fixture_N801_decision": fail_n["decision"],
        "fixture_clusters29_decision": fail_clusters["decision"],
        "real_inventory_gate": "NOT_EVALUATED_BY_FIXTURES",
        "github_actions_used": False,
        "independent_statistical_review": "NOT_PERFORMED_BY_THIS_VALIDATOR",
        "holdout": "NOT_AUTHORIZED"
    }, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"WP-006 complete validation failed: {exc}", file=sys.stderr)
        raise
