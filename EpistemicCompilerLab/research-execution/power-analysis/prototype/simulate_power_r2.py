#!/usr/bin/env python3
"""WP-006 R2 clustered paired Monte-Carlo power and Type-I calibration.

This is a planning simulator for base_scenario_id-level publication-composite outcomes.
It is deliberately not fitted to sealed outcomes. It includes frozen domain/model
heterogeneity, source-family dependence, explicit scored failures, CR1 inference with
Student-t reference, independent HOLDOUT/REPLICATION draws, and Monte-Carlo
uncertainty gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "R2_SIMULATION_SCENARIOS.json"
REQUIREMENTS_PATH = ROOT / "requirements-r2.txt"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_config() -> dict[str, Any]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    require(config["analysis_unit"] == "base_scenario_id", "R2 analysis unit drift")
    require(config["endpoint"] == "publication_composite_correctness", "R2 endpoint drift")
    require(config["power_search"]["seed_shopping"] is False, "seed shopping must be forbidden")
    return config


def wilson_interval(successes: int, trials: int, confidence: float = 0.95) -> tuple[float, float]:
    require(0 <= successes <= trials and trials > 0, "invalid Wilson inputs")
    # One-sided 95% bound, as frozen in R2_SIMULATION_SCENARIOS.json.
    z = float(stats.norm.ppf(confidence))
    phat = successes / trials
    z2 = z * z
    denom = 1.0 + z2 / trials
    center = (phat + z2 / (2.0 * trials)) / denom
    half = z * math.sqrt(phat * (1.0 - phat) / trials + z2 / (4.0 * trials * trials)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def cluster_sizes(n: int, target: int) -> np.ndarray:
    require(n >= 1 and target >= 1, "invalid N/cluster size")
    full, remainder = divmod(n, target)
    sizes = [target] * full
    if remainder:
        sizes.append(remainder)
    return np.asarray(sizes, dtype=np.int64)


def stratum_records(config: dict[str, Any], average_final_delta: float, null: bool) -> list[dict[str, float | str]]:
    paired = config["paired_semantic_generator"]
    failure = config["failure_generator"]
    domains = config["strata"]["domains"]
    models = config["strata"]["model_profiles"]
    records: list[dict[str, float | str]] = []

    for domain in domains:
        for model in models:
            p0 = paired["base_control_accuracy"] + domain["control_accuracy_offset"] + model["control_accuracy_offset"]
            q = paired["base_discordance_q"] + domain["discordance_offset"] + model["discordance_offset"]
            final_delta = 0.0 if null else average_final_delta + domain["final_delta_offset"] + model["final_delta_offset"]
            multiplier = domain["failure_multiplier"] * model["failure_multiplier"]
            fail_t = failure["treatment_case_failure_probability_base"] * multiplier
            fail_c = failure["control_case_failure_probability_base"] * multiplier
            cluster_fail = failure["source_family_catastrophic_failure_probability"]
            common_fail = failure["scenario_common_failure_probability"]
            common_survival = (1.0 - cluster_fail) * (1.0 - common_fail)

            # Solve the latent treatment success probability so the FINAL expected
            # difference after explicit scored failures equals final_delta.
            p1 = (final_delta / common_survival + (1.0 - fail_c) * p0) / (1.0 - fail_t)
            latent_delta = p1 - p0
            p10 = (q + latent_delta) / 2.0
            p01 = (q - latent_delta) / 2.0
            p11 = p0 - p01
            p00 = 1.0 - p11 - p10 - p01
            probabilities = [p11, p10, p01, p00]
            require(all(-1e-12 <= value <= 1.0 + 1e-12 for value in probabilities), f"invalid paired probabilities for {domain['id']}/{model['id']}: {probabilities}")
            require(abs(sum(probabilities) - 1.0) < 1e-10, "paired probabilities do not sum to one")
            require(q >= abs(latent_delta) - 1e-12, "discordance smaller than latent delta")
            expected_final_t = common_survival * (1.0 - fail_t) * p1
            expected_final_c = common_survival * (1.0 - fail_c) * p0
            require(abs((expected_final_t - expected_final_c) - final_delta) < 1e-12, "post-failure delta calibration failed")

            records.append({
                "domain_id": domain["id"],
                "model_id": model["id"],
                "p11": p11,
                "p10": p10,
                "p01": p01,
                "p00": p00,
                "p0": p0,
                "p1": p1,
                "q": q,
                "latent_delta": latent_delta,
                "target_final_delta": final_delta,
                "treatment_failure": fail_t,
                "control_failure": fail_c,
            })
    require(len(records) == 12, "expected exactly 12 domain-model strata")
    return records


def layout(config: dict[str, Any], n: int) -> dict[str, np.ndarray | int]:
    target = int(config["clustering"]["mean_source_family_cluster_size"])
    sizes = cluster_sizes(n, target)
    g = len(sizes)
    cluster_stratum = np.arange(g, dtype=np.int64) % 12
    cluster_ids = np.repeat(np.arange(g, dtype=np.int64), sizes)
    scenario_stratum = cluster_stratum[cluster_ids]
    starts = np.concatenate(([0], np.cumsum(sizes)[:-1])).astype(np.int64)
    require(len(cluster_ids) == n, "layout N drift")
    return {
        "sizes": sizes,
        "g": g,
        "cluster_stratum": cluster_stratum,
        "cluster_ids": cluster_ids,
        "scenario_stratum": scenario_stratum,
        "starts": starts,
    }


def categorical_pair(u: np.ndarray, p11: np.ndarray, p10: np.ndarray, p01: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    cut11 = p11
    cut10 = p11 + p10
    cut01 = cut10 + p01
    treatment = u < cut10
    control = (u < cut11) | ((u >= cut10) & (u < cut01))
    return treatment, control


def draw_dataset(
    rng: np.random.Generator,
    config: dict[str, Any],
    n: int,
    records: list[dict[str, float | str]],
    batch: int,
) -> tuple[np.ndarray, np.ndarray, int]:
    info = layout(config, n)
    sizes = info["sizes"]
    g = int(info["g"])
    cluster_stratum = info["cluster_stratum"]
    cluster_ids = info["cluster_ids"]
    scenario_stratum = info["scenario_stratum"]
    starts = info["starts"]

    p11_s = np.asarray([float(row["p11"]) for row in records], dtype=np.float64)
    p10_s = np.asarray([float(row["p10"]) for row in records], dtype=np.float64)
    p01_s = np.asarray([float(row["p01"]) for row in records], dtype=np.float64)
    fail_t_s = np.asarray([float(row["treatment_failure"]) for row in records], dtype=np.float64)
    fail_c_s = np.asarray([float(row["control_failure"]) for row in records], dtype=np.float64)

    # Independent paired semantic outcomes per scenario.
    u = rng.random((batch, n))
    independent_t, independent_c = categorical_pair(
        u,
        p11_s[scenario_stratum][None, :],
        p10_s[scenario_stratum][None, :],
        p01_s[scenario_stratum][None, :],
    )

    # Source-family mixture component. When active, a shared paired outcome is
    # reused across all base scenarios in the cluster. This preserves the frozen
    # marginal stratum distribution while introducing family-level dependence.
    rho = float(config["paired_semantic_generator"]["source_family_shared_pair_mixture_probability"])
    shared_active = rng.random((batch, g)) < rho
    shared_u = rng.random((batch, g))
    shared_t, shared_c = categorical_pair(
        shared_u,
        p11_s[cluster_stratum][None, :],
        p10_s[cluster_stratum][None, :],
        p01_s[cluster_stratum][None, :],
    )
    active_scenario = shared_active[:, cluster_ids]
    treatment = np.where(active_scenario, shared_t[:, cluster_ids], independent_t)
    control = np.where(active_scenario, shared_c[:, cluster_ids], independent_c)

    failure = config["failure_generator"]
    catastrophic = rng.random((batch, g)) < float(failure["source_family_catastrophic_failure_probability"])
    common = rng.random((batch, n)) < float(failure["scenario_common_failure_probability"])
    t_fail = rng.random((batch, n)) < fail_t_s[scenario_stratum][None, :]
    c_fail = rng.random((batch, n)) < fail_c_s[scenario_stratum][None, :]
    blocked = catastrophic[:, cluster_ids] | common
    treatment = treatment & ~blocked & ~t_fail
    control = control & ~blocked & ~c_fail

    d = treatment.astype(np.int8) - control.astype(np.int8)
    estimate = d.mean(axis=1, dtype=np.float64)
    cluster_sums = np.add.reduceat(d.astype(np.float64), starts, axis=1)
    residual_sums = cluster_sums - estimate[:, None] * sizes[None, :]
    variance = (g / (g - 1.0)) * np.sum(residual_sums * residual_sums, axis=1) / (n * n)
    se = np.sqrt(np.maximum(variance, 0.0))
    t_stat = np.zeros(batch, dtype=np.float64)
    nonzero = se > 0
    t_stat[nonzero] = estimate[nonzero] / se[nonzero]
    t_stat[~nonzero & (estimate > 0)] = np.inf
    t_stat[~nonzero & (estimate < 0)] = -np.inf
    p_value = np.ones(batch, dtype=np.float64)
    p_value[nonzero] = 2.0 * stats.t.sf(np.abs(t_stat[nonzero]), df=g - 1)
    p_value[~nonzero & (estimate != 0)] = 0.0
    return estimate, p_value, g


def simulate_joint(
    config: dict[str, Any],
    n: int,
    average_final_delta: float,
    repetitions: int,
    seed: int,
    batch_size: int,
) -> dict[str, Any]:
    records = stratum_records(config, average_final_delta, null=False)
    rng_holdout = np.random.default_rng(np.random.SeedSequence([seed, n, 1]))
    rng_replication = np.random.default_rng(np.random.SeedSequence([seed, n, 2]))
    holdout_success = 0
    replication_positive = 0
    replication_significant = 0
    joint_success = 0
    sum_holdout_estimate = 0.0
    sum_replication_estimate = 0.0
    g_seen: int | None = None

    done = 0
    while done < repetitions:
        batch = min(batch_size, repetitions - done)
        h_est, h_p, g_h = draw_dataset(rng_holdout, config, n, records, batch)
        r_est, r_p, g_r = draw_dataset(rng_replication, config, n, records, batch)
        require(g_h == g_r, "HOLDOUT/REPLICATION cluster-count drift")
        g_seen = g_h
        h_ok = (h_est > 0.0) & (h_p < 0.05)
        r_pos = r_est > 0.0
        r_sig = r_pos & (r_p < 0.05)
        joint = h_ok & r_pos
        holdout_success += int(np.count_nonzero(h_ok))
        replication_positive += int(np.count_nonzero(r_pos))
        replication_significant += int(np.count_nonzero(r_sig))
        joint_success += int(np.count_nonzero(joint))
        sum_holdout_estimate += float(np.sum(h_est))
        sum_replication_estimate += float(np.sum(r_est))
        done += batch

    lower, upper = wilson_interval(joint_success, repetitions)
    h_lower, h_upper = wilson_interval(holdout_success, repetitions)
    return {
        "eligible_n": n,
        "independent_source_family_clusters": g_seen,
        "average_target_final_delta": average_final_delta,
        "repetitions": repetitions,
        "seed": seed,
        "holdout_success_probability": holdout_success / repetitions,
        "holdout_success_wilson_one_sided_95_lower": h_lower,
        "holdout_success_wilson_one_sided_95_upper": h_upper,
        "replication_positive_probability": replication_positive / repetitions,
        "replication_significant_positive_probability": replication_significant / repetitions,
        "joint_success_probability": joint_success / repetitions,
        "joint_success_wilson_one_sided_95_lower": lower,
        "joint_success_wilson_one_sided_95_upper": upper,
        "mean_holdout_estimate": sum_holdout_estimate / repetitions,
        "mean_replication_estimate": sum_replication_estimate / repetitions,
    }


def simulate_type_i(config: dict[str, Any], repetitions: int, seed: int, batch_size: int) -> dict[str, Any]:
    settings = config["type_I_calibration"]
    n = int(settings["eligible_n"])
    records = stratum_records(config, 0.0, null=True)
    rng = np.random.default_rng(np.random.SeedSequence([seed, n, 0]))
    false_positives = 0
    positive_false_positives = 0
    sum_estimate = 0.0
    g_seen: int | None = None
    done = 0
    while done < repetitions:
        batch = min(batch_size, repetitions - done)
        estimate, p_value, g = draw_dataset(rng, config, n, records, batch)
        g_seen = g
        reject = p_value < 0.05
        false_positives += int(np.count_nonzero(reject))
        positive_false_positives += int(np.count_nonzero(reject & (estimate > 0.0)))
        sum_estimate += float(np.sum(estimate))
        done += batch
    lower, upper = wilson_interval(false_positives, repetitions)
    return {
        "eligible_n": n,
        "independent_source_family_clusters": g_seen,
        "repetitions": repetitions,
        "seed": seed,
        "two_sided_false_positive_probability": false_positives / repetitions,
        "two_sided_false_positive_wilson_one_sided_95_lower": lower,
        "two_sided_false_positive_wilson_one_sided_95_upper": upper,
        "positive_direction_false_positive_probability": positive_false_positives / repetitions,
        "mean_estimate": sum_estimate / repetitions,
        "acceptance_upper_bound_max": 0.055,
        "type_I_gate_pass": upper <= 0.055,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--repetitions", type=int, help="Override power repetitions for diagnostic runs only")
    parser.add_argument("--type-i-repetitions", type=int, help="Override Type-I repetitions for diagnostic runs only")
    parser.add_argument("--allow-diagnostic-overrides", action="store_true")
    args = parser.parse_args()
    if (args.repetitions is not None or args.type_i_repetitions is not None) and not args.allow_diagnostic_overrides:
        raise RuntimeError("repetition overrides require --allow-diagnostic-overrides and are not acceptance evidence")

    config = load_config()
    search = config["power_search"]
    alt = config["primary_alternative"]
    repetitions = int(args.repetitions or search["repetitions_per_candidate"])
    type_i_repetitions = int(args.type_i_repetitions or config["type_I_calibration"]["repetitions"])
    acceptance_evidence = args.repetitions is None and args.type_i_repetitions is None

    type_i = simulate_type_i(config, type_i_repetitions, int(config["type_I_calibration"]["seed"]), args.batch_size)
    require(type_i["independent_source_family_clusters"] == config["type_I_calibration"]["independent_source_family_clusters"], "Type-I cluster boundary drift")

    rows: list[dict[str, Any]] = []
    selected: dict[str, Any] | None = None
    for n in search["candidate_eligible_n_grid"]:
        row = simulate_joint(
            config,
            int(n),
            float(alt["average_final_delta"]),
            repetitions,
            int(search["seed"]),
            args.batch_size,
        )
        row["joint_lower_bound_gate_pass"] = row["joint_success_wilson_one_sided_95_lower"] >= float(alt["joint_success_probability_target"])
        rows.append(row)
        if selected is None and int(n) >= int(search["non_decreasing_floor"]) and row["joint_lower_bound_gate_pass"]:
            selected = row
            break

    # Sensitivity is descriptive at the selected N. It never changes the 0.08 gate.
    sensitivity: list[dict[str, Any]] = []
    if selected is not None:
        sensitivity_repetitions = min(repetitions, 10000)
        for index, delta in enumerate(config["sensitivity"]["SESOI_delta_values"]):
            sensitivity.append(simulate_joint(
                config,
                int(selected["eligible_n"]),
                float(delta),
                sensitivity_repetitions,
                int(search["seed"]) + 100 + index,
                args.batch_size,
            ))

    result = {
        "schema_version": "1.0.0",
        "work_package_id": "WP-006",
        "simulation_id": config["simulation_id"],
        "evidence_class": "ACCEPTANCE_CANDIDATE" if acceptance_evidence else "DIAGNOSTIC_ONLY",
        "config_sha256": sha256_file(CONFIG_PATH),
        "requirements_sha256": sha256_file(REQUIREMENTS_PATH),
        "analysis_unit": "base_scenario_id",
        "type_I_calibration": type_i,
        "power_search": rows,
        "selected_R2_grid_floor": int(selected["eligible_n"]) if selected is not None else None,
        "selected_joint_lower_bound": selected["joint_success_wilson_one_sided_95_lower"] if selected is not None else None,
        "non_decreasing_floor": int(search["non_decreasing_floor"]),
        "sensitivity_at_selected_n": sensitivity,
        "acceptance_conditions": {
            "type_I_upper_bound_le_0_055": bool(type_i["type_I_gate_pass"]),
            "joint_power_lower_bound_ge_0_90": bool(selected is not None),
            "selected_n_not_below_802": bool(selected is not None and int(selected["eligible_n"]) >= 802),
            "final_N_accepted_by_independent_review": False,
            "WP004_exact_arm_binding_accepted": False,
            "WP005_scorer_accepted": False,
            "WP007_feasibility_accepted": False,
            "HOLDOUT_or_REPLICATION_accessed": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if acceptance_evidence and (not type_i["type_I_gate_pass"] or selected is None):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
