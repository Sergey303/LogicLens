#!/usr/bin/env python3
import argparse
import json
import math
import random
from statistics import NormalDist
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS_PATH = ROOT / "POWER_SCENARIOS.json"


def draw_d(rng, delta, q):
    p_plus = (q + delta) / 2.0
    p_minus = (q - delta) / 2.0
    u = rng.random()
    if u < p_plus:
        return 1
    if u < p_plus + p_minus:
        return -1
    return 0


def cluster_sizes(n, mean_cluster_size):
    base = int(mean_cluster_size)
    if base < 1 or abs(mean_cluster_size - base) > 1e-12:
        raise ValueError("simulation currently requires integer mean_cluster_size")
    full, rem = divmod(n, base)
    sizes = [base] * full
    if rem:
        sizes.append(rem)
    return sizes


def one_replicate(rng, n, delta, q, mean_cluster_size, icc, attrition, zcrit):
    observed = []
    for cluster_id, size in enumerate(cluster_sizes(n, mean_cluster_size)):
        shared = rng.random() < icc
        shared_d = draw_d(rng, delta, q) if shared else None
        values = []
        for _ in range(size):
            d = shared_d if shared else draw_d(rng, delta, q)
            if rng.random() >= attrition:
                values.append(d)
        if values:
            observed.append((cluster_id, values))

    g = len(observed)
    n_obs = sum(len(values) for _, values in observed)
    if g < 2 or n_obs < 2:
        return False, True, n_obs, g, 0.0

    total = sum(sum(values) for _, values in observed)
    estimate = total / n_obs
    residual_cluster_sums = [sum(value - estimate for value in values) for _, values in observed]
    variance = (g / (g - 1.0)) * sum(s * s for s in residual_cluster_sums) / (n_obs * n_obs)

    if variance <= 0.0:
        # Degenerate all-identical replicate. Preserve it explicitly rather than
        # divide by zero or silently exclude it.
        return estimate != 0.0, True, n_obs, g, estimate

    se = math.sqrt(variance)
    z = estimate / se
    return abs(z) > zcrit, False, n_obs, g, estimate


def simulate(repetitions, seed, n, delta, q, mean_cluster_size, icc, attrition, alpha):
    if repetitions < 100:
        raise ValueError("repetitions must be >= 100")
    if not abs(delta) <= q <= 1:
        raise ValueError("q must satisfy |delta| <= q <= 1")
    if not 0 <= icc < 1:
        raise ValueError("icc must be in [0,1)")
    if not 0 <= attrition < 1:
        raise ValueError("attrition must be in [0,1)")

    rng = random.Random(seed)
    zcrit = NormalDist().inv_cdf(1.0 - alpha / 2.0)
    rejects = 0
    degenerate = 0
    sum_n_obs = 0
    sum_clusters = 0
    sum_estimate = 0.0

    for _ in range(repetitions):
        reject, was_degenerate, n_obs, g, estimate = one_replicate(
            rng, n, delta, q, mean_cluster_size, icc, attrition, zcrit
        )
        rejects += int(reject)
        degenerate += int(was_degenerate)
        sum_n_obs += n_obs
        sum_clusters += g
        sum_estimate += estimate

    power = rejects / repetitions
    mc_se = math.sqrt(power * (1.0 - power) / repetitions)
    return {
        "repetitions": repetitions,
        "seed": seed,
        "eligible_n": n,
        "delta": delta,
        "discordance_q": q,
        "mean_cluster_size": mean_cluster_size,
        "icc": icc,
        "attrition": attrition,
        "alpha_two_sided": alpha,
        "simulated_power": power,
        "monte_carlo_se": mc_se,
        "degenerate_replicates": degenerate,
        "mean_observed_n": sum_n_obs / repetitions,
        "mean_observed_clusters": sum_clusters / repetitions,
        "mean_estimate": sum_estimate / repetitions,
    }


def analytical_power(n, delta, q, mean_cluster_size, icc, attrition, alpha):
    design_effect = 1.0 + (mean_cluster_size - 1.0) * icc
    effective_n = n * (1.0 - attrition) / design_effect
    variance = q - delta * delta
    mu = abs(delta) * math.sqrt(effective_n / variance)
    normal = NormalDist()
    zcrit = normal.inv_cdf(1.0 - alpha / 2.0)
    return normal.cdf(-zcrit - mu) + 1.0 - normal.cdf(zcrit - mu)


def main():
    parser = argparse.ArgumentParser(description="WP-006 exact-ICC cluster Monte-Carlo power stress check")
    parser.add_argument("--repetitions", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=158006)
    parser.add_argument("--eligible-n", type=int)
    args = parser.parse_args()

    scenarios = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    primary = scenarios["primary_planning"]
    n = args.eligible_n if args.eligible_n is not None else primary["expected_minimum_eligible_n"]

    result = simulate(
        args.repetitions,
        args.seed,
        n,
        primary["delta"],
        primary["discordance_q"],
        primary["mean_cluster_size"],
        primary["icc"],
        primary["attrition"],
        primary["alpha_two_sided"],
    )
    analytic = analytical_power(
        n,
        primary["delta"],
        primary["discordance_q"],
        primary["mean_cluster_size"],
        primary["icc"],
        primary["attrition"],
        primary["alpha_two_sided"],
    )
    result["analytical_power"] = analytic
    result["absolute_simulation_analytic_gap"] = abs(result["simulated_power"] - analytic)
    result["crosscheck_tolerance"] = 0.02
    result["crosscheck_pass"] = result["absolute_simulation_analytic_gap"] <= 0.02
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
