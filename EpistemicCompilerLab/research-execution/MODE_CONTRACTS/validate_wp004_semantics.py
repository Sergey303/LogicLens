#!/usr/bin/env python3
"""Dedicated non-mutating semantic validator for ENG-156 / WP-004.

Two intentionally separate decisions are emitted:

1. local_semantics: whether the current WP-004 causal artifacts are internally
   coherent and close the known B1-B8 design defects;
2. freeze_readiness: whether all independently governed cross-package inputs are
   actually accepted and exactly aligned.

The default command exits zero when local semantics are valid even if freeze is
blocked. `--require-freeze-ready` exits non-zero unless every blocker is gone.
This prevents producer artifacts or semantically-similar identifiers from being
silently promoted into a confirmatory freeze.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # fail clearly rather than use a partial YAML parser
    raise SystemExit("PyYAML is required: install PyYAML==6.0.2") from exc

MODE_DIR = Path(__file__).resolve().parent
EXEC_ROOT = MODE_DIR.parent
REPO_ROOT = EXEC_ROOT.parents[1]
POWER_ROOT = EXEC_ROOT / "power-analysis"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_MODES = [f"M{i}" for i in range(15)]
EXPECTED_PRIMARY = {
    "contrast_id": "C-PRIMARY",
    "estimand_id": "E-PRIMARY-COMPILED-BUNDLE",
    "treatment": "M6",
    "comparator": "M14",
    "baseline_rule": "DEV-GLOBAL-STRONGEST-MATCHED-V2",
    "unit": "base_scenario_id",
    "endpoint": "scenario_level_exact_epistemic_contract_accuracy",
}


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), f"expected mapping: {path}")
    return data


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), f"expected object: {path}")
    return data


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mode_map(modes_doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    modes = modes_doc.get("modes")
    require(isinstance(modes, list), "MODE_CONTRACTS/modes.yaml modes must be a list")
    result: dict[str, dict[str, Any]] = {}
    for row in modes:
        require(isinstance(row, dict), "mode row must be mapping")
        mode_id = row.get("id")
        require(isinstance(mode_id, str), "mode id missing")
        require(mode_id not in result, f"duplicate mode id: {mode_id}")
        result[mode_id] = row
    require(list(result) == EXPECTED_MODES, f"mode registry must be exactly M0..M14 in order, got {list(result)}")
    for mode_id, row in result.items():
        for key in ("name", "visible", "extra_hidden", "renderer", "authoritative", "budget"):
            require(key in row, f"{mode_id} missing required field {key}")
    return result


def validate_primary(contrasts: dict[str, Any], estimands: dict[str, Any], baseline: dict[str, Any]) -> None:
    primary = contrasts["primary_contrast"]
    require(primary["contrast_id"] == EXPECTED_PRIMARY["contrast_id"], "primary contrast id drift")
    require(primary["estimand_id"] == EXPECTED_PRIMARY["estimand_id"], "primary estimand id drift")
    require(primary["treatment"] == EXPECTED_PRIMARY["treatment"], "primary treatment drift")
    require(primary["comparator"] == EXPECTED_PRIMARY["comparator"], "primary comparator drift")
    require(primary["unit"] == EXPECTED_PRIMARY["unit"], "primary unit drift")
    require(primary["endpoint"] == EXPECTED_PRIMARY["endpoint"], "primary endpoint drift")
    require(primary["intervention_type"] == "multi-component deployed-interface bundle", "primary is not declared as bundle")
    prohibited = str(primary["prohibited_interpretation"]).lower()
    for word in ("execution", "type structure", "conclusion", "renderer"):
        require(word in prohibited, f"primary prohibited-interpretation boundary missing {word}")
    require("sesoi=.08" in str(primary["hypothesis"]).lower(), "primary SESOI role missing")
    require("not a hard observed-point-estimate threshold" in str(primary["hypothesis"]).lower(), "hard SESOI point gate not explicitly forbidden")

    ep = estimands["primary"]
    require(ep["estimand_id"] == EXPECTED_PRIMARY["estimand_id"], "ESTIMANDS primary id drift")
    require(ep["treatment"] == "M6", "ESTIMANDS treatment drift")
    require(ep["comparator"] == "M14(global B*)", "ESTIMANDS comparator drift")
    require(ep["unit"] == EXPECTED_PRIMARY["unit"], "ESTIMANDS unit drift")
    require(ep["endpoint"] == EXPECTED_PRIMARY["endpoint"], "ESTIMANDS endpoint drift")
    require("multi" not in str(ep.get("interpretation", "")).lower() or "bundle" in str(ep["interpretation"]).lower(), "primary interpretation lost bundle boundary")
    require("two-sided superiority" in str(ep["hypothesis"]).lower(), "superiority hypothesis missing")
    require("not a hard" in str(ep["hypothesis"]).lower(), "SESOI hard-threshold prohibition missing")

    require(baseline["rule_id"] == EXPECTED_PRIMARY["baseline_rule"], "baseline rule version drift")
    require(baseline["construction_of_primary_control"]["output_mode_id"] == "M14", "baseline does not construct M14")
    prohibitions = "\n".join(map(str, baseline["matching_prohibitions"])).lower()
    require("truncation" in prohibitions, "baseline does not prohibit truncation")
    require(baseline["adversarial_profile_sensitivity"]["required"] is True, "profile-wise strongest sensitivity missing")
    require(baseline["padding_invariance"]["required"] is True, "padding invariance not required")
    require(baseline["token_tolerance"]["conditional_on"] == "padding_invariance_PASS", "exact token equality not conditioned on padding invariance")


def validate_modes(modes: dict[str, dict[str, Any]], estimands: dict[str, Any]) -> None:
    m9 = modes["M9"]
    require(m9["name"] == "Unstructured Verified Result Serialization", "M9 name/contract drift")
    require("canonical" in str(m9.get("transformation_contract", "")).lower(), "M9 canonical transform missing")
    require("round-trip" in str(m9.get("transformation_contract", "")).lower(), "M9 semantic round-trip requirement missing")
    require("does not isolate typing alone" in str(m9.get("causal_boundary", "")).lower(), "M9 typing-only claim not prohibited")

    m10 = modes["M10"]
    require(m10["name"] == "Minimal Verified Decision Contract", "M10 must be the minimal decision contract")
    require(m10["authoritative"] == ["status", "action"], f"M10 must expose exactly status+action, got {m10['authoritative']}")
    visible = " ".join(map(str, m10["visible"])).lower()
    require("verified status" in visible and "verified action" in visible, "M10 visible contract missing status/action")
    require("allowedconclusion" in " ".join(map(str, m10["extra_hidden"])).lower(), "M10 must hide allowedConclusion")
    require("not a status-only" in str(m10.get("causal_boundary", "")).lower(), "M10 status-only ambiguity remains")

    m11 = modes["M11"]
    require(m11["renderer"] == "deterministic", "M11 is not deterministic")
    require("exact same answer/scoring schema" in str(m11.get("canonical_output", "")).lower(), "M11 canonical scoring equivalence missing")
    require(m11.get("comparison_contract") == "MODE_CONTRACTS/M11_RENDERER_COMPARABILITY.yaml", "M11 comparison contract missing")
    m11_contract = load_yaml(MODE_DIR / "M11_RENDERER_COMPARABILITY.yaml")
    require(m11_contract["non_inferiority"]["margin_absolute_accuracy"] == 0.02, "M11 non-inferiority margin drift")
    require(m11_contract["non_inferiority"]["no_llm_necessity_wording_if_met"] is True, "M11 no-LLM necessity pivot missing")
    require(m11_contract["style_metrics"] == "descriptive_only", "M11 style metrics can influence semantic claim")

    m13 = modes["M13"]
    require(m13.get("mutation_contract") == "MODE_CONTRACTS/M13_MUTATION_CONTRACT.yaml", "M13 mutation contract missing")
    mutation = load_yaml(MODE_DIR / "M13_MUTATION_CONTRACT.yaml")
    require(mutation["scoring"]["aggregate_detectable_and_non_detectable_together"] is False, "M13 detectable/non-detectable mutations are pooled")
    require(set(mutation["allowed_detectability"]) == {"detectable", "non_detectable"}, "M13 detectability vocabulary drift")
    required_fields = set(mutation["instance_required_fields"])
    for key in ("detectability_from_remaining_visible_bytes", "expected_safe_behavior", "valid_answer_set_id", "scoring_rule_id"):
        require(key in required_fields, f"M13 instance contract missing {key}")
    prohibited_labels = " ".join(mutation["scoring"]["prohibited_labels"]).lower()
    require("universal_blind_corruption" in prohibited_labels, "M13 universal corruption aggregation not prohibited")

    padding = load_yaml(MODE_DIR / "PADDING_INVARIANCE_CONTRACT.yaml")
    require(padding["scope"] == "DEV-only before benchmark split freeze", "padding audit timing drift")
    require(padding["construction"]["truncation"] == "forbidden", "padding contract permits truncation")
    require(padding["invariance_gate"]["accuracy_absolute_difference_max"] == 0.02, "padding accuracy tolerance drift")
    require(padding["invariance_gate"]["exact_output_agreement_minimum"] == 0.95, "padding output-agreement tolerance drift")
    require("STOP" in padding["failure_action"][0], "padding failure does not stop matching design")

    secondary_ids = {row["estimand_id"] for row in estimands["secondary"]}
    required_estimands = {
        "E-RESULT-SERIALIZATION", "E-CONCLUSION", "E-MINIMAL-DECISION",
        "E-RICH-FRAME-BEYOND-MINIMAL", "E-RENDERER", "E-COMPILER-BOUNDARY",
        "E-CORRUPTION-DETECTABLE", "E-CORRUPTION-NONDETECTABLE",
    }
    require(required_estimands <= secondary_ids, f"missing secondary estimands: {sorted(required_estimands - secondary_ids)}")
    require("E-STRUCTURE" not in secondary_ids, "obsolete typing-only E-STRUCTURE estimand remains active")
    prohibited = "\n".join(map(str, estimands["prohibited_estimands"])).lower()
    require("m6-m9 as typed-structure-only" in prohibited, "typing-only M6-M9 interpretation not prohibited")
    require("m10 as a status-only" in prohibited, "status-only M10 interpretation not prohibited")
    require("detectable and non-detectable" in prohibited, "M13 pooling not prohibited")


def validate_transfer_boundaries() -> list[str]:
    transfer = load_yaml(MODE_DIR / "TRANSFER_LADDER_ADJUDICATION.yaml")
    require(transfer["status"] == "CONDITIONAL_INTEGRATION_NOT_FREEZE_READY", "transfer ladder falsely freeze-ready")
    decisions = transfer["mode_decisions"]
    require(decisions["M15"]["decision"] == "DEV_ONLY", "M15 must remain DEV-only")
    require(decisions["M16"]["decision"] == "CONDITIONAL_CANDIDATE", "M16 conditional decision drift")
    require(decisions["M18"]["decision"].startswith("DEV_ONLY"), "M18 must remain DEV-only by default")
    require(decisions["M19"]["confirmatory_eligible_now"] is False, "M19 prematurely confirmatory")
    require(decisions["M20"]["confirmatory_eligible_now"] is False, "M20 prematurely confirmatory")
    require(decisions["M21"]["confirmatory_eligible_now"] is False, "M21 prematurely confirmatory")
    require(decisions["M22"]["decision"].startswith("DEV_ONLY"), "M22 must remain DEV-only by default")
    require(transfer["confirmatory_extension_policy"]["current_active_extensions"] == [], "candidate extensions prematurely active")
    require(transfer["freeze_ready"] is False, "transfer registry falsely freeze-ready")

    weight = load_yaml(MODE_DIR / "WEIGHT_BOUNDARY_ADJUDICATION.yaml")
    require(weight["scientific_boundary"] == "separate_weight_changing_study_not_an_M_mode", "weight study merged into M-mode registry")
    require(weight["merge_into_fixed_weight_primary_claim"] == "forbidden", "weight evidence may leak into fixed-weight primary claim")
    require(weight["required_primary_boundary_contrast"] == "W-C_minus_W-B", "weight boundary lacks W-C vs W-B matched control")
    require(weight["current_child_evidence"]["real_linux_cuda_smoke"] == "missing", "ENG-202 CUDA smoke status drift")
    require(weight["freeze_ready"] is False, "weight boundary falsely freeze-ready")
    return list(transfer["freeze_blockers"])


def validate_wp006_alignment(blockers: list[str]) -> None:
    authority = load_json(POWER_ROOT / "WP006_STATISTICAL_AUTHORITY.json")
    primary = authority["primary"]
    require(authority["work_package_id"] == "WP-006", "WP-006 authority package drift")
    require(primary["unit"] == "base_scenario_id", "WP-006 unit drift")
    require(primary["paired"] is True, "WP-006 primary is not paired")
    require(primary["primary_confirmatory_contrasts"] == 1, "WP-006 primary contrast count drift")
    require(primary["alpha_two_sided"] == 0.05, "WP-006 alpha drift")
    require(primary["SESOI_absolute"] == 0.08, "WP-006 SESOI drift")
    require(primary["SESOI_role"] == "planning_relevance_alternative_not_hard_observed_point_threshold", "WP-006 SESOI role drift")
    numeric = authority["current_numeric_status"]
    require(numeric["R2_producer_grid_floor"] == 820, "WP-006 producer R2 floor drift")
    require(numeric["accepted_required_N"] is None, "WP-006 final N prematurely accepted")
    require(authority["confirmatory_access"] == {"HOLDOUT": False, "REPLICATION": False, "GATE_001": False}, "WP-006 opened confirmatory access")
    if primary["endpoint"] != EXPECTED_PRIMARY["endpoint"]:
        blockers.append("WP006_ENDPOINT_IDENTIFIER_DRIFT")


def validate_cross_package(blockers: list[str]) -> None:
    cross = load_yaml(MODE_DIR / "CROSS_PACKAGE_ALIGNMENT.yaml")
    identity = cross["primary_identity"]
    require(identity["contrast_id"] == EXPECTED_PRIMARY["contrast_id"], "cross-package contrast id drift")
    require(identity["estimand_id"] == EXPECTED_PRIMARY["estimand_id"], "cross-package estimand id drift")
    require(identity["treatment_mode"] == "M6" and identity["comparator_mode"] == "M14", "cross-package modes drift")
    require(identity["comparator_rule_id"] == EXPECTED_PRIMARY["baseline_rule"], "cross-package baseline drift")
    require(identity["unit"] == EXPECTED_PRIMARY["unit"], "cross-package unit drift")
    require(identity["endpoint"] == EXPECTED_PRIMARY["endpoint"], "cross-package endpoint drift")
    observed = cross["wp006_statistics"]["observed_producer_authority"]
    require(observed["endpoint_exact_identifier_match"] is False, "cross-package endpoint blocker unexpectedly marked resolved")
    require(observed["disposition"] == "BLOCKER_UNTIL_VERSIONED_EQUIVALENCE_OR_ENG158_REVISE", "endpoint-drift disposition weakened")
    for blocker in cross["freeze_blockers"]:
        if blocker not in blockers:
            blockers.append(blocker)


def validate_alternatives() -> None:
    text = (EXEC_ROOT / "ALTERNATIVE_EXPLANATIONS.md").read_text(encoding="utf-8").lower()
    for phrase in (
        "multi-component", "status + action", "serialization bundle", "padding-invariance",
        "non-detectable", "llm renderer was unnecessary", "weight-changing adaptation is a separate boundary study",
    ):
        require(phrase in text, f"alternative-explanation boundary missing: {phrase}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-freeze-ready", action="store_true")
    args = parser.parse_args()

    required = [
        EXEC_ROOT / "CAUSAL_CONTRASTS.yaml",
        EXEC_ROOT / "ESTIMANDS.yaml",
        EXEC_ROOT / "BASELINE_SELECTION_RULE.yaml",
        EXEC_ROOT / "ALTERNATIVE_EXPLANATIONS.md",
        MODE_DIR / "modes.yaml",
        MODE_DIR / "M13_MUTATION_CONTRACT.yaml",
        MODE_DIR / "M11_RENDERER_COMPARABILITY.yaml",
        MODE_DIR / "PADDING_INVARIANCE_CONTRACT.yaml",
        MODE_DIR / "TRANSFER_LADDER_ADJUDICATION.yaml",
        MODE_DIR / "WEIGHT_BOUNDARY_ADJUDICATION.yaml",
        MODE_DIR / "CROSS_PACKAGE_ALIGNMENT.yaml",
        POWER_ROOT / "WP006_STATISTICAL_AUTHORITY.json",
    ]
    for path in required:
        require(path.is_file(), f"missing WP-004 semantic artifact: {path.relative_to(REPO_ROOT)}")

    contrasts = load_yaml(EXEC_ROOT / "CAUSAL_CONTRASTS.yaml")
    estimands = load_yaml(EXEC_ROOT / "ESTIMANDS.yaml")
    baseline = load_yaml(EXEC_ROOT / "BASELINE_SELECTION_RULE.yaml")
    modes = mode_map(load_yaml(MODE_DIR / "modes.yaml"))

    validate_primary(contrasts, estimands, baseline)
    validate_modes(modes, estimands)
    validate_alternatives()

    blockers: list[str] = []
    for blocker in validate_transfer_boundaries():
        if blocker not in blockers:
            blockers.append(blocker)
    validate_wp006_alignment(blockers)
    validate_cross_package(blockers)

    # Stable order: cross-package contract is normative for current freeze blockers.
    canonical_order = load_yaml(MODE_DIR / "CROSS_PACKAGE_ALIGNMENT.yaml")["freeze_blockers"]
    blockers = [b for b in canonical_order if b in blockers] + sorted(b for b in blockers if b not in canonical_order)

    freeze_ready = not blockers
    status = "FREEZE_READY" if freeze_ready else "LOCAL_SEMANTICS_PASS_FREEZE_BLOCKED"
    report = {
        "schema_version": "1.0.0",
        "work_package_id": "WP-004",
        "linear_issue": "ENG-156",
        "status": status,
        "local_semantics": "PASS",
        "freeze_readiness": "PASS" if freeze_ready else "BLOCKED",
        "primary": EXPECTED_PRIMARY,
        "mode_registry": {"ids": EXPECTED_MODES, "M10_authoritative": modes["M10"]["authoritative"]},
        "known_B1_B8_local_design_remediation": "PASS",
        "freeze_blockers": blockers,
        "wp006_observed_endpoint": load_json(POWER_ROOT / "WP006_STATISTICAL_AUTHORITY.json")["primary"]["endpoint"],
        "wp004_required_endpoint": EXPECTED_PRIMARY["endpoint"],
        "endpoint_exact_identifier_match": load_json(POWER_ROOT / "WP006_STATISTICAL_AUTHORITY.json")["primary"]["endpoint"] == EXPECTED_PRIMARY["endpoint"],
        "producer_may_self_accept": False,
        "independent_review_required": True,
        "holdout_authorized": False,
        "replication_authorized": False,
        "artifact_hashes": {str(path.relative_to(REPO_ROOT)).replace("\\", "/"): sha256_file(path) for path in required},
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(json.dumps(report, sort_keys=True))

    if args.require_freeze_ready and not freeze_ready:
        return 3
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"WP-004 semantic validation failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
