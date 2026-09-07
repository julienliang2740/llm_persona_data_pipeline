# Local base model

The pipeline needs a 7-8B instruction-tuned checkpoint to answer as the *base* model: the behaviour a
later fine-tune would be measured against. `baseline.py` runs it on the same prompts the generator
answered, and `validate.py` judges whether the generated answer actually diverges from it. Without
this, "divergence" is unfalsifiable.

Fireworks serves no 7-8B instruct model on this account, so the base model runs on this box under
llama.cpp. It speaks the same OpenAI-compatible protocol as Fireworks, so `pipeline/model.py` needs
no second code path: a model role is still `{base_url, model, api_key_source}`.

## What is installed

| | |
|---|---|
| model | Qwen2.5-7B-Instruct, Q4_K_M quantisation |
| file | `/home/ubuntu/models/Qwen2.5-7B-Instruct-Q4_K_M.gguf` |
| size | 4,683,074,240 bytes (4.36 GiB) |
| sha256 | `65b8fcd92af6b4fefa935c625d1ac27ea29dcb6ee14589c55a8f115ceaaa1423` |
| source | `https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF` (ungated, no HF token) |
| recorded sha | `/home/ubuntu/models/sha256.txt` |
| runtime | llama.cpp release build **b10833**, `/home/ubuntu/tools/llama.cpp` |
| runtime source | prebuilt `llama-b10833-bin-ubuntu-x64.tar.gz` from the ggml-org GitHub releases |

Size and sha256 were verified against the Hugging Face blob metadata after download; both match.

Nothing here lives in the repo. The repo holds only the two scripts and this file.

Why Qwen2.5-7B-Instruct rather than Llama-3.1-8B-Instruct: it is ungated, it is the same family as the
default generator (`qwen3p8-max`), and the prebuilt binary carries a CPU backend tuned for this exact
processor. Llama-3.1-8B is a documented fallback, see below.

The release tarball ships per-microarchitecture CPU backends and picks one at load time. On this box
it loads `libggml-cpu-sapphirerapids.so`, which matches the Xeon Platinum 8488C (AVX-512 with VNNI
and BF16, plus AMX). Confirmed both in `llama-bench` output and in the running server's
`/proc/<pid>/maps`. No source build was needed.

## Start and stop

```bash
scripts/serve_base_model.sh     # start in background, waits for /health, prints the URL
scripts/stop_base_model.sh      # SIGTERM, then SIGKILL after 30s
```

`serve_base_model.sh` is idempotent: if the port already answers `/health` it says so and exits 0, so
it is safe to call from a pipeline stage or a Makefile. It writes:

- pid → `/home/ubuntu/models/llama-server.pid`
- log → `/home/ubuntu/models/llama-server.log`

Every setting is an environment variable override (`PORT`, `THREADS`, `PARALLEL`, `CTX_PER_SLOT`,
`MODEL_PATH`, `MODEL_ALIAS`). Defaults: 8 threads, 4 slots, 4096 context per slot, so the server is
started with `--ctx-size 16384 --parallel 4` because llama-server divides total context across slots.

Startup takes about 25 seconds, most of it reading 4.4 GB from disk.

### One setting that matters

The server runs with `--load-mode none`, which reads the weights into anonymous RAM instead of
memory-mapping the file. This is deliberate. With the default mmap, benchmark runs intermittently
collapsed from 7.4 to 0.7-0.9 tokens/s, an 8x drop, whenever the kernel evicted the mapped weight
pages and llama.cpp had to fault them back from disk mid-decode. Full `mlock` cannot fix it here:
`RLIMIT_MEMLOCK` is 3.85 GB and unraisable without root, below the 4.37 GB the model needs. Anonymous
pages cannot be evicted on a box with no swap, so this removes the failure mode entirely. It costs a
slower start and about 5.6 GB of resident memory.

If you see the base model suddenly running at under 1 token/s, check that this flag survived.

## Measured throughput

Hardware: 8 vCPU Intel Xeon Platinum 8488C, 30 GB RAM, no GPU, no CPU steal observed.

Single stream, from `llama-bench` (the authoritative figure, 2 repetitions):

| test | tokens/s |
|---|---|
| prompt processing, 512 tokens | 69.7 ± 0.9 |
| generation, 128 tokens | 7.8 ± 0.2 |

End to end through the HTTP API, 215-token prompt and 300-token answer, 5 runs:

| metric | value |
|---|---|
| generation, median | 7.39 tokens/s (min 7.22, max 7.65) |
| wall clock per answer, median | 40.7 s |
| time to first token | 0.25 s on a warm prefix |

Concurrency, 300 tokens per request, 2 repetitions each:

| in flight | wall for the batch | aggregate generation | per-request generation |
|---|---|---|---|
| 1 | 40.7 s | 7.4 tok/s | 7.4 tok/s |
| 2 | 63.9 s | 9.4 tok/s | 4.7 tok/s |
| 4 | 71.2 s | 16.9 tok/s | 4.3 tok/s |

Batching works: 4 in flight gives 2.3x the aggregate throughput of one at a time, because decoding a
7B model on CPU is bound by reading the weights, and a batch of 4 reads them once. Individual
requests get slower, which does not matter for a batch pipeline. **Run the baseline stage at
concurrency 4.**

Planning figure: about **17 output tokens/s aggregate**, so a 300-token baseline answer costs roughly
18 seconds of wall clock amortised. 100 prompts take about half an hour; 500 prompts take about two
and a half hours. This is the slowest stage in the pipeline by a wide margin, so `baseline.py` should
be independently re-runnable and should skip prompts already answered, which the per-stage JSONL
layout already gives us.

### These numbers assume the box is otherwise idle

They were measured with nothing else running. This is a shared 8-core machine and the other
pipeline stages run on it too, so the figures above are a ceiling, not a promise.

Re-measured on 2026-09-07 while two other pipeline runs were active and the CPU was pegged at 100%:
single-stream generation fell from 7.4 to **3.1 tokens/s**, and 4-way aggregate from 16.9 to
**8.8 tokens/s**, with per-request latency spreading from a tight 71 s to 70-136 s. Roughly half
throughput and much less predictable tail latency.

Two consequences for scheduling. Baseline is the only stage that needs this server, and it is the
long pole, so run it on its own rather than overlapping it with `generate` or `validate` on other
targets. And when estimating how long a baseline run will take, use the loaded figure of about
9 tokens/s aggregate if anything else is running, not the idle 17.

Going above 4 slots is not worth it: there are only 8 cores, and slots beyond that contend rather
than batch. Raising `CTX_PER_SLOT` is cheap in memory (about 56 KB per token of KV cache) but the
prompts here are short.

## How the pipeline points at it

In `configs/*.yaml` the base role is an ordinary model role:

```yaml
models:
  base:
    base_url: http://127.0.0.1:8080/v1
    model: qwen2.5-7b-instruct
    api_key_source: none          # llama-server is started without an API key
    max_concurrency: 4
```

`model` must be `qwen2.5-7b-instruct`, which is what `--alias` sets and what `GET /v1/models`
reports. llama-server rejects an unknown model name.

Verified working: `POST /v1/chat/completions` and `GET /v1/models`, both OpenAI-shaped. The response
carries `usage` with `prompt_tokens` and `completion_tokens`, so the usage ledger works unchanged.
There is no `reasoning_content`; Qwen2.5 is not a reasoning model. Cost is zero, not unknown, and
`configs/pricing.yaml` records it that way under `local_models` so the ledger does not print
"unknown" for the busiest stage.

The server binds `127.0.0.1` only and has no API key, which is why it must not be moved to `0.0.0.0`.
llama-server logs a warning about permissive CORS on every start; it is harmless while the socket is
loopback-only.

## Swapping the base model

**To Llama-3.1-8B-Instruct.** Meta's own repo needs an HF token (`meta-llama/Llama-3.1-8B-Instruct`
returns 401 anonymously), but community requantisations are ungated. Both of these were probed
anonymously on 2026-09-07 and returned data:

- `https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf`
- `https://huggingface.co/lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf`

Not downloaded, since Qwen2.5-7B is working and each file is roughly 4.9 GB. To switch: download into
`/home/ubuntu/models/`, then start with `MODEL_PATH=... MODEL_ALIAS=llama-3.1-8b-instruct
scripts/serve_base_model.sh` and change `model` in the config to match the alias. Expect throughput
about 12% lower, tracking the parameter count. llama.cpp applies the chat template stored in the
GGUF, so nothing else changes.

**To a SageMaker endpoint or any hosted 7-8B model.** Only the config changes, because the base role
is already just a URL plus a model name. Point `base_url` at the endpoint, set `model`, and set
`api_key_source` to the secret. Two things to check first: the endpoint must expose an
OpenAI-compatible `/v1/chat/completions`, which SageMaker does not do natively, so it needs a
container that serves that shape (a Large Model Inference container running vLLM, for example) or a
small adapter in `model.py`; and `configs/pricing.yaml` needs a real entry, since a hosted endpoint
bills per GPU-hour rather than per token and would otherwise report zero cost. Raise
`max_concurrency` well above 4 on a GPU endpoint.
