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

## 4. Experiments and competing approaches

Round 1 (one pass, then six critics):
- **Reviewer/generator from different families** (Qwen generator, DeepSeek reviewer): the reviewer
  still scored 4-5 on nearly everything; separation of families is not enough for calibration.
  Round 2 adds a required verbatim evidence quote (empty caps the score at 3), signature-move
  checks, and a second reviewer (kimi-k3) for agreement measurement.
- **Divergence vs the 7B base only**: confirmed 33/34 but almost all capability gap. Round 2 judges
  three ways (candidate, 7B base, strong generic with no spec) and counts only value-attributed
  divergence with a quoted sentence.
- **Flat similarity thresholds** (0.92 dedupe, 0.85 leakage): never fired. Round 2 measures prompts
  only and calibrates with median + 3 robust deviations (mean + 3 sd let a duplicate raise the cut
  that should catch it), and always prints the closest pairs.
- **Three prompts per family** produced three restatements of one answer; round 2 uses two prompts
  per family with different question kinds.
- **One deliberation shape for all targets** ("name the obligations, weigh them") imposed a duty
  ranking on Theravada and Confucian; round 2 uses a per-target `deliberation_shape` written by
  the researcher.
- **Retry policy**: six attempts (~1 minute) lost batches to a shared per-minute limit; now ten with
  a 90 s cap, and one API-heavy process at a time.
- **Train → evaluate plumbing**: a CPU LoRA on 14 Confucian rows with a 0.5B model, answers judged by
  the same rubric as the 7B base (base passed 1/7, adapter 0/7). This proves the path, not a result;
  a real result needs the GPU recipe in `training/`.

Round 2 experiments:
- **E1 three-way divergence**: see section 5; after the judge fixes the conservative value-attributed rate
  is 1/4, 2/4, 3/4, 4/4 families (Confucian, Catholic, Protestant, Theravāda) on the original judge; the
  re-judged numbers with the fair control and blind labels are in the round-2 run reports.
- **E2 second reviewer (kimi-k3 vs DeepSeek)**: every pair within one point; kimi-k3 runs about 0.3–0.8
  lower on every dimension and still accepts everything. Leniency is not model-specific.
- **E3 house style**: "watch for" paragraph 52/83 → 1/64; shared four-grams from dozens to one. But the
  per-target deliberation shapes were copied as openers in 15–16 of 16 responses per target.
- **E4 generator at `reasoning_effort: low` (Confucian)**: generate-stage cost $0.94 vs $1.78, reasoning
  tokens 55k vs 199k, fidelity 4.81 vs 5.00, same keep rate (15/16), but 8 of 16 responses were sent to
  the revise round versus 0 at full effort. Cheaper first drafts, more repair work; net run cost $2.43 vs
  $4.49 (the low-effort run also had no second reviewer).

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

### What six independent critics found (runs/critique/*.md, full detail there)

- **Divergence was mostly a capability gap.** 33 of 34 intended-divergence verdicts were "diverges",
  but on a critic's re-read only 3 (the Catholic double-effect family) were differences a strong
  generic assistant would not produce. 18 of 34 baseline answers were truncated at 512 tokens. In 5
  cases the user prompt itself stipulated the target's distinctive move.
- **The reviewer never failed anything.** `judgment_not_terminology` was 5 on 80 of 83 responses;
  three boolean flags were constant across all 83 reviews. The only two drops were the restraint
  branch of a deliberately built counterfactual pair, graded against the family's own intent.
- **A house style swamped the target.** Blunt-imperative opener 57/83, a "watch for" paragraph 46/83,
  an obligation-ranking deliberation opener 57/83, identical across all four traditions; the reviewer
  credited that template as Theravāda fidelity and penalised its absence elsewhere. A critic assigned
  7 of 8 shuffled answers to their tradition by recognising doctrinal tests transposed into plain
  English (double effect, the remonstrance ladder), not by judgment.
- **Coverage was an accident of YAML order.** The planner walked tradeoffs by index, so unresolved
  tradeoffs got 0 families for Confucian and Protestant; `confident_on_unresolved` was vacuous. Only
  12 of 45 specified tradeoffs and a handful of divergence hypotheses were exercised.
- **Splits were wrong by construction.** The one counterfactual pair always straddled train/eval and
  was promoted to eval, so eval was 3/8 instead of 2/8 and no training row carried a contrast; retries
  refilled slots by count, regenerating the wrong slot (Theravāda: three near-identical eval families).
- **Dedupe and leakage checks were inert.** Similarity ran over prompt+answer, and long answers washed
  out the scenario: a near-verbatim eval pair scored 0.78 on prompts but 0.41 as checked. Structural
  duplicates (same tradeoff, role, harm) repeated in three of four eval sets.
- **Spec knobs the code supported were never populated.** `soft_terms`, `avoid_keywords`, and the
  allow-lists researchers wrote into free-text notes were invisible, so Theravāda responses never used
  "craving" or "equanimity" and the avoided-topic screen protected nothing.
- **What generalised and what did not.** The code is tradition-agnostic; the assumptions were not: one
  deliberation shape (duty ranking) fitted Catholic and Protestant and misrepresented Theravāda and
  Confucian; the forbidden-term burden ranged from 4 to 16 ordinary concept words per target; layers
  defaulted differently per target.

The round-2 change list derived from these is `docs/round2-changes.md`.

### Round 2 (same sizes; whole-unit splits, planned features, three-way judge, second reviewer)

| target | kept | fidelity (primary / kimi-k3) | divergence confirmed | value-attributed (judge) | critic-defended | cost |
|---|---|---|---|---|---|---|
| confucian | 15/16 | 5.00 / 4.50 | 2/8 (5 unverified) | 1 | 0 of 2 judged | $4.49 |
| catholic | 15/16 | 5.00 / n.a. | 6/8 | 4/4 families | 3 of 4 | $5.87 |
| protestant | 16/16 | 4.94 / 4.81 | 7/8 | 4/4 | 3 of 4 | $5.44 |
| theravada | 14/16 | 4.94 / 4.69 | 8/8 | 4/4 | 4 of 4 | $5.85 |

Numbers are before the re-judge described below; "critic-defended" is the round-2 divergence critic's
re-read of every verdict against all three answers.

What round 2 fixed (per the second critique pass, `runs/critique/round2_*.md`): the shared house style
("watch for" paragraph 52/83 → 1/64; shared four-grams from dozens to one); the round-1 33/34 divergence
illusion (per-family, three-way, value-attributed rates with quoted evidence); unresolved tradeoffs now get
families before any repeat; eval is exactly the configured fraction; calibrated dedupe fires (8–13 pairs per
run against zero); reframing variants are genuinely reframed; grading keys name the concrete choice; the
prompt-stipulation leak is detected and relabelled.

What round 2 did not fix or newly broke:
- **The reviewer still filters nothing**: 127 reviews, zero rejections; the primary gives fidelity 5 on 61
  of 63; the second reviewer is a uniform one-point-lower copy. Evidence quotes are verbatim but not
  selective.
- **Per-target deliberation shapes became per-target templates**: the shape's own wording opens 15–16 of 16
  responses per target, a stronger learnable cue than the shared style it replaced.
- **The strong-generic control was mis-specified** (same model with reasoning off and a fifteenth of the
  budget), the judge was not blind (candidate always Reply A), and five "value" verdicts echo a claim the
  no-spec reply also makes. The critic defends 7 of 16 value-attributed families, not 13.
- **The diversity plan is degenerate at eight families**: the institution walk starts at the same index for
  every target (28 of 32 families clinical), role type never advances (32 of 32 "no authority"), a lone
  counterfactual pair can never reach eval, and the eval and divergence draws coincide (13 of 14 eval rows
  divergence).
- The Confucian run's strong-generic leg ran before the config fix and lost five verdicts.

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
8. **The real root cause of (1), found in round 2:** Fireworks returns HTTP 200 with a body
   `{"error": "The model has exceeded the maximum number of tokens allowed."}` when prompt plus
   `max_tokens` exceeds the window; the client branched on status code only, so the error body
   parsed as an empty list. Every earlier mitigation treated the symptom. Now an error body is an
   error, and that message halves the budget and retries.
9. Round-2 code landed with three defects that unit tests did not catch: a missing import in the new
   reframing-overlap check (NameError on the first variant); a scripted block replacement that left
   two `run_stage` definitions in validate.py, the live one referencing a renamed helper; and the
   planned institution/enums/stance/hypothesis never being written into the family assignment text,
   so "planned diversity" was stamped onto families after generation. Lessons applied: pyflakes in
   the loop, a duplicate-definition scan, and a stage-level test with a stubbed client.

## 7. Unresolved issues

- **Value divergence is rare by construction.** Most tradeoffs a spec lists have a modern
  professional-ethics answer a strong generic assistant already gives. Only tradeoffs with no generic
  analogue (Catholic double effect, Theravada non-deception under pressure, Confucian graded
  partiality) produced value-attributable divergence. Whether 500 rows can carry enough of those is
  the open question for Part 1's purpose.
- **Reviewer calibration.** A generator and a reviewer that share taste produce flat scores; the
  evidence-quote requirement and second reviewer are mitigations, not a solution. Human review of a
  sample is still required before training on any export.
- **Doctrinal tests transposed into plain English** pass every cue check and are still imitation at
  one remove. Nothing automatic distinguishes "states the double-effect test" from "judges the case".
- **Licensing.** Theravada grounding mixes CC BY-NC and CC BY-SA; the export is internal research
  use only until sources are segregated. Vatican and Catechism material is quotation-scale, pending
  rights review. SuttaCentral text was deliberately not used.
- **Interpretive choices left open by design** (each spec's `unresolved_choices`): confessional vs
  neutral mode, naturalised kamma, Protestant grace-and-agency neutrality, Confucian family partiality
  scope, Catholic sexual ethics excluded from the pilot. These need a human decision, not more data.
- **Base-model realism.** A 4-bit 7B on CPU is slow (baseline is the long pole) and its generic,
  list-shaped answers make the divergence bar low. The strong-generic third leg addresses the
  measurement; the training target is still the 7B.
- **Explicit-mode slice** (naming the tradition) was 0 in all pilots and is untested.

## 8. Approximate Fireworks cost

| item | cost |
|---|---|
| round-1 pilots (4 targets, ~8 families each) | ~$12.4 |
| round-2 pilots (4 targets, 8 families, second reviewer + three-way divergence + revise round) | ~$21.7 |
| dev, toy, and E4 low-effort runs | ~$5 |
| **total at end of round 2** | **about $39 over ~900 calls** (see `usage.jsonl` in each run directory) |

Measured unit costs (round 2): ~$0.10 per generated response including its share of family and prompt
calls, ~$0.02 per primary review, ~$0.05 per second review (kimi-k3), ~$0.02 per three-way judge verdict.
Roughly 90% of completion tokens are reasoning. A naive 500-row run with the round-2 configuration projects
to about $110-150; with `reasoning_effort: low` on the generator (E4) and `deepseek-v4-flash` as reviewer it
projects to roughly $40-60. Both exceed the brief's $10-20; the brief's estimate assumed non-reasoning models.

## 9. Recommended next step before generating the full Part 1 dataset

Do not scale yet. Three things must be true first, each checkable on one more 8-family run per target:

1. **A reviewer that rejects.** Replace per-response scoring as the filter with forced ranking inside each
   family (two responses per family, one must lose) plus the "would a strong no-spec assistant write this
   sentence" test on the evidence quote; keep per-response scores only as metadata. Gate: at least 15% of
   responses rejected or ranked-out per target, with a human reading 20 of them agreeing on most.
2. **A fair, blind divergence judge.** Strong-generic leg = generator settings minus the spec; shuffled
   labels; `generic_echo` required; value rate reported per family. Gate: value-attributed divergence of at
   least 35% of intended-divergence families per target under the fixed judge, and a human agreeing on a
   sample.
3. **A plan that varies what it claims to vary.** Institution and role mixes per target, varied axis cycled
   across pairs, pairs reaching eval, eval mix matching intent. Gate: the report's coverage tables show no
   feature with one dominant value, and no two targets sharing more than two institutions.

Also before scaling: decide the deliberation policy (visible deliberation as an ablation slice, and a shape
that describes what to consider without supplying phrasing), resolve the per-spec `unresolved_choices` that
need a human (confessional vs neutral mode, naturalised kamma, Protestant grace-and-agency), and clear the
licensing status of Theravada (NC/SA) and Catholic (Vatican quotation-scale) material for the intended
distribution. Then run `configs/full.yaml` for one target first (about 300 families × 2 prompts, projected
$30–40 with the low-effort generator), read it, and only then the other three.
