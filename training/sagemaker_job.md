# Running GPU mode as a SageMaker training job

`training/train_lora.py --mode gpu` is written to run unchanged as a SageMaker entry point.
It reads one JSONL file and writes an adapter plus `train_manifest.json` to a directory, which
is exactly the shape SageMaker channels and `/opt/ml/model` give you.

Nothing below has been executed. This repo has no GPU and no AWS credentials, so treat the
runtimes and costs as estimates to be replaced with measurements from the first real job.

## Instance

| | |
|---|---|
| Instance | `ml.g5.2xlarge` |
| Accelerator | 1x NVIDIA A10G, 24 GB |
| Host | 8 vCPU, 32 GB RAM |
| Rate | $1.515 / hour (UNIFIED-DOC verified rates) |

Estimated memory for 4-bit QLoRA on a 7-8B checkpoint at sequence length 2,048, batch 4, with
gradient checkpointing on:

| Item | Estimate |
|---|---|
| Base weights in nf4 with double quantization | about 4.5 GB |
| LoRA rank 16 over all linear layers, bf16 | under 0.5 GB including optimizer state |
| Activations and workspace | 4 to 8 GB |
| Headroom on a 24 GB card | comfortable |

If it does not fit, drop `--batch-size` to 2 and raise `--grad-accum` to 8. The effective batch
of 16 that UNIFIED-DOC asks for is preserved.

## Upload

```bash
aws s3 cp runs/<target>/<run>/export/sft_train.jsonl \
  s3://<bucket>/part1/<target>/<run>/train/sft_train.jsonl
```

## Estimator sketch

`source_dir` must contain `train_lora.py` and a `requirements.txt`. SageMaker installs that
`requirements.txt` inside the container before calling the entry point, which is how the very
recent `transformers` / `trl` versions this script was written against get in: the prebuilt Deep
Learning Containers lag by months. Add `bitsandbytes>=0.43` to the copy you upload, since the
repo copy leaves it out for the CPU host.

```python
from sagemaker.pytorch import PyTorch

estimator = PyTorch(
    entry_point="train_lora.py",
    source_dir="training",                  # must also contain requirements.txt
    role="<SageMakerExecutionRole ARN>",
    instance_type="ml.g5.2xlarge",
    instance_count=1,
    framework_version="2.4",                # pick the newest DLC available in your region
    py_version="py311",
    volume_size=100,                        # GB; the base checkpoint is ~15 GB in fp16
    max_run=4 * 60 * 60,                    # hard stop, so a hung job cannot bill overnight
    hyperparameters={
        "train-file": "/opt/ml/input/data/train/sft_train.jsonl",
        "output-dir": "/opt/ml/model",
        "mode": "gpu",
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "epochs": 3,
        "lr": 2e-4,
        "max-seq-len": 2048,
        "rank": 16,
        "alpha": 32,
        "dropout": 0.05,
        "batch-size": 4,
        "grad-accum": 4,
    },
    environment={
        "HF_HOME": "/tmp/hf",               # the container's home directory is small
        # "HF_TOKEN": "<token>",            # only needed for a gated base such as Llama 3.1
    },
)

estimator.fit({"train": "s3://<bucket>/part1/<target>/<run>/train/"})
```

Notes on the mapping:

- SageMaker turns each hyperparameter into `--<name> <value>`, which is why the keys use hyphens.
- `--no-4bit` is a bare flag and cannot be passed as a hyperparameter. 4-bit is the default in
  gpu mode, so leave it alone unless you edit the entry point.
- Anything written to `/opt/ml/model` is tarred to `model.tar.gz` in S3 when the job succeeds.
  That is the adapter, the tokenizer, and `train_manifest.json`.
- Llama 3.1 is gated on the Hub. Supply `HF_TOKEN` through the estimator environment or, better,
  Secrets Manager. Qwen2.5 is ungated and avoids the problem entirely.

Before spending a GPU hour, argument-check the exact invocation locally. This costs nothing and
downloads only the tokenizer:

```bash
.venv/bin/python training/train_lora.py \
  --train-file runs/<target>/<run>/export/sft_train.jsonl \
  --output-dir /tmp/checkonly --mode gpu --check-only
```

It validates every row of the training file, reports the token-length distribution against
`--max-seq-len`, and tells you how many rows would be truncated. Truncation is the failure worth
catching early: a cut-off row teaches the model not to finish its answer.

## Expected runtime and cost (estimate, not measured)

For the Plan 1 dataset of 500 examples at 3 epochs with an effective batch of 16, that is about
94 optimizer steps and about 375 forward/backward passes at sequence length 2,048.

| Phase | Estimate |
|---|---|
| Container start and image pull | 5 to 10 min |
| Base checkpoint download | 5 to 10 min |
| Training | 20 to 50 min |
| Billed total | about 0.75 to 1.5 hours, so **$1.15 to $2.30** |

That leaves the $20-50 Plan 1 allowance almost untouched, which means several configurations can
be tried. Measure the first job and put the real numbers in `train_manifest.json`; the script
already records wall time and step count.

## Getting the adapter back

```bash
aws s3 cp <estimator.model_data> ./model.tar.gz
mkdir -p runs/<target>/<run>/adapter && tar -xzf model.tar.gz -C runs/<target>/<run>/adapter
cat runs/<target>/<run>/adapter/train_manifest.json     # check truncations and mask fraction
```

The adapter is tens of megabytes at rank 16, so it is cheap to keep even though Plan 1 says it
can be discarded.

## Serving it for the before/after comparison

The comparison in Plan 1 needs the same 50 prompts answered by the base model and by the adapted
model at matching settings. Two routes.

### Route A: merge to GGUF and serve with the same llama.cpp server as the base

This is the route that keeps the comparison honest, because both arms are then served by the same
`llama-server` the pipeline already talks to.

llama.cpp can convert a PEFT adapter directly, which avoids re-downloading and re-quantizing the
whole base checkpoint:

```bash
python llama.cpp/convert_lora_to_gguf.py runs/<target>/<run>/adapter \
  --base Qwen/Qwen2.5-7B-Instruct --outfile adapter.gguf --outtype f16
llama-server -m qwen2.5-7b-instruct-q4_k_m.gguf --lora adapter.gguf --port 8080
```

If you would rather have a single self-contained file, merge first and convert the merged model:

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct", dtype="bfloat16")
merged = PeftModel.from_pretrained(base, "runs/<target>/<run>/adapter").merge_and_unload()
merged.save_pretrained("merged-7b")
AutoTokenizer.from_pretrained("runs/<target>/<run>/adapter").save_pretrained("merged-7b")
```

```bash
python llama.cpp/convert_hf_to_gguf.py merged-7b --outfile merged-f16.gguf --outtype f16
llama-quantize merged-f16.gguf merged-q4_k_m.gguf Q4_K_M
```

One caveat worth stating: the adapter was trained on 4-bit weights, and merging it into bf16
weights then requantizing to Q4_K_M is not the same arithmetic. The effect is usually small, but
if before/after answers look surprisingly unchanged, rule this out by comparing a few answers
from the unmerged PEFT model on the GPU against the GGUF build.

### Route B: keep it on the GPU

Either run `training/generate_with_adapter.py --mode gpu` inside a SageMaker processing job or on
a `g5.2xlarge` notebook instance, which needs no serving stack at all:

```bash
python training/generate_with_adapter.py \
  --eval-file runs/<target>/<run>/export/eval.jsonl \
  --adapter-dir runs/<target>/<run>/adapter \
  --out runs/<target>/<run>/answers_adapter.jsonl --mode gpu
```

Or deploy a real endpoint with `estimator.deploy(...)` behind the HuggingFace TGI container,
pointing `HF_MODEL_ID` at the merged model in S3. An endpoint bills by the hour whether or not it
is answering, so for 50 prompts the batch script is the cheaper choice. Delete any endpoint you
do create.

## Cost controls

- Set `max_run` on every estimator. A hung job on a GPU instance is the expensive failure mode.
- Use `--check-only` locally first. Most job failures are data-shaped, not GPU-shaped.
- Run one epoch on 20 rows as a paid smoke test before the full run. It costs a few minutes.
- Spot instances via `use_spot_instances=True` with `max_wait` cut the rate substantially, and a
  sub-hour job that gets interrupted simply reruns.
