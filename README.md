# Part 1 value-instantiation data pipeline

Generates and validates SFT training data for a **target**: one reviewed belief or value
system, described entirely in `targets/<id>/spec.yaml` plus its source excerpts. No
tradition is named anywhere in the code.

```
targets/<id>/spec.yaml + references/   configs/<run>.yaml
                    │
       generate ─► baseline ─► validate ─► export ─► evaluate
       families     base model  reviewer    sft_train.jsonl   before/after
       prompts      answers     cue check   eval.jsonl        on the held-out set
       responses                dedupe      manifest.json
                                leakage
                                divergence
```

Every stage reads and writes JSONL in `runs/<target>/<run_id>/`, so any artifact can be
inspected on its own and any stage can be re-run alone. Stages are idempotent on a run
directory: re-running fills in what is missing rather than starting over.

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

## Before and after a fine-tune

`baseline` and `evaluate` talk to a local OpenAI-compatible server, so the same code runs the
un-tuned checkpoint and the adapted one:

```bash
llama-server -m <model>.gguf --port 8080          # in another terminal
.venv/bin/python main.py evaluate --target confucian --endpoint base --label before
# ... fine-tune, restart llama-server on the adapter ...
.venv/bin/python main.py evaluate --target confucian --endpoint base --label after
.venv/bin/python main.py evaluate --target confucian \
    --before runs/confucian/<run>/eval_results_before.jsonl \
    --after  runs/confucian/<run>/eval_results_after.jsonl
```

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
| `pipeline/generate.py` | coverage plan, families, user prompts, responses |
| `pipeline/baseline.py` | base-model answers for the comparisons |
| `pipeline/validate.py` | reviewer critique, cue check, near-duplicates, leakage, divergence, decisions |
| `pipeline/export.py` | family split, `sft_train.jsonl`, `eval.jsonl`, `manifest.json` |
| `pipeline/evaluate.py` | run an endpoint over the eval set, judge it, before/after table |
| `pipeline/report.py` | the markdown run report |
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
| `usage.jsonl` | one line per model call: tokens, cost, stage, record id |
| `report.md` | the five-minute read |
| `log.txt` | the same log that went to stdout |

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

## Tests

```bash
.venv/bin/pytest -q                            # unit tests, no network
.venv/bin/pytest -m smoke -q                   # one real call per role; skipped without the key file
```

Unit tests cover key loading (including that no exception path can contain the key), record
IO, spec validation errors, the cue-term check, duplicate and leakage detection, lenient JSON
parsing, coverage planning, export rendering and the report. They use
`tests/fixtures/targets/toy`, an invented target, so they never depend on a real spec.
