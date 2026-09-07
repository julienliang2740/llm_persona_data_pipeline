#!/usr/bin/env python
"""Answer eval.jsonl prompts with the base model, with or without a LoRA adapter.

Run it twice with the same settings to get the before/after pair that Plan 1 asks for:

    # after
    python training/generate_with_adapter.py --eval-file .../eval.jsonl \
        --adapter-dir runs/.../adapter --out .../answers_adapter.jsonl
    # before
    python training/generate_with_adapter.py --eval-file .../eval.jsonl \
        --model Qwen/Qwen2.5-7B-Instruct --out .../answers_base.jsonl

Output is answers.jsonl, one row per prompt, in the shape pipeline/evaluate.py consumes:

    {"prompt_id": ..., "prompt": ..., "model": ..., "text": ...}

plus a "meta" object with the generation settings, so a judge run can be traced back.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

LOGGER = logging.getLogger("generate_with_adapter")

MODE_DEFAULTS = {
    # UNIFIED-DOC: "Evaluation generation | Same settings before/after; temperature 0.7".
    "gpu": {"max_new_tokens": 400, "temperature": 0.7},
    # Small enough to finish on CPU. Answers will be short and are only a plumbing check.
    "cpu-smoke": {"max_new_tokens": 96, "temperature": 0.7},
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--eval-file", required=True, type=Path, help="eval.jsonl from the export stage.")
    parser.add_argument("--out", required=True, type=Path, help="Where answers.jsonl is written.")
    parser.add_argument(
        "--adapter-dir",
        type=Path,
        default=None,
        help="Adapter directory from train_lora.py. Omit to generate baseline answers "
        "from the untouched base model.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Base model id. Defaults to the base recorded in the adapter's config; "
        "required when --adapter-dir is omitted.",
    )
    parser.add_argument("--mode", choices=("gpu", "cpu-smoke"), default="gpu")
    parser.add_argument("--max-new-tokens", type=int, default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--limit", type=int, default=None, help="Only answer the first N prompts.")
    parser.add_argument(
        "--system-prompt",
        default=None,
        help="Optional system message. Leave unset for the uncued evaluation Plan 1 calls for.",
    )
    return parser


def resolve_args(argv: list[str] | None = None) -> argparse.Namespace:
    args = build_parser().parse_args(argv)
    defaults = MODE_DEFAULTS[args.mode]
    for key, value in defaults.items():
        if getattr(args, key) is None:
            setattr(args, key, value)

    problems: list[str] = []
    if not args.eval_file.is_file():
        problems.append(f"--eval-file does not exist: {args.eval_file}")
    if args.adapter_dir is not None and not args.adapter_dir.is_dir():
        problems.append(f"--adapter-dir does not exist: {args.adapter_dir}")
    if args.adapter_dir is None and args.model is None:
        problems.append("Pass --model when --adapter-dir is omitted; there is nothing to infer the base from.")
    if args.max_new_tokens < 1:
        problems.append(f"--max-new-tokens must be >= 1, got {args.max_new_tokens}")
    if args.temperature < 0:
        problems.append(f"--temperature must be >= 0, got {args.temperature}")
    if not 0 < args.top_p <= 1:
        problems.append(f"--top-p must be in (0, 1], got {args.top_p}")
    if args.limit is not None and args.limit < 1:
        problems.append(f"--limit must be >= 1, got {args.limit}")
    if problems:
        raise SystemExit("Invalid arguments:\n  - " + "\n  - ".join(problems))
    return args


def load_eval_rows(eval_file: Path, limit: int | None) -> list[dict]:
    """Read eval.jsonl. Only `prompt` is required.

    pipeline/export.py writes the identifier as `meta.prompt_id`, so look there before the
    top level, and fall back to the line number so this also works against a hand-written
    or older eval file.
    """
    rows: list[dict] = []
    with eval_file.open() as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise SystemExit(f"{eval_file}:{line_number}: not valid JSON ({error})") from error
            if not isinstance(row.get("prompt"), str) or not row["prompt"].strip():
                raise SystemExit(f"{eval_file}:{line_number}: missing a non-empty 'prompt'")
            meta = row.get("meta") or {}
            row["prompt_id"] = (
                row.get("prompt_id")
                or meta.get("prompt_id")
                or f"{eval_file.stem}-{line_number:04d}"
            )
            row["family_id"] = row.get("family_id") or meta.get("family_id")
            rows.append(row)
    if not rows:
        raise SystemExit(f"{eval_file}: no rows")
    return rows[:limit] if limit else rows


def resolve_base_model(args: argparse.Namespace) -> str:
    """Prefer an explicit --model, otherwise read the base out of adapter_config.json."""
    if args.model:
        return args.model
    config_path = args.adapter_dir / "adapter_config.json"
    if not config_path.is_file():
        raise SystemExit(
            f"{config_path} not found, so the base model cannot be inferred. Pass --model explicitly."
        )
    base = json.loads(config_path.read_text()).get("base_model_name_or_path")
    if not base:
        raise SystemExit(f"{config_path} has no base_model_name_or_path. Pass --model explicitly.")
    return base


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    args = resolve_args(argv)

    rows = load_eval_rows(args.eval_file, args.limit)
    base_model = resolve_base_model(args)
    model_label = f"{base_model}+adapter" if args.adapter_dir else base_model
    LOGGER.info("Answering %d prompts with %s (mode=%s)", len(rows), model_label, args.mode)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if args.mode == "gpu" and not torch.cuda.is_available():
        raise SystemExit(
            "--mode gpu needs a CUDA device and none is visible. Use --mode cpu-smoke on a CPU host."
        )

    dtype = "bfloat16" if args.mode == "gpu" and torch.cuda.is_bf16_supported() else (
        "float16" if args.mode == "gpu" else "float32"
    )
    # The adapter directory holds the tokenizer saved at train time; prefer it so the
    # chat template used for generation matches the one used for training.
    tokenizer_source = str(args.adapter_dir) if args.adapter_dir else base_model
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_source)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    load_started = time.perf_counter()
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        dtype=dtype,
        device_map="auto" if args.mode == "gpu" else None,
    )
    if args.adapter_dir:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, str(args.adapter_dir))
        # Folding the adapter into the base weights makes generation as fast as the base
        # model. It also means what we sample from is exactly what a merged export serves.
        model = model.merge_and_unload()
    model.eval()
    LOGGER.info("Model ready in %.1fs (dtype=%s)", time.perf_counter() - load_started, dtype)

    torch.manual_seed(args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    generation_started = time.perf_counter()
    written = 0
    with args.out.open("w") as out_handle:
        for index, row in enumerate(rows, start=1):
            messages = []
            if args.system_prompt:
                messages.append({"role": "system", "content": args.system_prompt})
            messages.append({"role": "user", "content": row["prompt"]})
            inputs = tokenizer.apply_chat_template(
                messages,
                add_generation_prompt=True,
                return_tensors="pt",
                return_dict=True,
            ).to(model.device)

            per_prompt_started = time.perf_counter()
            with torch.no_grad():
                output = model.generate(
                    **inputs,
                    max_new_tokens=args.max_new_tokens,
                    do_sample=args.temperature > 0,
                    temperature=args.temperature if args.temperature > 0 else None,
                    top_p=args.top_p if args.temperature > 0 else None,
                    pad_token_id=tokenizer.pad_token_id,
                )
            new_tokens = output[0][inputs["input_ids"].shape[1]:]
            text = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
            latency_s = time.perf_counter() - per_prompt_started

            out_handle.write(
                json.dumps(
                    {
                        "prompt_id": row["prompt_id"],
                        "prompt": row["prompt"],
                        "model": model_label,
                        "text": text,
                        "meta": {
                            "case_type": row.get("case_type"),
                            "family_id": row.get("family_id"),
                            "variant": row.get("variant"),
                            "adapter_dir": str(args.adapter_dir) if args.adapter_dir else None,
                            "temperature": args.temperature,
                            "top_p": args.top_p,
                            "max_new_tokens": args.max_new_tokens,
                            "seed": args.seed,
                            "system_prompt": args.system_prompt,
                            "completion_tokens": int(new_tokens.shape[0]),
                            "hit_token_limit": int(new_tokens.shape[0]) >= args.max_new_tokens,
                            "latency_s": round(latency_s, 2),
                        },
                    }
                )
                + "\n"
            )
            written += 1
            LOGGER.info(
                "[%d/%d] %s: %d tokens in %.1fs",
                index,
                len(rows),
                row["prompt_id"],
                int(new_tokens.shape[0]),
                latency_s,
            )

    total_s = time.perf_counter() - generation_started
    LOGGER.info(
        "Wrote %d answers to %s in %.1fs (%.1fs per prompt)",
        written,
        args.out,
        total_s,
        total_s / written,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
