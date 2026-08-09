#!/usr/bin/env python3
import argparse
import itertools
import json
import math
from statistics import NormalDist
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_PATH = ROOT / "POWER_SCENARIOS.json"


def validate_inputs(delta, q, mean_cluster_size, icc, attrition, alpha, target_power):
    if not 0 < abs(delta) < 1:
        raise ValueError("delta must be in (-1,1) excluding zero")
    if not abs(delta) <= q <= 1:
        raise ValueError("discordance q must satisfy |delta| <= q <= 1")
    if mean_cluster_size < 1:
        raise ValueError("mean_cluster_size must be >= 1")
    if not 0 <= icc < 1:
        raise ValueError("icc must be in [0,1)")
    if not 0 <= attrition < 1:
        raise ValueError("attrition must be in [0,1)")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0,1)")
    if not 0 < target_power < 1:
        raise ValueError("target_power must be in (0,1)")
    if q - delta * delta <= 0:
        raise ValueError("paired difference variance must be positive")


def power_for_n(n, delta, q, mean_cluster_size, icc, attrition, alpha):
    validate_inputs(delta, q, mean_cluster_size, icc, attrition, alpha, 0.5)
    design_effect = 1.0 + (mean_cluster_size - 1.0) * icc
    effective_n = n * (1.0 - attrition) / design_effect
    variance = q - delta * delta
    mu = abs(delta) * math.sqrt(effective_n / variance)
    normal = NormalDist()
    zcrit = normal.inv_cdf(1.0 - alpha / 2.0)
    return normal.cdf(-zcrit - mu) + 1.0 - normal.cdf(zcrit - mu)


def minimum_n(delta, q, mean_cluster_size, icc, attrition, alpha, target_power, max_n=1_000_000):
    validate_inputs(delta, q, mean_cluster_size, icc, attrition, alpha, target_power)
    lo, hi = 2, 2
    while hi <= max_n and power_for_n(hi, delta, q, mean_cluster_size, icc, attrition, alpha) < target_power:
        hi *= 2
    if hi > max_n:
        hi = max_n
        if power_for_n(hi, delta, q, mean_cluster_size, icc, attrition, alpha) < target_power:
            raise RuntimeError("required N exceeds max_n")
    while lo < hi:
        mid = (lo + hi) // 2
        if power_for_n(mid, delta, q, mean_cluster_size, icc, attrition, alpha) >= target_power:
            hi = mid
        else:
            lo = mid + 1
    return lo


def scenario_result(values):
    required = minimum_n(
        values["delta"], values["discordance_q"], values["mean_cluster_size"],
        values["icc"], values["attrition"], values["alpha_two_sided"], values["target_power"]
    )
    design_effect = 1.0 + (values["mean_cluster_size"] - 1.0) * values["icc"]
    return {
        **values,
        "design_effect": design_effect,
        "required_eligible_n": required,
        "power_at_required_n": power_for_n(
            required, values["delta"], values["discordance_q"], values["mean_cluster_size"],
            values["icc"], values["attrition"], values["alpha_two_sided"]
        ),
        "power_at_previous_n": power_for_n(
            required - 1, values["delta"], values["discordance_q"], values["mean_cluster_size"],
            values["icc"], values["attrition"], values["alpha_two_sided"]
        ) if required > 2 else None,
        "approximate_clusters_at_required_n": math.ceil(required / values["mean_cluster_size"]),
    }


def main():
    parser = argparse.ArgumentParser(description="WP-006 outcome-blind paired/clustered power calculator")
    parser.add_argument("--sensitivity", action="store_true", help="Emit full frozen sensitivity grid")
    parser.add_argument("--eligible-n", type=int, help="Also compute primary-scenario power at this frozen eligible N")
    args = parser.parse_args()

    doc = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    primary = dict(doc["primary_planning"])
    expected = primary.pop("expected_minimum_eligible_n")
    minimum_clusters = primary.pop("minimum_clusters")
    result = scenario_result(primary)
    if result["required_eligible_n"] != expected:
        raise RuntimeError(
            f"primary expected N drift: calculated {result['required_eligible_n']}, manifest says {expected}"
        )

    output = {
        "schema_version": "1.0.0",
        "work_package_id": "WP-006",
        "planning_method": doc["method"],
        "primary": result,
        "minimum_independent_clusters": minimum_clusters,
        "primary_gate_required_eligible_n": expected,
    }

    if args.eligible_n is not None:
        if args.eligible_n < 1:
            raise ValueError("eligible-n must be positive")
        output["frozen_inventory_check"] = {
            "eligible_n": args.eligible_n,
            "power": power_for_n(
                args.eligible_n, primary["delta"], primary["discordance_q"],
                primary["mean_cluster_size"], primary["icc"], primary["attrition"],
                primary["alpha_two_sided"]
            ),
            "n_gate_pass": args.eligible_n >= expected,
        }

    if args.sensitivity:
        axes = doc["sensitivity_axes"]
        rows = []
        for delta, q, m, icc, attrition in itertools.product(
            axes["delta"], axes["discordance_q"], axes["mean_cluster_size"], axes["icc"], axes["attrition"]
        ):
            if q < abs(delta) or q - delta * delta <= 0:
                continue
            rows.append(scenario_result({
                "delta": delta,
                "discordance_q": q,
                "mean_cluster_size": m,
                "icc": icc,
                "attrition": attrition,
                "alpha_two_sided": primary["alpha_two_sided"],
                "target_power": primary["target_power"],
            }))
        output["sensitivity"] = rows

    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
