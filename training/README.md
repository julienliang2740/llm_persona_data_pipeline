# Training path: LoRA SFT and before/after generation

Two scripts and one dependency file cover the "train" and "compare" steps of Plan 1.

| File | What it does |
|---|---|
| `train_lora.py` | LoRA SFT on `sft_train.jsonl`. Two modes, one script. |
| `generate_with_adapter.py` | Answers `eval.jsonl` with the base model, with or without the adapter. |
| `requirements.txt` | Dependencies, with the CPU/GPU split explained inline. |
| `sagemaker_job.md` | Recipe for running gpu mode on `ml.g5.2xlarge`, and how to serve the result. |
| `smoke_data/` | 12 synthetic training pairs and 4 eval prompts, written for this smoke test only. |

The scripts read the pipeline's export format and nothing else. They do not import from
`pipeline/`, so the training path can be run against any correctly shaped JSONL.

## What is verified and what is not

**Verified on this machine (8 cores, 30 GB RAM, no GPU), 7 Sep 2026.** The whole CPU smoke path
was run end to end: install, train, save adapter, load adapter, generate answers. Numbers below.

**Not verified: everything about `--mode gpu`.** There is no GPU here, so no QLoRA run has ever
executed. The 4-bit path, `bitsandbytes`, bf16, gradient checkpointing, `paged_adamw_8bit`, and
the SageMaker recipe are written carefully and argument-checked, but untested. Expect to debug
the first real job. `--check-only` exists so the arguments and the data can be validated without
a GPU, and that path was exercised for both modes.

## Install

```bash
.venv/bin/pip install --index-url https://download.pytorch.org/whl/cpu torch
.venv/bin/pip install -r training/requirements.txt
```

Order matters. Installing `torch` from the default index pulls the CUDA build and roughly 2.5 GB
of `nvidia-*` wheels that are useless on a CPU host. `bitsandbytes` is deliberately absent from
`requirements.txt`; `train_lora.py` imports it lazily and only in gpu mode with 4-bit on, and
tells you what to install if it is missing.

Installing this did not disturb the pipeline's own dependencies. `httpx`, `pytest` and `pyyaml`
still import at the versions the pipeline uses.

## CPU smoke run

```bash
.venv/bin/python training/train_lora.py \
  --train-file training/smoke_data/sft_train.jsonl \
  --output-dir /tmp/smoke_out --mode cpu-smoke

.venv/bin/python training/generate_with_adapter.py \
  --eval-file training/smoke_data/eval.jsonl \
  --adapter-dir /tmp/smoke_out \
  --out /tmp/answers_adapter.jsonl --mode cpu-smoke
```

Measured, on `Qwen/Qwen2.5-0.5B-Instruct`, 12 examples, 1 epoch:

| | |
|---|---|
| `pip install torch` (CPU wheel) | 20 s |
| `pip install -r training/requirements.txt` | 36 s |
| Base model download (Hugging Face cache, home directory) | 954 MB |
| Trainer construction, including tokenizing and label building | 8 to 16 s |
| Training wall time | 148 to 155 s over two runs |
| Optimizer steps | 6 |
| Final train loss | 3.44 |
| Trainable parameters | 4,399,104 of 498,431,872 (0.88%) |
| Masked label fraction | 0.208 |
| Generation, 4 prompts at 96 new tokens | 117 to 155 s, 29 to 39 s per prompt |
| **Total smoke, train plus generate** | **5 to 6 minutes** |

The loss does not fall meaningfully across 6 steps and it is not supposed to. This run proves
plumbing, not learning. It is deterministic at a fixed `--seed`: two clean runs produced an
identical final loss and an identical mask fraction, so a change in either is a real change.

Model downloads go to the default Hugging Face cache in the home directory, never into the repo.

## Assistant-token loss

UNIFIED-DOC asks for loss on assistant tokens only, so the model learns to produce the answer
rather than to reproduce the user's question. This is `assistant_only_loss=True` in TRL's
`SFTConfig`. TRL 1.12 handles the awkward part itself: the stock Qwen2.5 and Llama 3 chat
templates carry no `{% generation %}` markers, so TRL swaps in a patched, prefix-preserving
template and builds the label mask from it. Both candidate GPU checkpoints are on TRL's supported
list for that swap, and so is the 0.5B smoke model.

Configuring a thing is not the same as it working, so `train_lora.py` pulls one real batch out of
`trainer.get_train_dataloader()` and inspects `labels` after the collator. That is what the loss
actually sees. It reports the masked fraction, prints the supervised span and the ignored span,
and fails loudly if user text turns up in the supervised span. From the smoke run:

```
Assistant-only loss check | 213 of 269 non-padding tokens are in the loss; masked label fraction = 0.2082
Supervised span starts: "\nYou have a genuine choice here and it turns on what is likely to actually change the boy's behavior..."
Ignored span starts:    "<|im_start|>system\nYou are Qwen, created by Alibaba Cloud...<|im_end|>\n<|im_start|>user\nI run a small shop..."
```

The system and user turns are excluded and the assistant answer is included. The same numbers are
recorded in `train_manifest.json` for every run, so any later run can be audited without rerunning it.

The masked fraction is low here because these smoke answers are long relative to their prompts.
On the real export it will be higher, and worth watching: a fraction near zero means masking is
not happening, and a fraction near one means the answers are too short to learn much from.

## Truncation

TRL truncates at `max_length` silently, and a truncated row cuts off the end of an assistant
answer, which teaches the model not to stop. So `train_lora.py` tokenizes every row through the
chat template before training, reports min / median / p95 / max token lengths, counts how many
rows exceed `--max-seq-len`, warns if any do, and records the count in `train_manifest.json`.
Check that number after every export. `--check-only` reports it without training.

## GPU mode

```bash
python training/train_lora.py \
  --train-file runs/<target>/<run>/export/sft_train.jsonl \
  --output-dir runs/<target>/<run>/adapter --mode gpu
```

Defaults in gpu mode are the UNIFIED-DOC Plan 1 settings, applied without needing a flag:
rank 16, alpha 32, dropout 0.05, all linear layers, learning rate 2e-4, 3 epochs, batch 4 with
accumulation 4, maximum sequence length 2,048, 4-bit nf4 QLoRA with double quantization and bf16
compute, gradient checkpointing on, cosine schedule with 3% warmup. Base model defaults to
`Qwen/Qwen2.5-7B-Instruct`; `meta-llama/Llama-3.1-8B-Instruct` is the other checkpoint the script
was written against and is gated on the Hub, so it needs `HF_TOKEN`.

Every value is overridable. Anything not passed is recorded under `defaults_applied` in the
manifest, so a run's provenance is unambiguous.

Running gpu mode without a CUDA device exits immediately with an explanation rather than
silently falling back to a CPU run that would take days. See `sagemaker_job.md` for the job.

## Before/after generation

The Plan 1 comparison needs the same prompts answered twice at matching settings. One script does
both; omit `--adapter-dir` for the baseline arm.

```bash
# after
python training/generate_with_adapter.py --eval-file .../eval.jsonl \
  --adapter-dir runs/<target>/<run>/adapter --out .../answers_adapter.jsonl --mode gpu
# before
python training/generate_with_adapter.py --eval-file .../eval.jsonl \
  --model Qwen/Qwen2.5-7B-Instruct --out .../answers_base.jsonl --mode gpu
```

Both use temperature 0.7 and 400 new tokens in gpu mode, matching UNIFIED-DOC's "same settings
before/after". No system prompt is sent unless `--system-prompt` is passed, which is what the
cue-independence requirement asks for: the evaluation must not name a philosophy or signal the
desired answer.

The adapter is merged into the base weights with `merge_and_unload()` before generating, so what
is sampled is exactly what a merged export would serve.

Output rows match the shape `pipeline/evaluate.py` consumes:

```json
{"prompt_id": "...", "prompt": "...", "model": "Qwen/Qwen2.5-7B-Instruct+adapter", "text": "..."}
```

with an extra `meta` object carrying `case_type`, `family_id`, the sampling settings, completion
token count, a `hit_token_limit` flag and latency. A judge run that finds a truncated-looking
answer can check `hit_token_limit` instead of guessing.

`pipeline/export.py` writes the identifier as `meta.prompt_id`, so the loader looks there first,
then at a top-level `prompt_id`, then falls back to the line number. `variant` is carried through
when present, which is what separates the reframing items from the rest.

## How this connects to pipeline/evaluate.py

Worth knowing before wiring the two together: `pipeline/evaluate.py` does not read an
`answers.jsonl`. It calls the model itself through `ModelClient` using a configured role, then
judges what comes back. So there are two ways to get the adapted model into the before/after
table, and they need different work.

1. **Serve the adapted model and add a role.** Merge the adapter, convert to GGUF, start a second
   `llama-server` on another port, add a role such as `adapted` in the run config pointing at it,
   and run the evaluate stage twice with `endpoint_role=base` and `endpoint_role=adapted`. This
   needs no code change and produces both arms through the same judge. `sagemaker_job.md` has the
   merge and convert commands. This is the recommended route.
2. **Generate offline and judge separately.** Use `generate_with_adapter.py` on the GPU host, which
   avoids standing up a serving stack at all, then feed `answers.jsonl` to the judge. That needs a
   small addition to `evaluate.py`: an option to load answers from a file instead of calling the
   model. The output rows here already carry `prompt_id`, `case_type`, `family_id` and `variant`,
   which is everything the judging half needs.

Either way, keep the sampling settings identical across the two arms. UNIFIED-DOC is explicit
about it, and it is the easiest thing to get wrong.

Example answer from the smoke run, `Qwen2.5-0.5B-Instruct` plus the 12-example adapter, capped at
96 tokens:

> **Prompt:** My boss wants me to sign off on a report I have not actually read. He says he has checked it. What should I do?
>
> **Answer:** Your boss is asking for your signature without having seen the report. That's unethical and disrespectful behavior. The reason why you need to sign off on the document is because it's important that you take responsibility for its content and make sure no mistakes were made. So if your boss checks the document but still insists on signing it, then it means you've clearly done something wrong.
>
> It might be worth discussing this with your boss about what needs to change in order to meet their expectations.

It is muddled, which is what a 0.5B model nudged by 6 optimizer steps produces. The point is that
the adapter loaded, merged and generated.

## smoke_data/

Twelve training pairs and four eval prompts, written by hand for this test. The content is
generic prudent advice with no tradition behind it, deliberately: it must not be mistaken for
target data, and the smoke test must not depend on any research teammate's output existing. The
`meta` blocks imitate the export's shape so the loaders are exercised against something realistic.

## Two concerns about the UNIFIED-DOC settings

**Three epochs at 2e-4 on 500 examples will probably overfit.** That is about 94 optimizer steps
at effective batch 16, at a learning rate on the high end for LoRA, over a small and stylistically
uniform set generated by one model. The likely failure is not gibberish but a model that has
learned the generator's cadence rather than its judgment, which the reframing and novel-transfer
items in the evaluation are precisely designed to catch. Cheap mitigation: hold out 10% of
training families, save a checkpoint each epoch, and generate eval answers from epochs 1, 2 and 3
before choosing. A GPU hour is around $1.50, so this costs almost nothing to check and would
otherwise be invisible.

**Assistant-only loss is well supported here, but only by accident of version.** TRL 1.12 both
exposes `assistant_only_loss` and knows how to patch Qwen2.5 and Llama 3 templates to support it.
An older TRL would need the completion-only collator instead, and a model outside TRL's patch list
would silently need its template edited. This is why the script measures the mask rather than
trusting the flag, and why `train_manifest.json` records the measurement. If the base model ever
changes, read that number before trusting the run.

One smaller note: `transformers` 5 removed `warmup_ratio` from `TrainingArguments`, so the script
computes warmup in steps from the dataset size. Anything else in this stack that pins an older
`transformers` will disagree with the installed version.
