# Target specification schema

A **target** is one belief/value system the pipeline can be configured with.
Everything tradition-specific lives under `targets/<target_id>/`; the pipeline
code never mentions a tradition by name.

```
targets/<target_id>/
  spec.yaml            # the reviewed target specification (schema below)
  references/          # acquired source texts used for grounding
  SOURCES.md           # provenance ledger for everything in references/
  research_notes.md    # what was verified/corrected relative to the research report
```

## spec.yaml

```yaml
id: confucian                      # short slug, used in run/artifact names
name: Early Confucian (Analects and Mengzi)
version: 0.1                       # bump when the spec changes; recorded in every artifact

# 1-2 paragraphs the generator reads first. Describe the *style of judgment*
# (what the tradition notices, weighs, and does), not a slogan list.
summary: >
  ...

# Layers are optional. Use them when the tradition itself has a core plus
# branches (e.g. Confucian core + Mencian development; shared Protestant
# core + denominational branches). Generation targets `core` by default.
layers:
  - id: core
    description: ...
    generate_by_default: true    # optional, default true; config generation.target_layers overrides
  - id: mencian
    description: ...
    generate_by_default: false   # a branch the pilot does not generate from

principles:                        # 8-20 items; each must be checkable
  - id: CM01
    name: Humane concern
    layer: core                    # optional
    description: >
      One paragraph: what the principle demands and how it shows up in conduct.
    positive_indicators:           # observable in a response
      - notices concrete human need
    failure_modes:                 # what a superficially similar but wrong response looks like
      - reduces humaneness to being pleasant; avoids necessary criticism
    sources:                       # passage ids that ground this principle
      - Analects 12.22
      - Mengzi 2A6

boundaries:                        # limits / counterexamples the tradition itself imposes
  - principle: CM03                # or free text
    limit: Filiality does not require participation in serious wrongdoing.
    sources: [Analects 4.18, Analects 13.18]

tradeoffs:                         # genuine conflicts that scenarios must cover
  - id: family_vs_public_justice
    description: How much protection does kinship justify when third parties are harmed?
    considerations: [relational responsibility, harm severity, public role]
    intended_lean: >               # how the reviewed target resolves it, if it does
      Distinguish minor wrongdoing from serious harm; do not obstruct accountability for serious harm.
    unresolved: false              # true = the pilot must NOT generate a confident resolution
    sources: [Analects 13.18, Mengzi 7A35]

unresolved_choices:                # interpretation choices that remain open for human review
  - id: analects_13_18
    question: How should the father-son concealment case be instantiated?
    working_assumption: >         # what the pilot assumes, flagged as provisional
      Treat as differentiated care with a serious-harm limit; never a blanket rule.
    generation_policy: avoid | mark_ambiguous | use_working_assumption
    avoid_keywords: [concealment, cover up]   # optional, only for generation_policy: avoid.
                                              # Word-boundary screen over seed_situation; a hit
                                              # marks the family `split: reserved` with a reason
                                              # rather than deleting it. Keep them specific:
                                              # a common word like "will" reserves everything.

misinterpretations:                # common distortions; used by the reviewer as red flags
  - claim: Confucius teaches blind obedience.
    correction: Respect coexists with remonstrance and judgment.

divergence_hypotheses:             # where we expect a generic assistant to answer differently
  - id: remonstrance_over_compliance
    description: >
      A generic assistant tends to ...; the target instead ...
    example_prompt_shape: ...

domains:                           # coverage requirements for scenario generation
  - id: work
    weight: 0.3
    notes: management, colleagues, incentives, whistleblowing
  - id: family
    weight: 0.3
  ...

cue_policy:
  prompts_must_not_name_tradition: true
  responses_avoid_doctrinal_vocabulary: true   # ordinary language by default
  forbidden_terms: [Confucius, Confucian, ren, li, yi, junzi, Analects, Mencius]   # hard: any hit rejects
  soft_terms: [grace, doctrine]                # optional; flagged in the report, never a reason to reject
  allowed_in_explicit_mode: true               # a separate small "explicit" slice may name sources

reference_material:                # what the generator/reviewer may quote or lean on
  - id: analects_legge
    path: references/analects_legge.txt
    title: The Analects (Confucian Analects)
    author: Confucius (received text)
    translator: James Legge
    edition: The Chinese Classics vol. 1, 1861/1893
    url: https://www.gutenberg.org/...
    license: public domain
    use: grounding                  # grounding | reference_only (do not quote at length)
    passage_id_format: "Analects <book>.<chapter>"
  - id: key_passages
    path: references/key_passages.md
    use: grounding
    notes: curated excerpts with passage ids; this is what is actually placed in prompts
```

## Rules

- Every principle, boundary, and tradeoff cites at least one passage id that exists in `references/`.
- `key_passages.md` has exactly one markdown heading (`##`, `###` or `####`) per passage; the heading text
  before an optional ` — title` is the passage id and must match the `sources:` entries exactly. Any other
  section headings must be level-1 (`#`) or bold text. The loader rejects a spec whose cited ids do not resolve.
- A tradeoff must carry either `intended_lean` or `unresolved: true`; the validator rejects one with neither.
- Optional keys the loader tolerates and ignores: anything not listed here, including
  `cue_policy.notes`, `cue_policy.forbidden_terms_notes`, `cue_policy.explicit_mode_notes`, and
  `reference_material[].author`. Only the required keys are enforced.
- `license` on every `use: grounding` reference entry is copied into the export manifest as
  `license_constraints`, so a non-commercial restriction travels with the dataset. Record it
  even when the answer is "public domain".
- Passage-id prefixes (e.g. "Analects") may also be forbidden cue terms; the cue check applies only to
  user-visible prompt/response text, never to internal record fields.
- `unresolved: true` tradeoffs and `unresolved_choices` are preserved, not silently resolved. The generator may produce scenarios for them but the response must present the conflict honestly; the reviewer flags confident resolutions.
- Modern normative constraints (anti-discrimination, safeguarding, consent) that the tradition did not formulate are labeled as such in `summary` or `boundaries`, never attributed to the sources.
- `SOURCES.md` records for each file: work, edition/translation, URL, access date, license or access terms, any AI-use restriction, and what was done to it (e.g. "chapters 1-20 extracted, headers removed").
- Do not include text that the source's terms forbid for this use. If a source is reference-only (e.g. SuttaCentral's AI-use request, copyrighted modern translations), record it in `SOURCES.md` with `use: reference_only` and do not copy it into `references/`.

## Round-2 additions (all optional except where the loader says otherwise)

```yaml
deliberation_shape: >          # 3-5 lines: how this target deliberates; used verbatim in the response prompt
  ...
signature_moves:               # 3-6 named, checkable moves the reviewer scores present/absent
  - id: names_the_act_first
    description: ...
cue_policy:
  allowed_terms: [...]         # ordinary-English concept words the target needs; rendered positively
  soft_terms: [...]            # phrase-shaped tells; flagged and counted, never a rejection reason
  archaic_register_examples: [...]   # diction from the source translations the generator must not imitate
unresolved_choices:
  - id: ...
    generation_policy: avoid
    avoid_keywords: [...]      # REQUIRED when generation_policy is avoid; keyword screen on seed situations
tradeoffs:
  - id: ...
    unresolved: true
    resolved_part: >           # what the tradition does settle here
    open_question: >           # the part that stays open; confident_on_unresolved covers only this
redistribution_note: >         # REQUIRED when any grounding source is not public domain
```
Every `reference_material` entry with `use: grounding` must have a non-null `license`.
