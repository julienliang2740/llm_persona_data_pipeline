# Targets: how to add a belief or value system

A **target** is everything the pipeline knows about one tradition. It is data, not code.

## Required input, in one page

### 1. Where it goes

```
targets/<target_id>/                 <target_id> = short lowercase slug, e.g. confucian
  spec.yaml                          REQUIRED   the target specification
  references/key_passages.md         REQUIRED   the source passages that spec.yaml cites
  SOURCES.md                         REQUIRED   provenance and licence of every reference
  references/<full texts>            optional   complete source texts you acquired
  research_notes.md                  optional   what you verified and left open
```

Nothing else is read. The directory name must equal `id:` inside `spec.yaml`. Run names, output
files and manifests all use `<target_id>`.

### 2. Format of each required file

**`spec.yaml`** is one YAML mapping. Keys the loader refuses to run without:

| key | type | rule |
|---|---|---|
| `id` | string | equals the directory name |
| `name`, `version` | string | `version` is recorded in every run manifest |
| `summary` | paragraph | how the tradition judges, in prose |
| `principles` | list | at least 3 (8-16 intended); each has `id`, `name`, `description`, `sources` (list of passage ids) |
| `domains` | list | each has `id`; add `weight` (weights sum to 1) |
| `cue_policy` | mapping | must contain `forbidden_terms` (list); `allowed_terms` and `soft_terms` must not overlap it |

Keys the pipeline needs to produce tradition-specific data (strict check warns or fails without them):

| key | what it holds |
|---|---|
| `tradeoffs` | genuine conflicts; each has `intended_lean`, or `unresolved: true` with `resolved_part` and `open_question` |
| `boundaries` | the tradition's own limits on its principles, each citing passages |
| `unresolved_choices` | interpretive decisions left to a human: `working_assumption` + `generation_policy` (`use_working_assumption` / `mark_ambiguous` / `avoid`; `avoid` requires `avoid_keywords`) |
| `divergence_hypotheses` | where a generic assistant would answer differently (`id`, `description`, `example_prompt_shape`) |
| `misinterpretations` | common distortions (`claim`, `correction`) |
| `deliberation_shape` | 3-5 lines on what this target considers and in what order (no phrasing) |
| `signature_moves` | 3-6 checkable moves the reviewer scores present/absent |
| `cue_policy.allowed_terms`, `soft_terms`, `archaic_register_examples` | words the target may use; phrase tells to count; source diction not to imitate |
| `layers` | optional core/branch structure with `generate_by_default` |
| `reference_material` | one entry per reference file; the entry whose `path` ends in `key_passages.md` is what reaches prompts; every `use: grounding` entry needs `license` |
| `redistribution_note` | required when any grounding licence is not public domain |

The annotated example of every key is `_template/spec.yaml`; the field-by-field reference is
`docs/target-spec-schema.md`.

**`references/key_passages.md`** is markdown with **one heading per passage**. The heading text
before an optional ` — title` is the passage id, and it must match the spec's `sources:` entries
character for character:

```markdown
### Analects 13.18 — Uprightness and concealment
The Duke of She told Confucius ... (excerpt or close paraphrase, 2-8 sentences)
Grounds: CM03, tradeoff family_vs_public_justice.
```

Only `##`, `###` and `####` headings are passage ids; use `#` or bold text for section labels. Keep
the file under about 8,000 words, because it is placed into prompts. Only include text whose licence
permits copying; otherwise paraphrase and cite.

**`SOURCES.md`** is a table with one row per file under `references/` and one per source consulted
but not copied: work, edition/translator, URL, access date, licence or terms, any AI-use restriction,
processing applied, and `use` (`grounding` or `reference_only`).

### 3. Content that has to be there for the data to be any good

- The `summary` describes a **style of judgment** (what is noticed first, what overrides what, what
  is refused), not a list of virtues. A vague summary produces generic advice.
- Each principle has `positive_indicators` (observable in a response) and `failure_modes` (what a
  superficially similar wrong answer looks like); the reviewer grades against these.
- Tradeoffs include the tradition's **hard cases**, and the ones the sources leave open are marked
  `unresolved: true`. The planner gives every unresolved tradeoff a scenario before repeating any.
- `divergence_hypotheses` name the places the tradition's answer differs from a strong generic
  assistant's; without them the intended-divergence cases collapse into generic professional ethics.
- Modern constraints (anti-discrimination, safeguarding, consent) are labelled as modern, never
  attributed to the sources.
- Every passage cited actually says what the spec claims. Verify against the source, not a summary.

The four existing targets are complete worked examples; `_template/` is a minimal one that validates
and is meant to be copied.

## The five steps

1. **Copy the template.**
   ```bash
   cp -r targets/_template targets/mytarget
   sed -i 's/^id: _template/id: mytarget/' targets/mytarget/spec.yaml
   ```
2. **Collect source passages** into `references/key_passages.md`. One markdown heading per passage;
   the heading text before an optional ` — title` is the **passage id** the spec will cite:
   ```markdown
   ### Analects 13.18 — Uprightness and concealment
   <excerpt or close paraphrase, 2-8 sentences>
   Grounds: which principle or tradeoff this passage supports.
   ```
   Use `#` (level 1) or bold text for section headings so they are not parsed as passage ids.
   Keep the whole file under roughly 8,000 words: it is placed in prompts. Record every source's
   provenance and licence in `SOURCES.md`; anything you may not copy stays `reference_only` there.
3. **Write `spec.yaml`.** Every field is annotated in `_template/spec.yaml`; the full reference is
   `docs/target-spec-schema.md`. The minimum the loader accepts: `id`, `name`, `version`, `summary`,
   at least 3 `principles` (8-16 is the intended range) each citing a passage id that exists in
   `key_passages.md`, `domains`, and a `cue_policy` with `forbidden_terms`. Everything else
   (tradeoffs, boundaries, unresolved choices, divergence hypotheses, deliberation shape, signature
   moves, allowed and soft terms, layers, licences) is what makes the target *this* tradition rather
   than generic good advice; the pilots showed that a spec without them produces generic advice.
4. **Check it.**
   ```bash
   .venv/bin/python main.py check --target mytarget
   ```
   This loads the spec in strict mode and prints every problem at once (missing keys, passage ids that
   do not resolve, cue-list overlaps, `avoid` choices without keywords, grounding sources without a
   licence) plus a summary of what the pipeline will use. Fix until it reports no problems.
5. **Run a tiny pilot and read it.**
   ```bash
   .venv/bin/python main.py all --target mytarget --config configs/pilot.yaml --n-families 2 --new-run --skip-baseline
   ```
   Then open `runs/mytarget/<run_id>/report.md` and `responses.jsonl`. If the responses could have
   been written without the spec, the spec is not yet doing its job (see `docs/DEVELOPMENT_SUMMARY.md`
   §5 for what that looks like).

## What each part of the spec is for

| section | who uses it | what happens if it is weak |
|---|---|---|
| `summary` | generator, reviewer | the judgment style; too vague and every answer is generic |
| `principles[]` with `positive_indicators`, `failure_modes`, `sources` | generator, reviewer | reviewer cannot tell a real application from vocabulary |
| `boundaries[]` | generator, reviewer | the tradition's own limits get overstated |
| `tradeoffs[]` (`intended_lean` or `unresolved: true` + `resolved_part`/`open_question`) | planner, generator, reviewer | scenarios avoid the hard cases; `confident_on_unresolved` never fires |
| `unresolved_choices[]` (`generation_policy`: use_working_assumption / mark_ambiguous / avoid + `avoid_keywords`) | planner, reviewer | topics you meant to exclude get generated |
| `divergence_hypotheses[]` | planner, generator, judge | the plan cannot target where the tradition differs from a generic assistant |
| `domains[]` with weights | planner | coverage skews to one setting |
| `cue_policy` (`forbidden_terms`, `allowed_terms`, `soft_terms`, `archaic_register_examples`) | generator, cue check, reviewer | either the tradition leaks by name or the target cannot use its own ordinary words |
| `deliberation_shape`, `signature_moves` | generator, reviewer | responses follow a shared house style instead of the tradition's own moves |
| `layers[]` with `generate_by_default` | planner, renderer | branch material mixes into the core |
| `reference_material[]` with `license`, `redistribution_note` | export | export refuses to write a dataset with unstated licence terms |

## Conventions that matter

- **Passage ids are exact strings.** `sources: [Analects 13.18]` must match a heading `### Analects 13.18`
  character for character. The checker lists every mismatch.
- **Cue lists**: `allowed_terms` and `soft_terms` may overlap each other; neither may overlap
  `forbidden_terms`. Matching is case-insensitive on word boundaries and supports multi-word phrases.
- **Modern constraints** (anti-discrimination, safeguarding, consent) are labelled as modern in
  `summary` or `boundaries`, never attributed to the sources.
- **Unresolved means unresolved.** A tradeoff marked `unresolved: true` will be presented as a
  genuine conflict; a response that resolves it confidently is flagged.
- **Licensing travels with the data.** Every `use: grounding` entry needs a `license`; if any is not
  public domain, a top-level `redistribution_note` is required. `SuttaCentral`-style requests not to
  use content for AI datasets are honoured by listing the source `reference_only`.
- **Do not put text in `key_passages.md` that its source forbids you to copy.** Paraphrase and cite.

## Files you will not need to touch

Nothing under `pipeline/`, `prompts/`, or `configs/` is tradition-specific. If a target seems to need
a code change, that is a schema gap: add the field to the spec, document it in
`docs/target-spec-schema.md`, and read it in `pipeline/target.py`.
