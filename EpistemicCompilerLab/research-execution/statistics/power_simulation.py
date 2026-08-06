#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from pathlib import Path
from typing import Any

import numpy as np
import scipy
import yaml
from scipy.stats import binom, chi2


def logistic(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def majority_probability(p: np.ndarray, repeats: int, required: int) -> np.ndarray:
    result = np.zeros_like(p, dtype=float)
    for k in range(required, repeats + 1):
        result += math.comb(repeats, k) * np.power(p, k) * np.power(1.0 - p, repeats - k)
    return result


def balanced_indices(n: int, levels: int, rng: np.random.Generator) -> np.ndarray:
    values = np.arange(n, dtype=int) % levels
    rng.shuffle(values)
    return values


def latent_sample(cfg: dict[str, Any], n: int, rng: np.random.Generator) -> tuple[np.ndarray, ...]:
    domain_offsets = np.asarray(cfg["domain_baseline_logit_offsets"], dtype=float)
    model_offsets = np.asarray(cfg["model_baseline_logit_offsets"], dtype=float)
    domain_treatment = np.asarray(cfg["domain_treatment_logit_offsets"], dtype=float)
    model_treatment = np.asarray(cfg["model_treatment_logit_offsets"], dtype=float)
    domains = balanced_indices(n, len(domain_offsets), rng)
    models = balanced_indices(n, len(model_offsets), rng)
    scenario = rng.normal(0.0, float(cfg["scenario_logit_sd"]), size=n)
    treatment_random = rng.normal(0.0, float(cfg["treatment_heterogeneity_logit_sd"]), size=n)
    paraphrase = rng.normal(0.0, float(cfg["paraphrase_logit_sd"]), size=(n, int(cfg["paraphrases_per_scenario"])))
    baseline_logit = (
        float(cfg["baseline_logit_intercept"])
        + domain_offsets[domains, None]
        + model_offsets[models, None]
        + scenario[:, None]
        + paraphrase
    )
    treatment_extra = domain_treatment[domains] + model_treatment[models] + treatment_random
    return baseline_logit, treatment_extra, domains, models


def expected_scenario_rates(
    cfg: dict[str, Any], baseline_logit: np.ndarray, treatment_extra: np.ndarray, shift: float
) -> tuple[float, float]:
    failure_rate = float(cfg["run_failure_rate"])
    repeats = int(cfg["repeats_per_paraphrase"])
    required = int(cfg["repeat_majority_required"])
    pb = logistic(baseline_logit) * (1.0 - failure_rate)
    pt = logistic(baseline_logit + treatment_extra[:, None] + shift) * (1.0 - failure_rate)
    qb = majority_probability(pb, repeats, required)
    qt = majority_probability(pt, repeats, required)
    sb = np.prod(qb, axis=1)
    st = np.prod(qt, axis=1)
    return float(np.mean(sb)), float(np.mean(st))


def calibrate_shift(cfg: dict[str, Any], seed: int) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    n = int(cfg["calibration_scenarios"])
    baseline_logit, treatment_extra, _, _ = latent_sample(cfg, n, rng)
    target = float(cfg["target_absolute_scenario_gain"])
    low, high = -0.5, 1.5
    for _ in range(50):
        mid = (low + high) / 2.0
        base, treated = expected_scenario_rates(cfg, baseline_logit, treatment_extra, mid)
        if treated - base < target:
            low = mid
        else:
            high = mid
    shift = (low + high) / 2.0
    base, treated = expected_scenario_rates(cfg, baseline_logit, treatment_extra, shift)
    return {
        "treatment_logit_shift": shift,
        "expected_baseline_scenario_accuracy": base,
        "expected_treatment_scenario_accuracy": treated,
        "expected_absolute_gain": treated - base,
    }


def evaluate_power(cfg: dict[str, Any], shift: float, seed: int) -> list[dict[str, Any]]:
    rng = np.random.default_rng(seed)
    simulations = int(cfg["simulations_per_candidate"])
    batch_size = int(cfg.get("simulation_batch_size", 100))
    repeats = int(cfg["repeats_per_paraphrase"])
    required = int(cfg["repeat_majority_required"])
    paraphrases = int(cfg["paraphrases_per_scenario"])
    failure_rate = float(cfg["run_failure_rate"])
    domain_offsets = np.asarray(cfg["domain_baseline_logit_offsets"], dtype=float)
    model_offsets = np.asarray(cfg["model_baseline_logit_offsets"], dtype=float)
    domain_treatment = np.asarray(cfg["domain_treatment_logit_offsets"], dtype=float)
    model_treatment = np.asarray(cfg["model_treatment_logit_offsets"], dtype=float)
    rows: list[dict[str, Any]] = []
    for n_value in cfg["candidate_scenario_counts"]:
        n = int(n_value)
        domains = np.arange(n, dtype=int) % len(domain_offsets)
        models = (np.arange(n, dtype=int) // len(domain_offsets)) % len(model_offsets)
        detections: list[np.ndarray] = []
        diffs: list[np.ndarray] = []
        b_rates: list[np.ndarray] = []
        c_rates: list[np.ndarray] = []
        baseline_rates: list[np.ndarray] = []
        treatment_rates: list[np.ndarray] = []
        remaining = simulations
        while remaining:
            batch = min(batch_size, remaining)
            remaining -= batch
            scenario = rng.normal(0.0, float(cfg["scenario_logit_sd"]), size=(batch, n, 1))
            treatment_random = rng.normal(
                0.0, float(cfg["treatment_heterogeneity_logit_sd"]), size=(batch, n, 1)
            )
            paraphrase = rng.normal(
                0.0, float(cfg["paraphrase_logit_sd"]), size=(batch, n, paraphrases)
            )
            baseline_logit = (
                float(cfg["baseline_logit_intercept"])
                + domain_offsets[domains][None, :, None]
                + model_offsets[models][None, :, None]
                + scenario
                + paraphrase
            )
            treatment_logit = (
                baseline_logit
                + shift
                + domain_treatment[domains][None, :, None]
                + model_treatment[models][None, :, None]
                + treatment_random
            )
            pb = logistic(baseline_logit)
            pt = logistic(treatment_logit)
            baseline_correct = rng.random((batch, n, paraphrases, repeats)) < pb[:, :, :, None]
            treatment_correct = rng.random((batch, n, paraphrases, repeats)) < pt[:, :, :, None]
            baseline_correct &= rng.random((batch, n, paraphrases, repeats)) >= failure_rate
            treatment_correct &= rng.random((batch, n, paraphrases, repeats)) >= failure_rate
            yb = (baseline_correct.sum(axis=3) >= required).all(axis=2)
            yt = (treatment_correct.sum(axis=3) >= required).all(axis=2)
            b = np.sum((~yb) & yt, axis=1)
            c = np.sum(yb & (~yt), axis=1)
            discordant = b + c
            pvalues = np.ones(batch, dtype=float)
            large = discordant >= 25
            statistic = np.zeros(batch, dtype=float)
            statistic[large] = (
                np.square(np.maximum(0.0, np.abs(b[large] - c[large]) - 1.0)) / discordant[large]
            )
            pvalues[large] = chi2.sf(statistic[large], 1)
            for idx in np.where((discordant > 0) & (~large))[0]:
                k = int(min(b[idx], c[idx]))
                pvalues[idx] = min(1.0, 2.0 * float(binom.cdf(k, int(discordant[idx]), 0.5)))
            diff = yt.mean(axis=1) - yb.mean(axis=1)
            detections.append((pvalues < float(cfg["alpha_two_sided"])) & (diff > 0.0))
            diffs.append(diff)
            b_rates.append(b / n)
            c_rates.append(c / n)
            baseline_rates.append(yb.mean(axis=1))
            treatment_rates.append(yt.mean(axis=1))
        detected_all = np.concatenate(detections)
        diffs_all = np.concatenate(diffs)
        b_all = np.concatenate(b_rates)
        c_all = np.concatenate(c_rates)
        base_all = np.concatenate(baseline_rates)
        treat_all = np.concatenate(treatment_rates)
        power = float(np.mean(detected_all))
        monte_carlo_se = math.sqrt(power * (1.0 - power) / simulations)
        rows.append(
            {
                "scenario_count": n,
                "power": power,
                "monte_carlo_se": monte_carlo_se,
                "mean_absolute_gain": float(np.mean(diffs_all)),
                "gain_quantiles": {
                    "q025": float(np.quantile(diffs_all, 0.025)),
                    "q50": float(np.quantile(diffs_all, 0.5)),
                    "q975": float(np.quantile(diffs_all, 0.975)),
                },
                "mean_baseline_accuracy": float(np.mean(base_all)),
                "mean_treatment_accuracy": float(np.mean(treat_all)),
                "mean_baseline_only_discordance": float(np.mean(c_all)),
                "mean_treatment_only_discordance": float(np.mean(b_all)),
            }
        )
    return rows


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assumptions", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    assumptions = yaml.safe_load(args.assumptions.read_text(encoding="utf-8"))
    results: list[dict[str, Any]] = []
    for index, scenario in enumerate(assumptions["simulation_scenarios"]):
        calibration = calibrate_shift(scenario, int(assumptions["seeds"]["calibration"]) + index)
        table = evaluate_power(
            scenario,
            calibration["treatment_logit_shift"],
            int(assumptions["seeds"]["power"]) + index,
        )
        results.append(
            {"scenario_id": scenario["scenario_id"], "calibration": calibration, "power_table": table}
        )

    threshold = float(assumptions["decision_rule"]["minimum_power"])
    candidates = assumptions["simulation_scenarios"][0]["candidate_scenario_counts"]
    recommended = None
    for n in candidates:
        if all(
            next(row["power"] for row in result["power_table"] if row["scenario_count"] == n)
            >= threshold
            for result in results
        ):
            recommended = int(n)
            break

    output = {
        "schema_version": "1.0.0",
        "kind": "wp006_clustered_paired_power_simulation",
        "assumptions_path": str(args.assumptions),
        "assumptions_sha256": sha256(args.assumptions),
        "software": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "pyyaml": yaml.__version__,
        },
        "decision_rule": assumptions["decision_rule"],
        "recommended_base_scenarios": recommended,
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_json(output))
    print(json.dumps({"recommended_base_scenarios": recommended, "scenarios": len(results)}, sort_keys=True))
    return 0 if recommended is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
