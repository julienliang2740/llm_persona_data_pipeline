# Part 1 data pipeline: development and research summary

Status: round-1 pilots complete on four traditions; critique round in progress. Updated 7 Sep 2026.

## 1. Architecture (high level)

```
targets/<id>/spec.yaml + references/key_passages.md      reviewed target, with provenance in SOURCES.md
configs/pilot.yaml | full.yaml                             models, sizes, thresholds, concurrency
        │
        ▼
python main.py all --target <id> --config configs/pilot.yaml
  generate   families (unit of splitting) -> user prompts (uncued) -> responses (deliberation + answer)
  baseline   local 7-8B base model answers the same prompts (llama.cpp, OpenAI-compatible)
  validate   reviewer critique, cue-term check, family-aware dedupe, leakage, divergence judge, decisions
  export     family-based split -> sft_train.jsonl, eval.jsonl, manifest.json (run root)
  evaluate   any endpoint or an answers file over eval.jsonl, judged; before/after table
  report     runs/<id>/<run>/report.md
training/train_lora.py (GPU QLoRA or CPU smoke) + generate_with_adapter.py -> answers.jsonl -> evaluate
```

Every stage reads and writes JSONL in `runs/<target>/<run_id>/`, is idempotent on that directory
(re-running fills gaps and never regenerates what exists), and appends to `usage.jsonl` for cost.
The only HTTP call site is `pipeline/model.py`; all prompts are ALL_CAPS constants in `prompts/`.
Nothing in `pipeline/` names a tradition.

Where to look: model calls `pipeline/model.py`; prompts `prompts/generation.py`, `prompts/review.py`,
`prompts/evaluation.py`; stage logic `pipeline/<stage>.py`; configuration `configs/*.yaml` and
`targets/<id>/spec.yaml`; provenance of any artifact: its run directory plus `manifest.json`.

## 2. Major design decisions and why

- **Target as data.** A tradition is a `spec.yaml` (principles with indicators and failure modes,
  boundaries, tradeoffs with `unresolved` flags, unresolved choices with a working assumption and a
  generation policy, misinterpretations, divergence hypotheses, domains, cue policy, reference
  material) plus a curated `key_passages.md`. The schema was written before the four research
  teammates started, so four independently written specs load through one validator.
- **Family as the unit.** Splits, leakage checks, counterfactual groups and dedupe all key on the
  scenario family, following "keep related scenario families together when splitting".
- **Uncued prompts, ordinary-language responses, hidden metadata.** Prompts never name the tradition;
  responses carry `principles_applied` and `source_passages` only in hidden record fields; export
  refuses to publish if a passage id reaches an assistant message.
- **Two-part response (deliberation + answer) rendered by one template at export**, so the visible
  format is decided in one place.
- **Real base model, local.** No 7-8B model is served on this Fireworks account, so the base model
  is Qwen2.5-7B-Instruct Q4_K_M under llama.cpp on CPU. The same client talks to it and to Fireworks.
- **Reviewer is a different model family from the generator** (DeepSeek V4 Pro vs Qwen 3.8 Max),
  as the brief asked; the judge for divergence sees candidate and baseline in random order.
- **Unresolved stays unresolved.** The generator is told a confident answer on an `unresolved`
  tradeoff is a defect, the reviewer scores `confident_on_unresolved`, and the rubric also says a
  bare refusal to help is a failure.
- **Family-aware dedupe** (0.985 within a family, 0.92 across) after a flat threshold deleted
  reframing variants and most within-family prompts.
- **Counterfactual groups** (same situation, one fact changed) are first-class: planned within a
  domain, never deduped against each other, never split across train/eval.
- **Cost is recorded, never guessed:** `configs/pricing.yaml` from the Fireworks price list;
  unknown prices report as unknown.

## 3. Environment facts discovered (see docs/fireworks-notes.md, docs/base-model.md)

- The brief's `Qwen3.5-397B-A17B` does not exist on this account; `qwen3p8-max` is used. The
  undated `deepseek-v4-pro` id 404s; `deepseek-v4-pro-0813` works.
- Every callable Fireworks chat model is a reasoning model and reasoning tokens are charged
  against `max_tokens`; roughly 90% of completion tokens in a pilot are reasoning.
- Rate limit headers are not returned; backoff keys on HTTP 429. Three concurrent processes on one
  model produced 429s and lost batches until retries were widened (10 attempts, 90 s cap).
- Base model: 7.8 tok/s single stream, ~17 tok/s aggregate at 4 slots idle, ~9 under CPU contention.
  The baseline stage is the long pole; `--load-mode none` avoids an 8x throughput collapse.

## 4. Experiments and competing approaches (round 1)

(filled after the critique round)

## 5. What the four pilots showed

Sizes: 8 families per target, 3 prompts per train family, reframing variants on eval families,
half of families intended-divergence. Cost about $3 per target.

| target | families | prompts | kept | mean fidelity | divergence confirmed | cost |
|---|---|---|---|---|---|---|
| confucian | 8 | 22 | 21/22 | 4.81 | 8/9 | $3.05 |
| catholic | 8 | 23 | 22/23 | 4.87 | 10/10 | $3.04 |
| protestant | 8 | 20 | 18/20 | 4.65 | 9/9 | $3.17 |
| theravada | 8 | 18 | 18/18 | 4.78 | 6/6 | $2.76 |

Lead's reading before the critique round: responses read as judgment rather than vocabulary and
no cue term leaked, but the reviewer almost never scores below 4 and the divergence judge almost
never says no, so neither filter is yet doing much work. The 7B baseline answers are generic
numbered-list advice, so "divergence" partly measures a capability gap rather than a value gap.

(critique findings filled in below)

## 6. Failures discovered by running real pilots

1. Generator sometimes returned `{"family": [...]}` (singular); the reader accepted only the plural
   key and silently dropped half the families in two runs. Fixed with lenient extraction, a retry
   with a shape reminder, and raw payload dumps to `debug/` on any shortfall.
2. Reasoning-only truncation: generator at 4096 tokens returned no answer; reviewer at 8192 lost
   2-6 reviews per target. Budgets now 24000/16000/12000 plus an automatic retry at double budget.
3. Flat dedupe threshold deleted reframing variants and 2 of 3 within-family prompts.
4. Shared rate limit across concurrent processes lost batches; run one API-heavy process at a time.
5. Explicit-mode prompts were never told which tradition to name, so the generator invented one.
6. A 900 s read timeout was also the connect timeout; a dead local server would stall 15 minutes.
7. Contrastive pairs formed inside per-domain batches could never form in small pilots; now planned.

## 7. Unresolved issues

(filled after the critique round)

## 8. Approximate Fireworks cost

Total across all run directories at the end of round 1: about $16.50 over ~480 calls (four pilots
~$12, dev and toy runs ~$4.50). Measured unit costs before budget increases: ~$0.055 per generated
response, ~$0.018 per review. A naive full run (500 rows) with the current models projects to
$50-90, above the brief's $10-20; measured levers: `reasoning_effort: low` on the generator
(about half the cost), a cheaper reviewer (`deepseek-v4-flash-0731`, about 6x cheaper).

## 9. Recommended next step before generating the full Part 1 dataset

(filled after the critique round)
