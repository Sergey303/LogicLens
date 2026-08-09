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
EXPECTED_SEEDS = [17, 29, 43]
EXPECTED_PACKAGES = {
    "torch": "2.5.1",
    "transformers": "4.46.3",
    "peft": "0.14.0",
    "accelerate": "1.2.1",
    "datasets": "3.2.0",
    "bitsandbytes": "0.46.0",
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def check_revision(value, expected, label):
    require(value == expected, f"{label} revision drift")
    require(bool(re.fullmatch(r"[0-9a-f]{40}", value)), f"{label} revision is not immutable SHA")


def parse_smoke_constants(source):
    tree = ast.parse(source)
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            try:
                constants[name] = ast.literal_eval(node.value)
            except Exception:
                pass
    return constants


def validate_manifest():
    text = read("TRAINING_MANIFEST.yaml")
    required_fragments = [
        f"repository: {SCIENTIFIC_REPO}",
        f"revision: {SCIENTIFIC_REV}",
        f"repository: {SMOKE_REPO}",
        f"revision: {SMOKE_REV}",
        "family: QLoRA_SFT",
        "quantization_bits: 4",
        "quantization_type: nf4",
        "target_modules: all-linear",
        "seeds: [17, 29, 43]",
        "optimizer_steps: 256",
        "early_stopping: false",
        "checkpoint_selection: final_step_only",
        "target_token_matching: exact_total_effective_supervised_tokens",
        "independently_generated_codex_train_targets_same_schema",
        "teacher_gold_targets_visible: false",
        "runtime: codex_cli",
        "model_selection: runtime_default_no_guessed_override",
        "resolved_model_identity_required_before_generation: true",
        "gold_targets_visible: false",
        "visible_fields: [input_text, teacher_evidence_view, target_schema, teacher_instructions]",
        "max_successful_semantic_responses_per_record: 1",
        "max_provider_attempts_per_record: 2",
        "retry_attempt_condition: pre_semantic_transport_or_infrastructure_failure_only",
        "retry_after_refusal_or_schema_failure: false",
        "max_input_tokens_per_attempt: 4096",
        "max_output_tokens_per_semantic_response: 256",
        "total_provider_attempt_ceiling_formula: 2*N_train",
        "total_input_token_ceiling_formula: 8192*N_train",
        "total_output_token_ceiling_formula: 256*N_train",
        "producer_hidden_content_access: false",
        "teacher_hidden_content_access: false",
        "permitted_output: leakage_report_status_and_aggregate_evidence_only",
        "W-D:",
        "enabled: false",
        "scope: DEV_ONLY",
        "holdout_access_authorized: false",
        "replication_access_authorized: false",
        "retry_after_semantic_response",
        "outcome_directed_teacher_regeneration",
        "silent_teacher_model_fallback",
        "fixed_weight_claim_from_weight_changing_result",
    ]
    for fragment in required_fragments:
        require(fragment in text, f"training manifest missing: {fragment}")
    require("moving_revision_forbidden: true" in text, "moving revision prohibition missing")
    require("extra_rationale: false" in text, "core arms must forbid extra rationale")
    require("match_to: W-B" in text, "W-C matching rule missing")
    require("visible_split: TRAIN" in text, "teacher TRAIN-only visibility missing")
    require("student_outputs_visible: false" in text, "teacher must not see student outputs")
    return text


def validate_selection_rule():
    text = read("ADAPTER_SELECTION_RULE.yaml")
    for fragment in [
        "seeds: [17, 29, 43]",
        "early_stopping: disabled",
        "eligible_checkpoint: final_step_only",
        "optimizer_step: 256",
        "dev_checkpoint_selection: forbidden",
        "select_best_seed: false",
        "discard_failed_seed: false",
        "report_all_seeds: true",
        "new_candidate_version_and_rerun_all_W-B_W-C_seeds",
        "change_after_holdout: prohibited",
    ]:
        require(fragment in text, f"selection rule missing: {fragment}")


def validate_environment():
    env = json.loads(read("TRAINING_ENVIRONMENT_LOCK.json"))
    require(env["reference_environment"]["python"] == "3.11", "Python reference version drift")
    require(env["reference_environment"]["cuda"] == "12.4", "CUDA reference version drift")
    require(env["reference_environment"]["packages"] == EXPECTED_PACKAGES, "package pin drift")
    install = env["installation_contract"]
    require(install["exact_versions_required"] is True, "exact package versions not required")
    require(install["pip_freeze_required_per_run"] is True, "pip freeze evidence not required")

    requirements = {}
    for line in read("requirements-smoke.txt").splitlines():
        if not line.strip():
            continue
        require("==" in line, f"unpinned requirement: {line}")
        name, version = line.split("==", 1)
        requirements[name] = version
    require(requirements == EXPECTED_PACKAGES, "requirements-smoke.txt differs from environment lock")


def validate_leakage_schema():
    schema = json.loads(read("LEAKAGE_MEMORIZATION_REPORT.schema.json"))
    checks = schema["properties"]["checks"]["required"]
    expected = {
        "exact_normalized_overlap",
        "internal_identifier_leak",
        "forbidden_split_reference",
        "lexical_near_duplicate",
        "semantic_near_duplicate",
        "source_family_policy",
        "teacher_prompt_audit",
        "target_schema_validity",
        "matched_token_budget",
    }
    require(set(checks) == expected, "leakage check set drift")
    statuses = schema["$defs"]["check"]["properties"]["status"]["enum"]
    require(set(statuses) == {"pass", "fail", "unknown"}, "fail-closed epistemic statuses drift")
    require("allOf" in schema, "confirmatory fail-closed rule missing")


def validate_teacher_contract_and_ledger():
    contract = read("TEACHER_RUNTIME_CONTRACT.md")
    for fragment in [
        "without an unsupported guessed `--codex-model` override",
        "teacher_model_reproducibility: limited",
        "maximum successful semantic generation responses: `1`",
        "maximum provider attempts: `2`",
        "byte-identical frozen request",
        "no retry is permitted after a refusal",
        "`8192 * N`",
        "No target may be regenerated because W-C underperforms",
    ]:
        require(fragment in contract, f"teacher runtime contract missing: {fragment}")

    schema = json.loads(read("TEACHER_GENERATION_LEDGER.schema.json"))
    budget = schema["properties"]["budget"]["properties"]
    require(budget["max_successful_semantic_responses_per_record"]["const"] == 1, "teacher success budget drift")
    require(budget["max_provider_attempts_per_record"]["const"] == 2, "teacher attempt budget drift")
    require(budget["max_input_tokens_per_attempt"]["const"] == 4096, "teacher input token budget drift")
    require(budget["max_output_tokens_per_semantic_response"]["const"] == 256, "teacher output token budget drift")
    attempts = schema["properties"]["records"]["items"]["properties"]["attempts"]
    require(attempts["maxItems"] == 2, "teacher ledger permits too many attempts")
    successful = schema["properties"]["records"]["items"]["properties"]["successful_semantic_responses"]
    require(successful["maximum"] == 1, "teacher ledger permits multiple semantic successes")
    outcome_directed = schema["properties"]["summary"]["properties"]["outcome_directed_regeneration"]
    require(outcome_directed["const"] is False, "teacher ledger allows outcome-directed regeneration")


def validate_training_report_schema():
    schema = json.loads(read("TRAINING_RUN_REPORT.schema.json"))
    props = schema["properties"]
    require(props["seed"]["enum"] == EXPECTED_SEEDS, "training report seed set drift")
    require(props["base_model"]["properties"]["repository"]["const"] == SCIENTIFIC_REPO, "training report base repository drift")
    require(props["base_model"]["properties"]["revision"]["const"] == SCIENTIFIC_REV, "training report base revision drift")
    recipe = props["recipe"]["properties"]
    require(recipe["optimizer_steps"]["const"] == 256, "training report step count drift")
    require(recipe["rank"]["const"] == 16, "training report rank drift")
    require(recipe["selected_checkpoint"]["const"] == "final_step_256", "training report checkpoint selection drift")
    require(props["failure_retained"]["const"] is True, "training report may discard failures")


def validate_smoke_data_and_script():
    rows = []
    data_path = PROTO / "synthetic_train.jsonl"
    for line in data_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    require(len(rows) >= 4, "smoke corpus too small")
    for row in rows:
        require(set(row) == {"split", "input_text", "target_text"}, "unexpected smoke data fields")
        require(row["split"] == "TRAIN", "smoke data is not TRAIN-only")
        visible = (row["input_text"] + "\n" + row["target_text"]).upper()
        for forbidden in ("DEV", "HOLDOUT", "REPLICATION"):
            require(forbidden not in visible, f"forbidden split text in smoke data: {forbidden}")

    smoke_source = (PROTO / "smoke_train.py").read_text(encoding="utf-8")
    ast.parse(smoke_source)
    constants = parse_smoke_constants(smoke_source)
    require(constants["MODEL_REPO"] == SMOKE_REPO, "smoke repository drift")
    check_revision(constants["MODEL_REVISION"], SMOKE_REV, "smoke")
    require(constants["SEED"] == 17, "smoke seed drift")
    require(constants["MAX_LENGTH"] == 256, "smoke sequence length drift")
    require(constants["EXPECTED_PACKAGES"] == EXPECTED_PACKAGES, "smoke package pins drift")
    for code_fragment in [
        "load_in_4bit=True",
        'bnb_4bit_quant_type="nf4"',
        "bnb_4bit_use_double_quant=True",
        "r=16",
        "lora_alpha=32",
        'target_modules="all-linear"',
        "optimizer.step()",
        "adapter_pre_sha256",
        "adapter_post_sha256",
        "peak_allocated_vram_bytes",
        "pip-freeze.txt",
    ]:
        require(code_fragment in smoke_source, f"smoke implementation missing: {code_fragment}")


def validate_general_regression():
    plan = read("GENERAL_REGRESSION_CHECK_PLAN.md")
    for fragment in [
        "exactly 12 DEV-only synthetic cases",
        "three cases per family",
        "must not be used to",
        "choose the best W-B/W-C seed",
        "REGRESSION_SEVERE",
        "no broad claim such as",
    ]:
        require(fragment in plan, f"general regression plan missing: {fragment}")

    rows = []
    for line in (PROTO / "general_regression_dev.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    require(len(rows) == 12, "general regression set must contain exactly 12 cases")
    require(len({row["id"] for row in rows}) == 12, "duplicate general regression case id")
    require(all(row["split"] == "DEV" for row in rows), "general regression set is not DEV-only")
    families = Counter(row["family"] for row in rows)
    require(families == Counter({"arithmetic": 3, "instruction": 3, "python_understanding": 3, "json_transform": 3}), "general regression family balance drift")
    for row in rows:
        require(set(row) == {"id", "split", "family", "prompt", "expected"}, "general regression fields drift")
        visible = (row["prompt"] + "\n" + row["expected"]).upper()
        require("HOLDOUT" not in visible and "REPLICATION" not in visible, "hidden-split text in general regression set")

    scorer = (PROTO / "score_general_regression.py").read_text(encoding="utf-8")
    ast.parse(scorer)
    require('.replace("\\r\\n", "\\n").strip()' in scorer, "regression normalization drift")
    require("prediction id mismatch" in scorer, "regression scorer does not fail closed on case mismatch")


def validate_docs():
    protocol = read("WEIGHT_ADAPTATION_PROTOCOL.md")
    data = read("DISTILLATION_DATA_CONTRACT.md")
    smoke = read("SMOKE_TRAINING_CONTRACT.md")
    require("W-C vs W-B" in protocol, "primary teacher contrast missing")
    require("does not expose independently adjudicated gold targets to Codex" in protocol, "gold-blind teacher rule missing")
    require("same supervised-target token budget" in protocol, "matched target-token principle missing")
    require("There is no best-seed selection" in protocol, "no-best-seed rule missing")
    require("It must not receive `gold_target`" in data, "teacher gold exclusion missing")
    require("Free-form chain-of-thought" in data, "rationale separation rule missing")
    require("Unknown overlap is not treated as safe" in data, "unknown leakage fail-closed rule missing")
    require("sealed split custodian" in data, "sealed hidden-split scanner boundary missing")
    require(SMOKE_REV in smoke and SMOKE_REPO in smoke, "smoke immutable anchor missing")
    require("requirements-smoke.txt" in smoke, "smoke environment install command missing")
    require("Existence of this command is not evidence that it ran" in smoke, "smoke evidence boundary missing")


def main():
    manifest = validate_manifest()
    check_revision(SCIENTIFIC_REV, SCIENTIFIC_REV, "scientific")
    check_revision(SMOKE_REV, SMOKE_REV, "smoke")
    require("revision: main" not in manifest, "moving main revision is forbidden")
    validate_selection_rule()
    validate_environment()
    validate_leakage_schema()
    validate_teacher_contract_and_ledger()
    validate_training_report_schema()
    validate_smoke_data_and_script()
    validate_general_regression()
    validate_docs()
    report = {
        "issue": "ENG-202",
        "status": "CONTRACT_PASS_NO_TRAINING_EVIDENCE",
        "scientific_revision": SCIENTIFIC_REV,
        "smoke_revision": SMOKE_REV,
        "seeds": EXPECTED_SEEDS,
        "arms": ["W-A", "W-B", "W-C"],
        "W-D": "DISABLED_DEV_ONLY",
        "teacher_gold_targets_visible": False,
        "teacher_max_provider_attempts_per_record": 2,
        "general_regression_cases": 12,
        "holdout_access": "FORBIDDEN",
        "github_actions_used": False,
    }
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
