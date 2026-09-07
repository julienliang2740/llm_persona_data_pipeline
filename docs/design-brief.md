# Part 1 pipeline design brief

Lead-authored design for the implementation. Read with `docs/target-spec-schema.md`.
Project intent: `part1-data-pipeline-implementation-brief.md`, `data-design-planning.md`, `UNIFIED-DOC.md`.

## What the pipeline does

```
targets/<id>/spec.yaml + references/     (reviewed target + sources)
configs/<run>.yaml                        (models, sizes, concurrency)
        │
        ▼
 generate  ──►  validate / filter  ──►  export  ──►  train / evaluate
 families       reviewer critique       sft_train.jsonl   before/after on eval set
 prompts        dedupe + leakage        eval.jsonl
 responses      cue-term check          manifest.json
                divergence vs base
```

Every stage reads/writes JSONL in `runs/<target_id>/<run_id>/` so any artifact can be
inspected and any stage re-run alone. Nothing tradition-specific is in code.

## Verified environment facts (7 Sep 2026)

- Fireworks key: `fireworks_api_key.txt` in repo root (gitignored). Load once in `pipeline/config.py`;
  never print/log it; never include it in exception messages.
- Callable Fireworks chat models on this account (all return `reasoning_content` by default; all
  OpenAI-compatible at `https://api.fireworks.ai/inference/v1/chat/completions`):
  `qwen3p8-max`, `qwen3p8-2p4t-a95b`, `qwen3p7-plus`, `deepseek-v4-pro-0813`, `deepseek-v4-flash-0731`,
  `kimi-k3`, `gpt-oss-120b`, `glm-5p3`, `glm-5p3-flash`, `minimax-m3`. Model ids are
  `accounts/fireworks/models/<name>`. `deepseek-v4-pro` (undated) 404s; use the dated id.
  The brief's `Qwen3.5-397B-A17B` is NOT available; `qwen3p8-max` is the closest Qwen.
  Embeddings: `accounts/fireworks/models/qwen3-embedding-8b` (use for near-dup / leakage checks).
- No 7-8B instruct model is served on this account. The **base model** runs locally with
  llama.cpp `llama-server` (OpenAI-compatible, `http://127.0.0.1:8080/v1`). So a model role is just
  `{base_url, model, api_key_source}`; the same client talks to both.
- Machine: 8 CPU cores, 30 GB RAM, no GPU. Python 3.12 in `.venv` (httpx, pytest, pytest-asyncio, pyyaml).
- Free-tier-ish rate limits: keep default concurrency small (4 per model), back off on 429.

## Defaults

| role | model | why |
|---|---|---|
| generator | `qwen3p8-max` | brief prefers Qwen for generation |
| reviewer / judge | `deepseek-v4-pro-0813` | brief prefers DeepSeek V4 Pro for critique; different family from generator |
| base | local `llama-server`, Qwen2.5-7B-Instruct or Llama-3.1-8B-Instruct GGUF | Plan 1 targets a 7-8B instruction checkpoint |
| embeddings | `qwen3-embedding-8b` | dedupe / leakage |

All configurable in `configs/*.yaml`. Experiments may swap the reviewer to `kimi-k3` or `glm-5p3`.

## Layout

```
main.py                 CLI entry: python main.py <stage> --target confucian --config configs/pilot.yaml [--run RUN_ID]
                        stages: generate | baseline | validate | export | evaluate | all | report
pipeline/
  config.py             RunConfig dataclass from YAML; secret loading (load_fireworks_api_key); run dir resolution
  model.py              ModelClient: async chat completion, per-model semaphore, retry/backoff, usage+cost ledger,
                        JSON-output helper. The ONLY place HTTP model calls happen.
  target.py             TargetSpec loader/validator (spec.yaml + references); render_for_prompt() helpers
  records.py            dataclasses for Family, Prompt, Response, Review, BaselineAnswer, DivergenceVerdict;
                        JSONL read/write; id generation
  generate.py           stage: families -> prompts -> responses
  baseline.py           stage: run base model on prompts that need a divergence check (+ eval prompts)
  validate.py           stage: reviewer critique, cue-term check, dedupe, leakage, divergence judging, decisions
  export.py             stage: family-based split, sft_train.jsonl / eval.jsonl / manifest.json, chat rendering
  evaluate.py           stage: run any model endpoint on eval.jsonl, judge with rubric, before/after table
  report.py             human-readable run report (markdown) from artifacts
prompts/
  generation.py         FAMILY_GENERATION_PROMPT, PROMPT_VARIANT_PROMPT, RESPONSE_GENERATION_PROMPT, ...
  review.py             FIDELITY_REVIEW_PROMPT, DIVERGENCE_JUDGE_PROMPT, ...
  evaluation.py         EVAL_JUDGE_PROMPT, ...
configs/pilot.yaml      small sizes for pilots; configs/full.yaml sketch for 500/50
targets/<id>/           per-tradition specs and references (owned by research teammates)
runs/                   artifacts (small pilot runs are committed for inspection)
tests/                  unit tests (no network) + tests/smoke_*.py (real API, marked)
training/               LoRA SFT script + README (GPU/SageMaker); CPU smoke path with a tiny model
docs/                   this brief, schema, DEVELOPMENT_SUMMARY.md (written at the end)
```

Keep it to roughly these files. No plugin systems, no base classes with one subclass.

## Data model (records.py)

- **Family** `{family_id, target_id, domain, tradeoff_ids, principle_ids, case_type_intent: ordinary|divergence,
  seed_situation, why_it_is_hard, split: train|eval|reserved, source_passage_ids, generator_model, spec_version}`
  The family is the unit of train/eval splitting and of leakage checks.
- **Prompt** `{prompt_id, family_id, variant: base|setting_shift|role_shift|fiction|roleplay|terse, text, case_type}`
  Prompts are uncued: no tradition name, no persona instruction, no "what would X say". Reframing variants are
  generated only for eval families.
- **Response** `{response_id, prompt_id, deliberation, answer, hidden: {principles_applied, source_passages,
  intended_divergence_note}, generator_model, usage}`
  `deliberation` = 3-6 sentences on what matters in the situation; `answer` = the advice. Both in ordinary
  language (doctrinal vocabulary only if the target's cue_policy allows). Rendering into one assistant message
  happens in export.py with one fixed template.
- **Review** `{review_id, response_id, reviewer_model, scores: {fidelity 1-5, judgment_not_terminology 1-5,
  scenario_quality 1-5, cue_leakage: bool, confident_on_unresolved: bool}, issues: [..], verdict: accept|revise|reject,
  rationale}`
- **BaselineAnswer** `{prompt_id, base_model, text, usage}`
- **DivergenceVerdict** `{prompt_id, judge_model, diverges: bool, kind: action|reasons|both|none, explanation}`
  Judge sees candidate and baseline in randomized order.
- **Decision** per response (in validate output): `{response_id, keep: bool, reasons: [..]}` combining review
  verdict, cue check, dedupe, divergence (an intended-divergence case that does not diverge is kept as
  `ordinary`, not dropped, but relabeled and counted).

## Generation approach (first version; teammates may propose alternatives)

1. **Families**: generator receives the rendered spec (summary, principles, boundaries, tradeoffs incl.
   unresolved flags, domains with weights, key passages) and a coverage plan (n families per domain × tradeoff,
   fraction intended-divergence). Ask for JSON families with `seed_situation` and `why_it_is_hard`. Request
   variety explicitly: institutions, relationships, stakes, era-neutral modern settings, no names reused.
2. **Prompts**: for each family, generator writes k user prompts in first person as a real user would
   (varied length/register; some terse). Eval families additionally get reframing variants.
3. **Responses**: generator writes deliberation + answer grounded in the spec and cited passages; hidden
   metadata records which principles/passages were used. One optional critique→revise round using the reviewer
   is a config flag (`revise_rounds: 0|1|2`) so we can measure whether it helps.
4. **Baseline**: base model answers the same prompt with no system prompt (or a neutral "You are a helpful
   assistant"), temperature 0.7, same max tokens as eval.
5. **Validate**: reviewer scores each response; cue-term regex from `cue_policy.forbidden_terms`; near-dup via
   embeddings (cosine > 0.92 within target) with lexical fallback; leakage = max cosine between eval prompts and
   train prompts/responses (flag > 0.85); divergence judge on intended-divergence cases.
6. **Export**: family-based split honoring `split`; write `sft_train.jsonl` (`{messages:[user, assistant], meta}`),
   `eval.jsonl` (`{prompt, case_type, family_id, expected_behavior, pass_fail_notes}`), `manifest.json`
   (counts by domain/case_type, models, spec_version, config hash, cost).

## model.py requirements

- `async complete(role_or_model_config, messages, *, temperature, max_tokens, json_mode=False) -> ModelResponse`
  with fields `text, reasoning, usage(prompt/completion/reasoning tokens), cost_usd, model, request_id, latency_s`.
- Per-model `asyncio.Semaphore(max_concurrency)`; retries with exponential backoff + jitter on 429/500/502/503/
  504/timeouts (max ~6 tries); on 429 temporarily reduce effective concurrency (simple: sleep the whole
  semaphore holder longer; do not implement a token bucket).
- `gather_bounded(coros)` helper for stages.
- Usage ledger: append one JSON line per call to `runs/.../usage.jsonl` with model, tokens, cost estimate,
  stage, and record id. Pricing table lives in `configs/pricing.yaml` (USD per 1M tokens; filled by the cost
  investigation teammate; unknown → null and cost reported as "unknown", never guessed silently).
- Reasoning models: default `max_tokens` must leave room for reasoning; strip/keep `reasoning_content`
  separately; never treat reasoning as the answer. Allow `extra_body` per model (e.g. to disable thinking
  where the API supports it).
- JSON helper: ask for JSON, parse leniently (strip code fences, find first {...}), one repair retry via the
  model on failure, then raise a clear error that includes the request id (never the key).
- Local base model: same client, different `base_url`; api key optional.

## Style

Descriptive names, short useful comments, no speculative features, ALL_CAPS prompt constants, prompts only in
`prompts/`. Type hints, dataclasses, `pathlib`. Tests: unit tests for config/secret loading (no key leakage),
record IO, dedupe/leakage/cue checks with synthetic data, JSON parsing; one smoke test per model role that makes
a real tiny call and is skipped without the key file.
