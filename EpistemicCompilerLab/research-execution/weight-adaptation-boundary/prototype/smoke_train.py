import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

MODEL_REPO = "Qwen/Qwen2.5-Coder-0.5B-Instruct"
MODEL_REVISION = "bbf27711794f58ebd1796058f4280b53c32e19fc"
SEED = 17
MAX_LENGTH = 256
EXPECTED_PACKAGES = {
    "torch": "2.5.1",
    "transformers": "4.46.3",
    "peft": "0.14.0",
    "accelerate": "1.2.1",
    "datasets": "3.2.0",
    "bitsandbytes": "0.46.0",
}
FORBIDDEN_TEXT = ("HOLDOUT", "REPLICATION", "DEV")

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "synthetic_train.jsonl"


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_trainable_state(model):
    h = hashlib.sha256()
    count = 0
    for name, parameter in sorted(model.named_parameters(), key=lambda item: item[0]):
        if not parameter.requires_grad:
            continue
        count += parameter.numel()
        h.update(name.encode("utf-8"))
        tensor = parameter.detach().float().cpu().contiguous()
        h.update(tensor.numpy().tobytes())
    if count == 0:
        raise RuntimeError("no trainable adapter parameters")
    return h.hexdigest(), count


def check_packages():
    actual = {}
    for package, expected in EXPECTED_PACKAGES.items():
        version = importlib.metadata.version(package)
        actual[package] = version
        if version != expected:
            raise RuntimeError(f"package drift: {package}={version}, expected {expected}")
    return actual


def load_rows():
    rows = []
    for line_number, line in enumerate(DATA_PATH.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("split") != "TRAIN":
            raise RuntimeError(f"non-TRAIN row at line {line_number}")
        visible = f"{row.get('input_text', '')}\n{row.get('target_text', '')}"
        for token in FORBIDDEN_TEXT:
            if token in visible.upper():
                raise RuntimeError(f"forbidden split token {token} in line {line_number}")
        if set(row) != {"split", "input_text", "target_text"}:
            raise RuntimeError(f"unexpected data fields at line {line_number}")
        rows.append(row)
    if not rows:
        raise RuntimeError("empty synthetic training corpus")
    return rows


def get_driver_version():
    try:
        proc = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            check=True,
            capture_output=True,
            text=True,
        )
        return proc.stdout.strip().splitlines()[0]
    except Exception:
        return "unavailable"


def pip_freeze():
    proc = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout


def encode_example(tokenizer, input_text, target_text, torch):
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": input_text}],
        tokenize=False,
        add_generation_prompt=True,
    )
    full_text = prompt + target_text + tokenizer.eos_token
    prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    encoded = tokenizer(
        full_text,
        add_special_tokens=False,
        truncation=True,
        max_length=MAX_LENGTH,
        return_tensors="pt",
    )
    labels = encoded["input_ids"].clone()
    prompt_len = min(len(prompt_ids), labels.shape[1])
    labels[:, :prompt_len] = -100
    if torch.all(labels == -100):
        raise RuntimeError("target was fully truncated")
    encoded["labels"] = labels
    return encoded


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output = Path(args.output).resolve()
    if output.exists() and any(output.iterdir()):
        raise RuntimeError("output directory must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)

    package_versions = check_packages()
    rows = load_rows()

    import torch
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required by the frozen smoke contract")

    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.use_deterministic_algorithms(True, warn_only=False)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.cuda.reset_peak_memory_stats()

    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_REPO, revision=MODEL_REVISION)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_REPO,
        revision=MODEL_REVISION,
        quantization_config=quantization,
        device_map={"": 0},
        torch_dtype=torch.bfloat16,
    )
    resolved = getattr(model.config, "_commit_hash", None)
    if resolved and resolved != MODEL_REVISION:
        raise RuntimeError(f"resolved model revision drift: {resolved}")

    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model = get_peft_model(
        model,
        LoraConfig(
            r=16,
            lora_alpha=32,
            lora_dropout=0.05,
            target_modules="all-linear",
            bias="none",
            task_type="CAUSAL_LM",
        ),
    )
    model.train()

    pre_hash, trainable_parameters = hash_trainable_state(model)
    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=2e-4,
        weight_decay=0.0,
    )

    encoded = encode_example(tokenizer, rows[0]["input_text"], rows[0]["target_text"], torch)
    encoded = {key: value.to("cuda:0") for key, value in encoded.items()}

    started = time.perf_counter()
    optimizer.zero_grad(set_to_none=True)
    outputs = model(**encoded)
    loss = outputs.loss
    if not math.isfinite(float(loss.detach().cpu())):
        raise RuntimeError("non-finite smoke loss")
    loss.backward()
    torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 1.0)
    optimizer.step()
    torch.cuda.synchronize()
    wall_seconds = time.perf_counter() - started

    post_hash, post_count = hash_trainable_state(model)
    if post_count != trainable_parameters:
        raise RuntimeError("trainable parameter count changed")
    if post_hash == pre_hash:
        raise RuntimeError("adapter hash did not change after optimizer step")

    adapter_dir = output / "adapter"
    model.save_pretrained(adapter_dir, safe_serialization=True)
    tokenizer.save_pretrained(output / "tokenizer")

    adapter_files = {}
    for path in sorted(adapter_dir.rglob("*")):
        if path.is_file():
            adapter_files[str(path.relative_to(output)).replace(os.sep, "/")] = sha256_file(path)
    if not adapter_files:
        raise RuntimeError("no adapter files saved")

    freeze_text = pip_freeze()
    (output / "pip-freeze.txt").write_text(freeze_text, encoding="utf-8", newline="\n")

    report = {
        "schema_version": "1.0.0",
        "issue": "ENG-202",
        "evidence_class": "INFRASTRUCTURE_SMOKE_ONLY_NOT_SCIENTIFIC",
        "model_repository": MODEL_REPO,
        "model_revision": MODEL_REVISION,
        "tokenizer_repository": MODEL_REPO,
        "tokenizer_revision": MODEL_REVISION,
        "seed": SEED,
        "optimizer_steps": 1,
        "max_sequence_length": MAX_LENGTH,
        "corpus_sha256": sha256_file(DATA_PATH),
        "packages": package_versions,
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "torch": torch.__version__,
        "cuda_runtime": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0),
        "driver": get_driver_version(),
        "loss": float(loss.detach().cpu()),
        "wall_seconds": wall_seconds,
        "peak_allocated_vram_bytes": torch.cuda.max_memory_allocated(),
        "trainable_parameters": trainable_parameters,
        "adapter_pre_sha256": pre_hash,
        "adapter_post_sha256": post_hash,
        "adapter_files": adapter_files,
    }
    (output / "smoke-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
