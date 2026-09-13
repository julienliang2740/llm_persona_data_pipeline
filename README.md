# Part 1 value-instantiation data pipeline

Generates and validates SFT training data for a **target**: one reviewed belief or value
system, described entirely in `targets/<id>/spec.yaml` plus its source excerpts. No
tradition is named anywhere in the code.

```
targets/<id>/spec.yaml + references/   configs/<run>.yaml
                    │
       generate ─► baseline ─► validate ─► export
       families     base model  reviewer    sft_train.jsonl
       prompts      answers     cue check   eval.jsonl
       responses                dedupe      manifest.json
                                leakage
                                divergence
```

Training on the export and evaluating before/after a fine-tune live in two sibling
repositories that read this one's run directories: `llm_persona_training` (LoRA SFT,
adapter answer generation) and `llm_persona_eval` (judge answers over `eval.jsonl`,
before/after table).

Every stage reads and writes JSONL in `runs/<target>/<run_id>/`, so any artifact can be
inspected on its own and any stage can be re-run alone. Stages are idempotent on a run
directory: re-running fills in what is missing rather than starting over.

## Adding a target

A target is a directory under `targets/`, not code. Copy `targets/_template/`, fill in `spec.yaml`
and `references/key_passages.md`, record provenance in `SOURCES.md`, then run

```bash
.venv/bin/python main.py check --target <your_id>
```

until it reports no problems, and run a two-family pilot. The full walkthrough, with what each spec
section does and the conventions that matter, is `targets/README.md`; the field reference is
`docs/target-spec-schema.md`; the four existing targets are complete worked examples.

The pipeline does not acquire sources. Collecting, verifying and licence-checking reference texts is
research work done before the pipeline runs (for the four pilots it was done by research teammates
with web access, recorded in each target's `SOURCES.md` and `research_notes.md`).

## Run a pilot

```bash
.venv/bin/pip install -r requirements.txt          # httpx, pyyaml, pytest, pytest-asyncio
echo "<your key>" > fireworks_api_key.txt          # gitignored; never logged or committed

# End to end on the built-in toy target, which needs no real tradition spec:
.venv/bin/python main.py all --target toy --config configs/pilot.yaml \
    --targets-dir tests/fixtures/targets --n-families 4 --new-run

# One stage at a time on a real target:
.venv/bin/python main.py generate --target confucian --config configs/pilot.yaml --new-run
.venv/bin/python main.py baseline --target confucian    # needs the local base server, see below
.venv/bin/python main.py validate --target confucian
.venv/bin/python main.py export   --target confucian
.venv/bin/python main.py report   --target confucian
```

Without `--run`, a stage continues the most recent run for that target. `--new-run` starts a
fresh one. `--n-families` overrides `generation.n_families` for a quick pilot.

The full Part 1 size (about 500 training rows and 50 evaluation prompts) is
`configs/full.yaml`: 240 families, 3 prompts per training family, one critique-and-rewrite
pass. Read the cost note in that file before launching it.

## What the generated data contains

Beyond one prompt and one response per case, three structures matter:

- **Contrastive groups.** A configurable share of families (`counterfactual_fraction`) are
  written in pairs: the same situation with exactly one morally relevant fact changed, recorded
  in `varied_fact`. Members of a group are never treated as duplicates of each other and never
  split apart, so the contrast survives into the dataset.
- **Situation features.** Each family records `relationship`, `role_type`, `harm_severity`,
  `urgency`, `public_or_private` and `asker_state` in the generator's own words. The run report
  shows the spread, which is how you catch a run where everything came out minor and private.
- **The explicit slice.** `explicit_fraction` (0 by default) produces records where the prompt
  may name the tradition and the cue check is deliberately skipped. Everything else is uncued.

## Layers

A spec may define `layers` and tag principles with one. A layer is generated unless it sets
`generate_by_default: false`, and `generation.target_layers` in the config overrides that
entirely. Principles with no layer are always included, and a spec with no layers renders all
of its principles.

## Before and after a fine-tune

`baseline` here talks to a local OpenAI-compatible server for the un-tuned checkpoint. The
rest of the loop moved out on 8 September 2026:

- `../llm_persona_training`: `train_lora.py` on `sft_train.jsonl`, `generate_with_adapter.py`
  over `eval.jsonl`, whose rows are `{prompt_id, prompt, model, text}`.
- `../llm_persona_eval`: `main.py evaluate` runs a configured model role or an answers file over
  `eval.jsonl` and judges it; `main.py compare` writes the before/after table. Results land in
  this repo's run directory as `eval_results_<label>.jsonl` and `before_after.md`.

The `evaluation:` section of each config (temperature, answer token budget) is read by the eval
repo, which imports this repo's `pipeline` package rather than copying it.

If the local server is not running, `baseline` stops with a one-line explanation rather than a
traceback, and `main.py all` continues without it. Intended-divergence cases are then recorded
as `unverified` instead of confirmed, and the report says so.

## Where things are

| Path | What it holds |
|---|---|
| `main.py` | the CLI; one function per stage |
| `pipeline/config.py` | run config, API-key loading, run-directory resolution |
| `pipeline/model.py` | **the only place HTTP model calls happen**: retries, concurrency, usage ledger, JSON parsing |
| `pipeline/target.py` | spec loading, validation, and the text handed to prompts |
| `pipeline/records.py` | every record type, and JSONL read/write |
| `pipeline/plan.py` | the coverage plan: slots, splits, pairs, stance mix, held-out tradeoffs (no model calls) |
| `pipeline/institutions.py` | the institution list sampled per slot |
| `pipeline/generate.py` | families, user prompts, responses |
| `pipeline/baseline.py` | base-model answers, and the strong-generic third leg of the divergence comparison |
| `pipeline/validate.py` | the validation stage: orders the checks below, turns their output into one Decision per response, writes the artifacts |
| `pipeline/similarity.py` | cue-term check, near-duplicates, leakage, and the per-run calibrated threshold |
| `pipeline/review.py` | reviewer critique, the score-key repair, and the revise round |
| `pipeline/divergence.py` | three-way judging against the base model and a strong generic answer |
| `pipeline/export.py` | family split, `sft_train.jsonl`, `eval.jsonl`, `manifest.json` |
| `pipeline/report.py`, `report_style.py` | the markdown run report; cross-target style, coverage and similarity tables |
| `prompts/` | **all model-facing text**, as ALL_CAPS constants with `{{placeholders}}` |
| `configs/` | `pilot.yaml`, `full.yaml`, `pricing.yaml` |
| `tests/fixtures/targets/toy/` | an invented target so tests never need a real one |

## Run outputs

Inside `runs/<target>/<run_id>/`:

| File | Contents |
|---|---|
| `families.jsonl` | scenario families: the unit of splitting and of leakage checks |
| `prompts.jsonl` | uncued user messages, `base` plus reframing variants for eval families |
| `responses.jsonl` | deliberation, answer, and hidden principle/passage metadata |
| `baseline.jsonl` | the base model's answers to the same prompts |
| `reviews.jsonl` | reviewer scores, issues and verdicts |
| `divergence.jsonl` | judge verdicts, candidate and baseline shown in randomised order |
| `decisions.jsonl` | keep/drop per response with every reason |
| `sft_train.jsonl` | `{"messages": [user, assistant], "meta": {...}}` |
| `eval.jsonl` | prompt, case type, expected behaviour, pass/fail notes |
| `manifest.json` | counts, models, spec version, config hash, cost |
| `similarity_pairs.jsonl` | the closest prompt pairs with the calibrated cut that was applied |
| `reviews_second.jsonl` | optional second reviewer's scores (config `validation.second_reviewer_role`) |
| `config.resolved.yaml`, `spec.yaml` | copies of the exact config and target spec this run used |
| `usage.jsonl` | one line per model call: tokens, cost, stage, record id |
| `report.md` | the five-minute read |
| `log.txt` | the same log that went to stdout |

## Licence terms travel with the data

`manifest.json` carries `license_constraints`: every distinct `license` value from the spec's
`grounding` reference material, plus an optional `redistribution_note` from the config. One
target's grounding sources are CC BY-NC, so a dataset built from it is not freely commercial.
Read that field before redistributing an export.

## Cost

`configs/pricing.yaml` holds USD per million tokens per model. Any model missing from it, or
carrying a `null` price, produces `cost_usd: null` in the usage ledger, and the manifest and
report then say the cost is **unknown**. A price is never guessed. Fill the file in from the
provider's published list and record the source next to each number.

Token counts are always exact. The generator is a reasoning model and spends most of its
output budget on reasoning: 4,000 to 11,000 reasoning tokens per response, which is about 90%
of its output. Measured on this repo's defaults, one generated response costs $0.055 and one
review costs $0.018, so a 600-response run lands near $49 with `revise_rounds: 0` and near $89
with `revise_rounds: 1`. Setting `extra_body: {reasoning_effort: low}` on the generator role
cuts reasoning roughly fourfold and the per-response cost roughly in half, with no obvious loss
of quality on the cases inspected. Reasoning tokens count against `max_tokens`, so a role whose
budget is too small returns reasoning and no answer; the client raises a clear error naming the
role and the limit when that happens.

## How near-duplicates and leakage are judged

Similarity is measured on the user prompt and the family's seed situation, never on the
answers: generated answers share register and structure, which washes the scenario signal
out. One round-1 pair scored 0.784 on prompts alone and 0.412 once its answers were included.

The cut is calibrated per run at the median plus three robust deviations of that run's own
pair distribution, using the median absolute deviation scaled by 1.4826 rather than a mean and
a standard deviation. The reason is that the duplicates are precisely the values in the tail,
so they poison a mean-based cut: on a clean distribution holding one near-duplicate at 0.784,
mean plus three standard deviations lands at 1.14 and the duplicate hides behind the threshold
it raised itself, while the robust cut lands at 0.16 and flags it. The robust cut still cannot
resolve a set where duplicates are not a minority, which is why the closest pairs are always
written to `similarity_pairs.jsonl` and printed in the report whether or not any crossed the
threshold.

## Known limits

- Divergence judging is position-blind, not provenance-blind. The three replies are shuffled
  per call so the judge cannot learn that one slot always holds the candidate, which is what
  produced 23 of 26 verdicts favouring it. The judge is still told which label holds the reply
  under test and which holds the no-specification reply, because the `generic_echo` check
  cannot be asked for otherwise. A fully provenance-blind variant would need a second judging
  pass that never mentions roles; it is deferred because it doubles judge cost, and the
  forced-capability rule already catches the case it would find.

- The reviewer sees the whole target on every call, about 11,000 input tokens on a real spec,
  which is now the largest single input cost in a run. It is deliberate: a critic that cannot
  see a principle cannot notice that it was missed.
- A reasoning model sometimes spends its whole `max_tokens` thinking and returns no answer. The
  client retries once at double the budget, capped at 32,000, and only then raises an error
  naming the role. If you see that error, raise the role's `max_tokens` or set
  `extra_body: {reasoning_effort: low}`.
- Contrastive pairs need at least two families in one domain, so a very small pilot produces
  none. That is by design, not a failure.
- `pipeline/generate.py` is around 780 lines because coverage planning and the three generation
  stages live together. Splitting the planning out into its own module would fix it.

## Tests

```bash
.venv/bin/pytest -q                            # unit tests, no network
.venv/bin/pytest -m smoke -q                   # one real call per role; skipped without the key file
```

`tests/test_validate_stage.py` runs the whole validation stage against a stubbed client, so
the stage itself is exercised without the network. It also carries two structural guards over
every pipeline module, both of which exist because of a real defect that shipped: no module may
define the same top-level name twice, and no module may call a private helper it never defines
or imports. A scripted edit had left two copies of `run_stage` in `validate.py`, and the
surviving copy called a helper that had been renamed away, so the stage would have raised
`NameError` on its first real run while every unit test passed.

Unit tests cover key loading (including that no exception path can contain the key), record
IO, spec validation errors, the cue-term check, duplicate and leakage detection, lenient JSON
parsing, coverage planning, export rendering and the report. They use
`tests/fixtures/targets/toy`, an invented target, so they never depend on a real spec.

### Divergence judging: what is and is not blind

The three-way judge shuffles the candidate, the local base answer and the strong no-spec answer into
random positions per prompt, so the positional cue is gone. It is still told which label is the reply
under test and which is the no-spec reply, because it must quote the closest no-spec sentence
(`generic_echo`). A provenance-blind second pass that never names roles is a deferred option; it doubles
judge cost. A family counts as value-attributed only when every judged prompt in it is; the any-prompt
rate is reported as a secondary line.

### Sources and References:
https://arxiv.org/abs/2408.11779 
https://arxiv.org/abs/2410.16491
