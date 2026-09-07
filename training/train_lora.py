#!/usr/bin/env python
"""LoRA SFT for the Part 1 value-instantiation experiment.

One script, two modes:

  --mode gpu        QLoRA on a 7-8B instruct checkpoint, sized for a 24 GB A10G
                    (SageMaker ml.g5.2xlarge). Defaults follow UNIFIED-DOC "Plan 1".
                    NOT tested on a GPU from this repo; see training/README.md.

  --mode cpu-smoke  LoRA on a tiny instruct model, CPU only, a handful of examples.
                    Proves the plumbing (chat template, assistant-only loss masking,
                    adapter save, generation) without a GPU.

Input is the pipeline's export: runs/<target>/<run>/export/sft_train.jsonl, one JSON
object per line shaped {"messages": [{"role": "user", ...}, {"role": "assistant", ...}],
"meta": {...}}.

Output is an adapter directory plus train_manifest.json recording the arguments, row
count, truncations at max sequence length, optimizer steps, wall time, final loss and
the measured assistant-token mask fraction.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import math
import os
import platform
import random
import sys
import time
from pathlib import Path

LOGGER = logging.getLogger("train_lora")

# UNIFIED-DOC "Plan 1" -> "Starting settings and cost".
GPU_DEFAULTS = {
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "epochs": 3.0,
    "lr": 2e-4,
    "max_seq_len": 2048,
    "rank": 16,
    "alpha": 32,
    "dropout": 0.05,
    "batch_size": 4,
    "grad_accum": 4,
}

# Small enough to finish on 8 CPU cores in minutes. Not a research setting.
CPU_SMOKE_DEFAULTS = {
    "model": "Qwen/Qwen2.5-0.5B-Instruct",
    "epochs": 1.0,
    "lr": 2e-4,
    "max_seq_len": 1024,
    "rank": 8,
    "alpha": 16,
    "dropout": 0.05,
    "batch_size": 1,
    "grad_accum": 2,
}

SUPPORTED_GPU_MODELS = (
    "Qwen/Qwen2.5-7B-Instruct",
    "meta-llama/Llama-3.1-8B-Instruct",
)


# --------------------------------------------------------------------------- args


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--train-file",
        required=True,
        type=Path,
        help="sft_train.jsonl from the export stage.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Where the adapter, tokenizer and train_manifest.json are written.",
    )
    parser.add_argument(
        "--mode",
        choices=("gpu", "cpu-smoke"),
        default="gpu",
        help="gpu = QLoRA on a 7-8B checkpoint; cpu-smoke = tiny model, CPU, plumbing test.",
    )
    # Everything below defaults per mode; None means "use the mode default".
    parser.add_argument("--model", default=None, help="Hugging Face model id or local path.")
    parser.add_argument("--epochs", type=float, default=None)
    parser.add_argument("--lr", type=float, default=None, help="Learning rate.")
    parser.add_argument("--max-seq-len", type=int, default=None)
    parser.add_argument("--rank", type=int, default=None, help="LoRA rank r.")
    parser.add_argument("--alpha", type=int, default=None, help="LoRA alpha.")
    parser.add_argument("--dropout", type=float, default=None, help="LoRA dropout.")
    parser.add_argument("--batch-size", type=int, default=None, help="Per-device train batch size.")
    parser.add_argument("--grad-accum", type=int, default=None, help="Gradient accumulation steps.")
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument(
        "--max-examples",
        type=int,
        default=None,
        help="Truncate the dataset to the first N rows (smoke runs and debugging).",
    )
    parser.add_argument(
        "--no-4bit",
        action="store_true",
        help="gpu mode only: plain bf16 LoRA instead of 4-bit QLoRA. Needs ~2x the VRAM.",
    )
    parser.add_argument(
        "--gradient-checkpointing",
        dest="gradient_checkpointing",
        action="store_true",
        default=None,
        help="Force gradient checkpointing on (default: on in gpu mode, off in cpu-smoke).",
    )
    parser.add_argument(
        "--no-gradient-checkpointing",
        dest="gradient_checkpointing",
        action="store_false",
        help="Force gradient checkpointing off.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate arguments, data and tokenizer, print the resolved plan, then exit "
        "without downloading or training. Use this to argument-check a GPU run cheaply.",
    )
    return parser


def resolve_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse, fill in mode defaults, and reject impossible combinations."""
    args = build_parser().parse_args(argv)
    defaults = GPU_DEFAULTS if args.mode == "gpu" else CPU_SMOKE_DEFAULTS

    for key, value in defaults.items():
        if getattr(args, key) is None:
            setattr(args, key, value)
            setattr(args, f"_{key}_from_default", True)

    if args.gradient_checkpointing is None:
        args.gradient_checkpointing = args.mode == "gpu"

    problems: list[str] = []
    if not args.train_file.is_file():
        problems.append(f"--train-file does not exist: {args.train_file}")
    if args.epochs <= 0:
        problems.append(f"--epochs must be > 0, got {args.epochs}")
    if args.lr <= 0 or args.lr > 1:
        problems.append(f"--lr must be in (0, 1], got {args.lr}")
    if args.max_seq_len < 64:
        problems.append(f"--max-seq-len must be >= 64, got {args.max_seq_len}")
    if args.rank < 1:
        problems.append(f"--rank must be >= 1, got {args.rank}")
    if args.alpha < 1:
        problems.append(f"--alpha must be >= 1, got {args.alpha}")
    if not 0.0 <= args.dropout < 1.0:
        problems.append(f"--dropout must be in [0, 1), got {args.dropout}")
    if args.batch_size < 1:
        problems.append(f"--batch-size must be >= 1, got {args.batch_size}")
    if args.grad_accum < 1:
        problems.append(f"--grad-accum must be >= 1, got {args.grad_accum}")
    if args.max_examples is not None and args.max_examples < 1:
        problems.append(f"--max-examples must be >= 1, got {args.max_examples}")
    if args.mode == "cpu-smoke" and _looks_large(args.model):
        problems.append(
            f"--mode cpu-smoke with a large model ({args.model}) will not finish on CPU. "
            "Pass a small model such as Qwen/Qwen2.5-0.5B-Instruct."
        )

    if problems:
        raise SystemExit("Invalid arguments:\n  - " + "\n  - ".join(problems))

    if args.mode == "gpu" and args.model not in SUPPORTED_GPU_MODELS:
        LOGGER.warning(
            "Model %s is outside the two checkpoints this script was written against (%s). "
            "It should still work; check the chat template supports assistant-only loss.",
            args.model,
            ", ".join(SUPPORTED_GPU_MODELS),
        )
    return args


def _looks_large(model_id: str) -> bool:
    """Crude size sniff on the model name, used only to catch obvious CPU mistakes."""
    lowered = model_id.lower()
    return any(tag in lowered for tag in ("-3b", "-7b", "-8b", "-13b", "-14b", "-32b", "-70b"))


# ---------------------------------------------------------------------- data


def load_rows(train_file: Path, max_examples: int | None) -> list[dict]:
    """Read sft_train.jsonl and check every row is a single user/assistant exchange."""
    rows: list[dict] = []
    with train_file.open() as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise SystemExit(f"{train_file}:{line_number}: not valid JSON ({error})") from error
            messages = row.get("messages")
            if not isinstance(messages, list) or not messages:
                raise SystemExit(f"{train_file}:{line_number}: missing a non-empty 'messages' list")
            roles = [message.get("role") for message in messages]
            if roles[-1] != "assistant":
                raise SystemExit(
                    f"{train_file}:{line_number}: last message role is {roles[-1]!r}, expected 'assistant'. "
                    "Assistant-only loss needs the assistant turn last."
                )
            for index, message in enumerate(messages):
                if message.get("role") not in {"system", "user", "assistant"}:
                    raise SystemExit(f"{train_file}:{line_number}: message {index} has role {message.get('role')!r}")
                if not isinstance(message.get("content"), str) or not message["content"].strip():
                    raise SystemExit(f"{train_file}:{line_number}: message {index} has empty content")
            rows.append(row)
    if not rows:
        raise SystemExit(f"{train_file}: no rows")
    if max_examples is not None:
        rows = rows[:max_examples]
    return rows


def count_truncations(rows: list[dict], tokenizer, max_seq_len: int) -> tuple[int, dict]:
    """Tokenize every row through the chat template and count what exceeds max_seq_len.

    TRL truncates silently, so this pre-pass is the only place truncation is visible.
    """
    lengths: list[int] = []
    for row in rows:
        text = tokenizer.apply_chat_template(row["messages"], tokenize=False)
        lengths.append(len(tokenizer(text, add_special_tokens=False)["input_ids"]))
    lengths.sort()
    truncated = sum(1 for length in lengths if length > max_seq_len)
    stats = {
        "min": lengths[0],
        "median": lengths[len(lengths) // 2],
        "p95": lengths[min(len(lengths) - 1, int(0.95 * len(lengths)))],
        "max": lengths[-1],
    }
    return truncated, stats


# ------------------------------------------------------------------- masking check


def measure_assistant_mask(trainer, tokenizer) -> dict:
    """Pull one real training batch and report how much of it is excluded from the loss.

    This is the check that assistant-only loss is actually in force: it reads `labels`
    after the collator, so it reflects what the loss sees rather than what was configured.
    Returns the masked fraction plus the decoded supervised span of the first example,
    which must be assistant text only.
    """
    import torch

    batch = next(iter(trainer.get_train_dataloader()))
    labels = batch["labels"]
    input_ids = batch["input_ids"]

    real = labels != -100
    padding = input_ids == tokenizer.pad_token_id
    considered = ~padding
    masked = considered & ~real

    first_labels = labels[0]
    first_ids = input_ids[0]
    supervised_ids = first_ids[first_labels != -100]
    ignored_ids = first_ids[(first_labels == -100) & (first_ids != tokenizer.pad_token_id)]

    total = int(considered.sum())
    return {
        "batch_tokens_excluding_padding": total,
        "tokens_in_loss": int(real.sum()),
        "masked_label_fraction": round(float(masked.sum()) / total, 4) if total else None,
        "example_supervised_text": tokenizer.decode(supervised_ids, skip_special_tokens=False),
        "example_ignored_text": tokenizer.decode(ignored_ids, skip_special_tokens=False),
    }


def assert_user_tokens_masked(measurement: dict, rows: list[dict]) -> list[str]:
    """Cheap sanity check: the first user turn must not appear in the supervised span."""
    warnings: list[str] = []
    supervised = measurement["example_supervised_text"]
    for row in rows[:1]:
        for message in row["messages"]:
            if message["role"] != "user":
                continue
            probe = message["content"][:60]
            if probe and probe in supervised:
                warnings.append(
                    "User text appears inside the supervised span: assistant-only loss is NOT masking "
                    "the prompt. Do not trust this run."
                )
    fraction = measurement["masked_label_fraction"]
    if fraction is not None and fraction < 0.01:
        warnings.append(
            f"Only {fraction:.2%} of tokens are masked. For a single user/assistant exchange the prompt "
            "should account for a visible share; assistant-only loss may not be applied."
        )
    return warnings


# ------------------------------------------------------------------------ main


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    args = resolve_args(argv)

    rows = load_rows(args.train_file, args.max_examples)
    LOGGER.info("Loaded %d training rows from %s", len(rows), args.train_file)

    effective_batch = args.batch_size * args.grad_accum
    LOGGER.info(
        "Resolved plan | mode=%s model=%s epochs=%s lr=%s max_seq_len=%d "
        "lora(r=%d, alpha=%d, dropout=%s, all-linear) batch=%d x accum=%d (effective %d)",
        args.mode,
        args.model,
        args.epochs,
        args.lr,
        args.max_seq_len,
        args.rank,
        args.alpha,
        args.dropout,
        args.batch_size,
        args.grad_accum,
        effective_batch,
    )

    import torch

    use_cuda = torch.cuda.is_available()
    if args.mode == "gpu" and not use_cuda and not args.check_only:
        raise SystemExit(
            "--mode gpu needs a CUDA device and none is visible. This machine has no GPU; "
            "run --mode cpu-smoke here and --mode gpu on ml.g5.2xlarge (see training/sagemaker_job.md). "
            "Use --check-only to validate the arguments without a GPU."
        )

    use_4bit = args.mode == "gpu" and not args.no_4bit
    if use_4bit and importlib.util.find_spec("bitsandbytes") is None and not args.check_only:
        raise SystemExit(
            "4-bit QLoRA needs bitsandbytes, which is not installed (it has no useful CPU build, so "
            "training/requirements.txt leaves it out). Install it on the GPU host with "
            "`pip install bitsandbytes>=0.43`, or pass --no-4bit for plain bf16 LoRA."
        )

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    if tokenizer.chat_template is None:
        raise SystemExit(
            f"{args.model} has no chat template. This script trains on chat-formatted data and "
            "will not guess a format."
        )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    truncated, length_stats = count_truncations(rows, tokenizer, args.max_seq_len)
    LOGGER.info(
        "Sequence lengths (chat-templated tokens): min=%d median=%d p95=%d max=%d | "
        "%d of %d rows exceed --max-seq-len %d and will be truncated",
        length_stats["min"],
        length_stats["median"],
        length_stats["p95"],
        length_stats["max"],
        truncated,
        len(rows),
        args.max_seq_len,
    )
    if truncated:
        LOGGER.warning(
            "%d row(s) will lose their tail. A truncated row loses the end of the assistant answer, "
            "which teaches the model not to finish. Raise --max-seq-len or shorten the export.",
            truncated,
        )

    if args.check_only:
        LOGGER.info("--check-only: arguments, data and tokenizer are consistent. Exiting before training.")
        return 0

    from datasets import Dataset
    from peft import LoraConfig
    from trl import SFTConfig, SFTTrainer

    random.seed(args.seed)
    torch.manual_seed(args.seed)

    dataset = Dataset.from_list([{"messages": row["messages"]} for row in rows])

    peft_config = LoraConfig(
        r=args.rank,
        lora_alpha=args.alpha,
        lora_dropout=args.dropout,
        bias="none",
        task_type="CAUSAL_LM",
        # UNIFIED-DOC says "all linear layers"; PEFT resolves this per architecture and
        # correctly skips the output head.
        target_modules="all-linear",
    )

    quantization_config = None
    if use_4bit:
        from transformers import BitsAndBytesConfig  # needs bitsandbytes at runtime

        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        )

    if args.mode == "gpu":
        dtype = "bfloat16" if torch.cuda.is_bf16_supported() else "float16"
        optim = "paged_adamw_8bit" if use_4bit else "adamw_torch"
    else:
        dtype = "float32"  # CPU bf16 training is slow and numerically awkward
        optim = "adamw_torch"

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # transformers 5 dropped `warmup_ratio`, so compute the warmup in steps.
    steps_per_epoch = max(1, math.ceil(len(rows) / effective_batch))
    planned_steps = max(1, math.ceil(steps_per_epoch * args.epochs))
    warmup_steps = max(1, round(0.03 * planned_steps))

    sft_config = SFTConfig(
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        max_length=args.max_seq_len,
        # Loss on assistant tokens only. TRL swaps in a chat template carrying
        # {% generation %} markers when the model's own template lacks them
        # (Qwen2.5 and Llama 3 are both covered), then builds the label mask from it.
        assistant_only_loss=True,
        packing=False,
        model_init_kwargs={"dtype": dtype},
        gradient_checkpointing=args.gradient_checkpointing,
        optim=optim,
        lr_scheduler_type="cosine",
        warmup_steps=warmup_steps,
        logging_steps=1,
        save_strategy="no",  # the adapter is saved once at the end
        bf16=args.mode == "gpu" and dtype == "bfloat16",
        fp16=args.mode == "gpu" and dtype == "float16",
        seed=args.seed,
        report_to=[],
        dataset_num_proc=1,
        use_cpu=args.mode == "cpu-smoke",
    )

    LOGGER.info("Building trainer (this downloads %s on first run)", args.model)
    build_started = time.perf_counter()
    trainer = SFTTrainer(
        model=args.model,
        args=sft_config,
        train_dataset=dataset,
        processing_class=tokenizer,
        peft_config=peft_config,
        quantization_config=quantization_config,
    )
    LOGGER.info("Trainer built in %.1fs", time.perf_counter() - build_started)

    trainable = sum(p.numel() for p in trainer.model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in trainer.model.parameters())
    LOGGER.info(
        "Trainable parameters: %s of %s (%.4f%%)",
        f"{trainable:,}",
        f"{total_params:,}",
        100 * trainable / total_params,
    )

    measurement = measure_assistant_mask(trainer, tokenizer)
    LOGGER.info(
        "Assistant-only loss check | %d of %d non-padding tokens are in the loss; "
        "masked label fraction = %.4f",
        measurement["tokens_in_loss"],
        measurement["batch_tokens_excluding_padding"],
        measurement["masked_label_fraction"],
    )
    LOGGER.info("Supervised span starts: %r", measurement["example_supervised_text"][:160])
    LOGGER.info("Ignored span starts:    %r", measurement["example_ignored_text"][:160])
    mask_warnings = assert_user_tokens_masked(measurement, rows)
    for warning in mask_warnings:
        LOGGER.error(warning)

    LOGGER.info("Training")
    train_started = time.perf_counter()
    result = trainer.train()
    wall_time_s = time.perf_counter() - train_started
    LOGGER.info("Training finished in %.1fs", wall_time_s)

    trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))

    manifest = {
        "script": "training/train_lora.py",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "args": {
            key: (str(value) if isinstance(value, Path) else value)
            for key, value in vars(args).items()
            if not key.startswith("_")
        },
        "defaults_applied": sorted(
            key.lstrip("_").removesuffix("_from_default")
            for key in vars(args)
            if key.endswith("_from_default")
        ),
        "dataset": {
            "train_file": str(args.train_file),
            "rows": len(rows),
            "sequence_length_tokens": length_stats,
            "truncated_at_max_seq_len": truncated,
        },
        "lora": {
            "r": args.rank,
            "alpha": args.alpha,
            "dropout": args.dropout,
            "target_modules": "all-linear",
            "trainable_parameters": trainable,
            "total_parameters": total_params,
        },
        "assistant_only_loss": {
            "enabled": True,
            "implementation": "trl.SFTConfig(assistant_only_loss=True)",
            **{k: v for k, v in measurement.items() if not k.startswith("example_")},
            "example_supervised_text_head": measurement["example_supervised_text"][:400],
            "example_ignored_text_head": measurement["example_ignored_text"][:400],
            "warnings": mask_warnings,
        },
        "training": {
            "mode": args.mode,
            "model": args.model,
            "dtype": dtype,
            "quantization": "nf4-double" if use_4bit else "none",
            "optimizer": optim,
            "effective_batch_size": effective_batch,
            "optimizer_steps": int(result.global_step),
            "wall_time_s": round(wall_time_s, 2),
            "final_train_loss": result.metrics.get("train_loss"),
            "loss_history": [
                entry["loss"] for entry in trainer.state.log_history if "loss" in entry
            ],
        },
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "cuda_available": use_cuda,
            "gpu": torch.cuda.get_device_name(0) if use_cuda else None,
            "cpu_count": os.cpu_count(),
        },
    }
    manifest_path = args.output_dir / "train_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    LOGGER.info("Adapter and manifest written to %s", args.output_dir)
    LOGGER.info(
        "steps=%d wall=%.1fs final_loss=%s masked_label_fraction=%.4f",
        result.global_step,
        wall_time_s,
        result.metrics.get("train_loss"),
        measurement["masked_label_fraction"],
    )
    return 1 if mask_warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
