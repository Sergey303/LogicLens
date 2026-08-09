from __future__ import annotations

import ast
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROTO = ROOT / "prototype"

SCIENTIFIC_REPO = "Qwen/Qwen2.5-Coder-7B-Instruct"
SCIENTIFIC_REV = "c03e6d358207e414f1eca0bb1891e29f1db0e242"
SMOKE_REPO = "Qwen/Qwen2.5-Coder-0.5B-Instruct"
SMOKE_REV = "bbf27711794f58ebd1796058f4280b53c32e19fc"
SEEDS = [17, 29, 43]
PACKAGES = {
    "torch": "2.5.1",
    "transformers": "4.46.3",
    "peft": "0.14.0",
    "accelerate": "1.2.1",
    "datasets": "3.2.0",
    "bitsandbytes": "0.46.0",
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise AssertionError(message)


def text(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def doc(name: str):
    return json.loads(text(name))


def require_fragments(body: str, fragments: list[str], label: str) -> None:
    for fragment in fragments:
        require(fragment in body, f"{label} missing: {fragment}")


def validate_model_binding() -> None:
    binding = doc("MODEL_BINDING_CONTRACT.json")
    base = binding["candidate_scientific_base"]
    require(base["repository"] == SCIENTIFIC_REPO, "binding scientific repository drift")
    require(base["revision"] == SCIENTIFIC_REV, "binding scientific revision drift")
    require(base["tokenizer_repository"] == SCIENTIFIC_REPO, "binding tokenizer repository drift")
    require(base["tokenizer_revision"] == SCIENTIFIC_REV, "binding tokenizer revision drift")
    require(binding["binding_status"] == "PROVISIONAL_UNTIL_WP004_FIXED_WEIGHT_PROFILE_ACCEPTED", "binding must remain provisional before WP004")
    causal = binding["causal_binding"]
    for key in [
        "required_same_student_repository",
        "required_same_student_revision",
        "required_same_tokenizer_repository",
        "required_same_tokenizer_revision",
        "required_same_inference_prompt_contract",
        "required_same_decoding_contract",
        "required_same_output_schema",
        "accepted_fixed_weight_profile_reference_required",
        "accepted_fixed_weight_profile_hash_required",
    ]:
        require(causal[key] is True, f"causal model binding relaxed: {key}")
    require(binding["if_binding_fails"]["causal_weight_placement_claim_allowed"] is False, "cross-model causal claim must fail closed")
    require(binding["smoke_model_is_binding_evidence"] is False, "smoke model cannot satisfy scientific model binding")


def validate_estimands() -> None:
    estimands = doc("WEIGHT_BOUNDARY_ESTIMANDS.json")
    require(estimands["analysis_unit"] == "base_scenario_id", "weight boundary must preserve base_scenario_id unit")
    require(estimands["training_seeds"] == SEEDS, "estimand seed drift")
    require(estimands["seed_role"] == "training_run_replication_not_independent_benchmark_sample", "seed role drift")
    require(estimands["pseudoreplication_forbidden"] is True, "seed pseudoreplication must be forbidden")
    primary = estimands["primary_teacher_increment_estimand"]
    require(primary["contrast"] == "W-C_minus_W-B", "primary teacher increment contrast drift")
    require(primary["endpoint"] == "exact_epistemic_contract_correctness", "boundary endpoint drift")
    require(primary["seed_pairing"] == "same_seed_ids_paired_across_W-B_and_W-C", "seed pairing drift")
    require(primary["best_seed_selection"] is False, "best-seed selection must be false")
    require(primary["seed_pooling_as_three_times_sample_size"] is False, "seed pseudoreplication enabled")
    require(estimands["inference"]["three_seed_t_test_as_primary"] is False, "three-seed t-test cannot be primary")


def validate_manifest() -> str:
    manifest = text("TRAINING_MANIFEST.yaml")
    require_fragments(manifest, [
        f"repository: {SCIENTIFIC_REPO}",
        f"revision: {SCIENTIFIC_REV}",
        f"repository: {SMOKE_REPO}",
        f"revision: {SMOKE_REV}",
        "family: QLoRA_SFT",
        "seeds: [17, 29, 43]",
        "seed_role: nested_training_run_replication_not_independent_benchmark_unit",
        "record_membership_matching: exact_same_grouped_record_ids_W-B_W-C",
        "record_ordering: sha256_decimal_seed_nul_record_id_ascending",
        "data_order_may_depend_on_target_bytes: false",
        "target_length_policy: complete_targets_same_schema_same_predeclared_cap_no_semantic_truncation",
        "exact_total_target_token_equality_required: false",
        "semantic_target_truncation_for_matching: prohibited",
        "student_weakness_directed_example_selection: false",
        "multiple_teacher_trajectory_selection: false",
        "segment_specific_teacher_loss_weighting: false",
        "outcome_driven_curriculum: false",
        "requires_exact_fixed_weight_model_binding_for_causal_weight_placement_claim: true",
        "seed_pseudoreplication",
        "cross_model_result_described_as_causal_weight_placement",
    ], "training manifest")
    require("revision: main" not in manifest, "moving model revision forbidden")
    return manifest


def validate_selection() -> None:
    rule = text("ADAPTER_SELECTION_RULE.yaml")
    require_fragments(rule, [
        "seeds: [17, 29, 43]",
        "eligible_checkpoint: final_step_only",
        "optimizer_step: 256",
        "select_best_seed: false",
        "discard_failed_seed: false",
        "replacement_seed: forbidden",
        "seed_role: nested_training_run_replication_not_independent_benchmark_unit",
        "benchmark_sample_size_multiplier_from_three_seeds: 1",
        "causal_fixed_weight_comparison_requires_exact_same_base_and_tokenizer: true",
        "cross_model_if_binding_fails: descriptive_only",
        "model_switch_after_dev_or_holdout: prohibited",
        "exact_model_binding_must_be_resolved_before_holdout: true",
        "seed_aware_estimand_must_be_WP006_accepted_before_holdout: true",
    ], "adapter selection rule")


def validate_environment() -> None:
    env = doc("TRAINING_ENVIRONMENT_LOCK.json")
    require(env["reference_environment"]["python"] == "3.11", "Python version drift")
    require(env["reference_environment"]["cuda"] == "12.4", "CUDA version drift")
    require(env["reference_environment"]["packages"] == PACKAGES, "package lock drift")
    requirements = {}
    for line in text("requirements-smoke.txt").splitlines():
        if line.strip():
            require("==" in line, f"unpinned smoke requirement: {line}")
            name, version = line.split("==", 1)
            requirements[name] = version
    require(requirements == PACKAGES, "smoke requirements differ from environment lock")


def validate_data_and_replicability_docs() -> None:
    data = text("DISTILLATION_DATA_CONTRACT.md")
    require_fragments(data, [
        "It must not receive `gold_target`",
        "exactly the same ordered evaluator-side `record_id` set",
        "Data order may not depend on `gold_target`, `teacher_target`, target length, model loss or DEV performance",
        "Do not end-truncate a semantically valid target",
        "student weakness",
        "DISTILLATION_CONTROL_BOUNDARY.md",
        "Unknown overlap is not treated as safe",
    ], "distillation data contract")
    require("deterministic end truncation is applied to the longer arm" not in data, "stale semantic target truncation rule survived")

    repl = text("TRAINING_REPLICABILITY_CONTRACT.md")
    require_fragments(repl, [
        "not an unsupported claim of bitwise-identical QLoRA weights",
        "SHA256(utf8(decimal_seed) || 0x00 || utf8(record_id))",
        "Three seeds are not three independent benchmark cases",
        "No bad seed may be replaced by a fourth seed",
        "CUBLAS_WORKSPACE_CONFIG=:4096:8",
    ], "training replicability contract")


def validate_leakage_and_teacher_schemas() -> None:
    leakage = doc("LEAKAGE_MEMORIZATION_REPORT.schema.json")
    checks = set(leakage["properties"]["checks"]["required"])
    require({
        "exact_normalized_overlap", "internal_identifier_leak", "forbidden_split_reference",
        "lexical_near_duplicate", "semantic_near_duplicate", "source_family_policy",
        "teacher_prompt_audit", "target_schema_validity", "matched_token_budget",
    } <= checks, "leakage checks incomplete")
    statuses = set(leakage["$defs"]["check"]["properties"]["status"]["enum"])
    require(statuses == {"pass", "fail", "unknown"}, "leakage status vocabulary drift")

    ledger = doc("TEACHER_GENERATION_LEDGER.schema.json")
    budget = ledger["properties"]["budget"]["properties"]
    require(budget["max_successful_semantic_responses_per_record"]["const"] == 1, "teacher success budget drift")
    require(budget["max_provider_attempts_per_record"]["const"] == 2, "teacher attempt budget drift")
    require(ledger["properties"]["summary"]["properties"]["outcome_directed_regeneration"]["const"] is False, "outcome-directed teacher regeneration allowed")

    report = doc("TRAINING_RUN_REPORT.schema.json")
    require(report["properties"]["seed"]["enum"] == SEEDS, "training report seed set drift")
    require(report["properties"]["base_model"]["properties"]["repository"]["const"] == SCIENTIFIC_REPO, "training report base repository drift")
    require(report["properties"]["base_model"]["properties"]["revision"]["const"] == SCIENTIFIC_REV, "training report base revision drift")


def parse_constants(source: str) -> dict:
    result = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                result[node.targets[0].id] = ast.literal_eval(node.value)
            except Exception:
                pass
    return result


def validate_smoke_contract() -> None:
    source = (PROTO / "smoke_train.py").read_text(encoding="utf-8")
    constants = parse_constants(source)
    require(constants["MODEL_REPO"] == SMOKE_REPO, "smoke repository drift")
    require(constants["MODEL_REVISION"] == SMOKE_REV and re.fullmatch(r"[0-9a-f]{40}", SMOKE_REV), "smoke revision drift")
    require(constants["SEED"] == 17, "smoke seed drift")
    require(constants["MAX_LENGTH"] == 256, "smoke max length drift")
    require(constants["EXPECTED_PACKAGES"] == PACKAGES, "smoke package drift")
    require("torch.use_deterministic_algorithms(True" in source, "smoke deterministic algorithms not enforced")
    require("adapter hash did not change after optimizer step" in source, "smoke does not verify adapter update")

    rows = [json.loads(line) for line in (PROTO / "synthetic_train.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    require(len(rows) >= 4, "smoke corpus too small")
    for row in rows:
        require(set(row) == {"split", "input_text", "target_text"}, "smoke fields drift")
        require(row["split"] == "TRAIN", "smoke non-TRAIN row")

    smoke_doc = text("SMOKE_TRAINING_CONTRACT.md")
    require("A real successful CUDA QLoRA smoke" not in smoke_doc or "real successful smoke artifact" in smoke_doc, "smoke evidence boundary unclear")
    require("Existence of this command is not evidence that it ran" in smoke_doc, "static validator must not substitute for smoke")


def validate_general_regression() -> None:
    rows = [json.loads(line) for line in (PROTO / "general_regression_dev.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    require(len(rows) == 12 and len({r["id"] for r in rows}) == 12, "general regression case count/id drift")
    require(all(r["split"] == "DEV" for r in rows), "general regression must be DEV-only")
    require(Counter(r["family"] for r in rows) == Counter({"arithmetic": 3, "instruction": 3, "python_understanding": 3, "json_transform": 3}), "regression family balance drift")


def validate_docs() -> None:
    protocol = text("WEIGHT_ADAPTATION_PROTOCOL.md")
    require_fragments(protocol, [
        "MODEL_BINDING_CONTRACT.json",
        "WEIGHT_BOUNDARY_ESTIMANDS.json",
        "Do not truncate, subsample, pad with supervised no-op content",
        "three seed runs must not be treated as three independent copies",
        "TRAINING_REPLICABILITY_CONTRACT.md",
        "DISTILLATION_CONTROL_BOUNDARY.md",
    ], "weight adaptation protocol")

    controls = text("DISTILLATION_CONTROL_BOUNDARY.md")
    for anchor in ["2026.findings-acl.1349", "2026.acl-short.49", "2026.acl-long.74", "2026.acl-industry.37", "2026.acl-long.908"]:
        require(anchor in controls, f"missing current distillation control: {anchor}")


def main() -> None:
    validate_model_binding()
    validate_estimands()
    validate_manifest()
    validate_selection()
    validate_environment()
    validate_data_and_replicability_docs()
    validate_leakage_and_teacher_schemas()
    validate_smoke_contract()
    validate_general_regression()
    validate_docs()
    print(json.dumps({
        "issue": "ENG-202",
        "status": "CONTRACT_PASS_NO_CUDA_SMOKE_NO_TRAINING_EVIDENCE",
        "scientific_base": f"{SCIENTIFIC_REPO}@{SCIENTIFIC_REV}",
        "scientific_model_binding": "PROVISIONAL_UNTIL_WP004",
        "seeds": SEEDS,
        "analysis_unit": "base_scenario_id",
        "seed_pseudoreplication": False,
        "semantic_target_truncation_for_matching": False,
        "arms": ["W-A", "W-B", "W-C"],
        "W-D": "DISABLED_DEV_ONLY",
        "holdout_access": "FORBIDDEN",
        "cuda_smoke": "NOT_ESTABLISHED_BY_STATIC_VALIDATOR",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
