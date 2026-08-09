import ast
import json
import re
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
        "W-D:",
        "enabled: false",
        "scope: DEV_ONLY",
        "holdout_access_authorized: false",
        "replication_access_authorized: false",
        "fixed_weight_claim_from_weight_changing_result",
    ]
    for fragment in required_fragments:
        require(fragment in text, f"training manifest missing: {fragment}")
    require("moving_revision_forbidden: true" in text, "moving revision prohibition missing")
    require("extra_rationale: false" in text, "core arms must forbid extra rationale")
    require("match_to: W-B" in text, "W-C matching rule missing")
    require("visible_split: TRAIN" in text, "teacher TRAIN-only visibility missing")
    require("student_outputs_visible: false" in text, "teacher must not see student outputs")
    require("call_budget_per_record: 1" in text, "teacher call budget not frozen")
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


def validate_data_and_smoke():
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


def validate_docs():
    protocol = read("WEIGHT_ADAPTATION_PROTOCOL.md")
    data = read("DISTILLATION_DATA_CONTRACT.md")
    smoke = read("SMOKE_TRAINING_CONTRACT.md")
    require("W-C vs W-B" in protocol, "primary teacher contrast missing")
    require("same supervised-target token budget" in protocol, "matched target-token principle missing")
    require("There is no best-seed selection" in protocol, "no-best-seed rule missing")
    require("Free-form chain-of-thought" in data, "rationale separation rule missing")
    require("Unknown overlap is not treated as safe" in data, "unknown leakage fail-closed rule missing")
    require(SMOKE_REV in smoke and SMOKE_REPO in smoke, "smoke immutable anchor missing")
    require("Existence of this command is not evidence that it ran" in smoke, "smoke evidence boundary missing")


def main():
    manifest = validate_manifest()
    check_revision(SCIENTIFIC_REV, SCIENTIFIC_REV, "scientific")
    check_revision(SMOKE_REV, SMOKE_REV, "smoke")
    require("revision: main" not in manifest, "moving main revision is forbidden")
    validate_selection_rule()
    validate_environment()
    validate_leakage_schema()
    validate_data_and_smoke()
    validate_docs()
    report = {
        "issue": "ENG-202",
        "status": "CONTRACT_PASS_NO_TRAINING_EVIDENCE",
        "scientific_revision": SCIENTIFIC_REV,
        "smoke_revision": SMOKE_REV,
        "seeds": EXPECTED_SEEDS,
        "arms": ["W-A", "W-B", "W-C"],
        "W-D": "DISABLED_DEV_ONLY",
        "holdout_access": false if False else "FORBIDDEN",
        "github_actions_used": False,
    }
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
