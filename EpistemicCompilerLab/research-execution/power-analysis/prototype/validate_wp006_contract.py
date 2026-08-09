#!/usr/bin/env python3
import importlib.util
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROTO = ROOT / "prototype"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load_json(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_primary_contract():
    contract = load_json("PRIMARY_ANALYSIS_CONTRACT.json")
    estimand = contract["primary_estimand"]
    hypothesis = contract["hypothesis"]
    require(estimand["paired"] is True, "primary analysis must be paired")
    require(estimand["outcome"] == "publication_composite_correctness", "primary endpoint drift")
    require(estimand["outcome_type"] == "binary", "primary endpoint type drift")
    require(estimand["se_soi_absolute"] == 0.08, "SESOI drift")
    require(hypothesis["alpha_two_sided"] == 0.05, "alpha drift")
    require(hypothesis["target_power_at_sesoi"] == 0.90, "target power drift")
    require(contract["multiplicity"]["primary_confirmatory_contrasts"] == 1, "must have exactly one primary contrast")
    require(contract["multiplicity"]["primary_alpha_allocation"] == 0.05, "primary alpha allocation drift")
    require("best-DEV-arm selection is forbidden" in estimand["arm_binding_rule"], "best-DEV arm selection not forbidden")
    require(contract["primary_analysis"]["cluster_id"] == "source_family_id", "cluster ID drift")
    require("fewer than 30" in contract["primary_analysis"]["small_cluster_rule"], "minimum cluster rule missing")
    prohibited = "\n".join(contract["selection_prohibitions"]).lower()
    for phrase in ["best dev", "change sesoi", "change alpha", "drop difficult", "replace final endpoint"]:
        require(phrase in prohibited, f"selection prohibition missing: {phrase}")
    authorization = contract["confirmatory_authorization"]
    require(authorization["holdout_access"] is False, "HOLDOUT must remain unauthorized")
    require(authorization["replication_access"] is False, "REPLICATION must remain unauthorized")
    require(authorization["requires_independent_statistical_review"] is True, "independent statistics review not required")
    return contract


def validate_power_scenarios():
    scenarios = load_json("POWER_SCENARIOS.json")
    primary = scenarios["primary_planning"]
    expected = {
        "delta": 0.08,
        "discordance_q": 0.35,
        "mean_cluster_size": 8,
        "icc": 0.05,
        "attrition": 0.05,
        "alpha_two_sided": 0.05,
        "target_power": 0.90,
        "expected_minimum_eligible_n": 802,
        "minimum_clusters": 30,
    }
    require(primary == expected, f"primary planning scenario drift: {primary}")
    axes = scenarios["sensitivity_axes"]
    require(axes["delta"] == [0.05, 0.08, 0.10], "delta sensitivity drift")
    require(axes["discordance_q"] == [0.20, 0.35, 0.50], "discordance sensitivity drift")
    require(axes["mean_cluster_size"] == [4, 8, 12], "cluster-size sensitivity drift")
    require(axes["icc"] == [0.00, 0.05, 0.10], "ICC sensitivity drift")
    require(axes["attrition"] == [0.00, 0.05, 0.10], "attrition sensitivity drift")
    require(802 in scenarios["candidate_n_grid"], "required N missing from candidate grid")
    return scenarios


def validate_calculator(scenarios):
    calc = load_module("wp006_calculate_power", PROTO / "calculate_power.py")
    primary = dict(scenarios["primary_planning"])
    expected_n = primary.pop("expected_minimum_eligible_n")
    primary.pop("minimum_clusters")
    required_n = calc.minimum_n(
        primary["delta"], primary["discordance_q"], primary["mean_cluster_size"],
        primary["icc"], primary["attrition"], primary["alpha_two_sided"], primary["target_power"]
    )
    require(required_n == expected_n == 802, f"calculated minimum N drift: {required_n}")
    p802 = calc.power_for_n(
        802, primary["delta"], primary["discordance_q"], primary["mean_cluster_size"],
        primary["icc"], primary["attrition"], primary["alpha_two_sided"]
    )
    p801 = calc.power_for_n(
        801, primary["delta"], primary["discordance_q"], primary["mean_cluster_size"],
        primary["icc"], primary["attrition"], primary["alpha_two_sided"]
    )
    require(p802 >= 0.90, f"N=802 does not reach 90% power: {p802}")
    require(p801 < 0.90, f"N=801 unexpectedly reaches 90% power: {p801}")
    require(0.899 <= p801 < p802 <= 0.902, "primary boundary power unexpectedly far from threshold")
    return p801, p802


def validate_blinded_update():
    protocol = load_json("BLINDED_NUISANCE_UPDATE_PROTOCOL.json")
    allowed = set(protocol["allowed_inputs"])
    forbidden = set(protocol["forbidden_inputs"])
    require("paired disagreement indicator without direction" in allowed, "non-directional discordance missing")
    require("signed treatment-minus-control difference" in forbidden, "signed treatment difference not forbidden")
    require("arm-labelled correctness rates" in forbidden, "arm-labelled rates not forbidden")
    require("HOLDOUT" in forbidden and "REPLICATION" in forbidden, "sealed splits not forbidden")
    immutable = protocol["immutable_parameters"]
    require(immutable["se_soi_absolute"] == 0.08, "blinded update may change SESOI")
    require(immutable["alpha_two_sided"] == 0.05, "blinded update may change alpha")
    require(immutable["target_power"] == 0.90, "blinded update may change target power")
    require(protocol["blinding"]["direction_removed_before_analyst"] is True, "direction is not removed before analyst")
    require(protocol["blinding"]["analyst_must_not_receive_mapping"] is True, "analyst may receive arm mapping")
    require(protocol["decision_rule"]["recalculate_required_n_once"] is True, "multiple nuisance updates allowed")
    require("POWER_GATE_FAIL" in protocol["decision_rule"]["if_available_confirmatory_cases_below_required_n"], "underpowered inventory does not fail gate")


def validate_simulation_contract():
    text = (ROOT / "SIMULATION_PROTOCOL.md").read_text(encoding="utf-8")
    for phrase in [
        "repetitions: `20000`",
        "seed: `158006`",
        "primary eligible N: `802`",
        "ICC exactly `rho`",
        "<= .02",
        "no seed shopping",
    ]:
        require(phrase.lower() in text.lower(), f"simulation protocol missing: {phrase}")
    source = (PROTO / "simulate_power.py").read_text(encoding="utf-8")
    require("random.Random(seed)" in source, "simulation seed not explicit")
    require("shared = rng.random() < icc" in source, "exact-ICC shared cluster construction missing")
    require("crosscheck_tolerance\"] = 0.02" in source, "simulation analytical-gap tolerance drift")
    require("--repetitions" in source and "default=20000" in source, "simulation repetition count drift")
    require("--seed" in source and "default=158006" in source, "simulation seed drift")


def validate_docs():
    protocol = (ROOT / "POWER_ANALYSIS_PROTOCOL.md").read_text(encoding="utf-8")
    missingness = (ROOT / "MULTIPLICITY_AND_MISSINGNESS.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for phrase in [
        "δ_SESOI = +0.08",
        "two-sided alpha: `0.05`",
        "target power at the SESOI: `0.90`",
        "N = 802",
        "at least 30 independent source-family clusters",
        "best DEV arm",
        "STOP before HOLDOUT",
    ]:
        require(phrase.lower() in protocol.lower(), f"power protocol missing: {phrase}")
    for phrase in ["Holm", "5%", "not ordinary missing data", "no optional stopping"]:
        require(phrase.lower() in missingness.lower(), f"missingness/multiplicity contract missing: {phrase}")
    require("802 eligible paired cases" in readme, "README required N cross-check missing")


def main():
    required_files = [
        "README.md",
        "POWER_ANALYSIS_PROTOCOL.md",
        "PRIMARY_ANALYSIS_CONTRACT.json",
        "POWER_SCENARIOS.json",
        "BLINDED_NUISANCE_UPDATE_PROTOCOL.json",
        "MULTIPLICITY_AND_MISSINGNESS.md",
        "SIMULATION_PROTOCOL.md",
        "prototype/calculate_power.py",
        "prototype/simulate_power.py",
    ]
    for name in required_files:
        require((ROOT / name).is_file(), f"missing WP-006 artifact: {name}")

    validate_primary_contract()
    scenarios = validate_power_scenarios()
    p801, p802 = validate_calculator(scenarios)
    validate_blinded_update()
    validate_simulation_contract()
    validate_docs()

    print(json.dumps({
        "work_package": "WP-006",
        "contract": "PASS",
        "primary_sesoi": 0.08,
        "alpha_two_sided": 0.05,
        "target_power": 0.90,
        "required_eligible_n": 802,
        "power_at_801": p801,
        "power_at_802": p802,
        "minimum_clusters": 30,
        "github_actions_required": False,
        "independent_statistical_review": "NOT_PERFORMED_BY_THIS_VALIDATOR",
        "holdout": "NOT_AUTHORIZED"
    }, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"WP-006 contract validation failed: {exc}", file=sys.stderr)
        raise
