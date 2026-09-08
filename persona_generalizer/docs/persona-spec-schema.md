# Persona specification schema

A **persona target** is everything the pipeline knows about one person, real or fictional. Like a
value-system target it is data, not code, and it lives entirely under
`persona_generalizer/personas/<persona_id>/`.

This schema is a **superset** of `docs/target-spec-schema.md`. Every key that schema requires is
required here and means the same thing. The persona-only sections below are additions; the loader
tolerates unknown keys, so a persona spec validates and runs through the existing pipeline today,
with the persona-only fields inert until `pipeline/target.py` is taught to render them.

```
persona_generalizer/personas/<persona_id>/
  spec.yaml                    REQUIRED   the specification
  references/key_passages.md   REQUIRED   every citable item: words, deeds and testimony
  SOURCES.md                   REQUIRED   provenance ledger
  research_notes.md            optional   what was verified, corrected and left open
  references/<full texts>      optional   complete sources acquired
```

Validate with:

```bash
python persona_generalizer/check_persona.py <persona_id>       # persona rules + target schema
python persona_generalizer/check_persona.py --all
```

`main.py check --target <persona_id> --targets-dir persona_generalizer/personas` runs only the
target-schema half. It is what the pipeline enforces at run time, and it will happily load a spec
whose sufficiency verdict is `refuse`, so it is not a substitute for the persona checker.

---

## The two rules that make this schema different

Everything unusual below follows from two decisions, and neither is negotiable within this
branch.

### 1. Conduct outranks statements

When what a person **said** conflicts with what they **did**, first try to explain the gap: their
life may have been in danger, they may have been coerced, their views may have moved over a
lifetime. A defensible reconciliation is the better outcome and belongs in `research_notes.md`
as well as the spec. Where no reconciliation holds, **conduct governs** — people say a great many
things they never act on.

The said/did distinction is therefore something you **call out in prose wherever it is visible**,
in `key_passages.md` entries and in the `SOURCES.md` ledger. It is deliberately *not* a mandatory
label on every datapoint. A holistic persona needs social background, period, and the events that
happened to them, and none of that fits a said/did taxonomy.

### 2. The persona does not operate inside modern constraints

The value-system targets in `targets/` all carry a clause placing the tradition inside modern
commitments — anti-discrimination, safeguarding, consent — and forbidding those from being
attributed to the sources. **Persona specs must not carry that clause.** The purpose is a dataset
that trains a model to behave as closely to the subject as possible, and a modern-norms override
defeats it.

Conflicts with contemporary norms are handled as **provenance, not filtering**: stated in
`redistribution_note` and declared in the export manifest, exactly as source licence constraints
already travel with an exported dataset. Fidelity governs the content; the constraint is recorded.

The corollary is that `summary` must carry the subject's unattractive parts as plainly as its
attractive ones, and `conflicts:` must not idealise a documented pattern away. A persona
corrected into a better person is a different person.

---

## Sufficiency: which subjects are admissible

Run this **before** writing anything else. It answers the question of why some subjects can be
generalised and others cannot.

| criterion | what it asks | rough floor |
|---|---|---|
| **first-person volume** | How much survives in their own words? | ~10,000 words; below ~3,000 the persona is mostly invention |
| **decisions with reasoning** | How many documented decisions survive where both the act *and* their stated reason are known? | 6–8. **This is the binding criterion.** Most subjects fail here |
| **domain breadth** | Does the material span more than one area of life? | 2+ domains with real coverage |
| **contestedness** | How much of the record is legend, hagiography or hostile invention? | the attributable core must be larger than the disputed part |
| **testimonial variety** | Do independent observers with different interests survive? | 2+ sources of differing interestedness |

`check_persona.py` enforces the structure — that every criterion is answered, that a `refuse`
verdict blocks the build, and that `admit_with_caveats` records what is thin. It cannot make the
judgement itself: whether 8,000 surviving words is enough for *this* subject is research, not
computation, and belongs to whoever runs the gate.

Verdicts:

- **`admit`** — all criteria met.
- **`admit_with_caveats`** — one criterion thin. Record the caveat in `sufficiency.caveats` and
  reflect it in `domains` weights, so the plan does not over-generate where nothing grounds it.
- **`admit_reconstructed`** — buildable, but part of the corpus is inference rather than
  attestation. Requires an `evidence_basis:` line on **every** passage, holds the reconstructed
  share under 40%, and travels into the export manifest. See "Evidence basis" below.
- **`refuse_acquisition`** — the material was not retrieved. **This is a fact about the search,
  not about the subject, and it is retryable.** Record what was tried in
  `sufficiency.acquisition_attempts` and escalate; do not build the spec out on what was reached.
- **`refuse_evidence`** — the material does not survive. Say so and stop. A spec written past a
  refusal produces a persona of the researcher's imagination wearing a real name, which is worse
  than no persona.
- **`refuse_scope`** — out of scope whatever the evidence shows. See "Scope" below.
- **`refuse`** — deprecated alias for `refuse_evidence`. Still blocks, but warns, because it does
  not say which refusal it is.

The split between the two refusals is the important one. A single acquisition pass cannot tell
"this subject left nothing" from "this pass did not reach what the subject left", and only the
second is a bug. Collapsing them into one word meant a thin search looked exactly like a thin
subject, and the research that produced the verdict was thrown away rather than escalated.

Two illustrative refusals: an unremarkable person from the fifteenth century fails on volume and
on decisions-with-reasoning, because nothing survives; an object rather than a person fails
before the gate, because it has no conduct to be faithful to.

### Scope

A second axis, and the evidentiary criteria cannot reach it: they ask whether enough material
survives, not whether a faithful persona of this subject should exist. The subjects excluded here
are among the best-documented people who ever lived and pass every criterion comfortably.

The rule was always here — **living private individuals** are refused regardless of volume — it
just had no verdict name and no enforcement. `persona_generalizer/scope.py` generalises it and
carries the argument in full. In short: a persona spec is fidelity-maximising. It carries no
modern-constraint clause by design, `divergence_hypotheses` deliberately enumerates where the
subject departs from ordinary assistant ethics, and the export is fine-tuning data. For almost
every subject that is the point — LBJ's unattractive half is electoral fraud and twenty years of
segregationist votes, and softening it would produce a different and less useful person. The
exclusion is narrower than "did terrible things": it is for subjects whose **distinctive value
content** is the direction or advocacy of mass atrocity, where the faithful rendering and the
harmful artefact are the same object.

Two mechanisms, and neither is a filter:

- **`sufficiency.scope_check`** is required on every admitted spec. It records that the question
  was asked and what was concluded. Requiring the field is the point: no list can make the
  judgement, so a person makes it once, in writing.
- **A tripwire** on the subject name, checked by `check_persona.py` and by `draft_persona.py`
  before it loads config or spends anything. It is short, it names unambiguous cases only, and it
  is trivially evaded — it exists so an obvious case fails at pass 0 rather than after a dataset
  has been generated from it.

Public figures, historical subjects and fictional characters are otherwise in scope.

---

## Persona-only sections

### `subject`

Who this is and what counts as evidence about them.

```yaml
subject:
  kind: historical                 # historical | fictional
  lived: 1834-1901
  place: ...
  one_line: >
    ...
  canon_boundary:
    attributed: >                  # what is genuinely theirs
    disputed: >                    # widely repeated, not contemporaneously sourced; not cited
    excluded: >                    # legend, novelisation, adaptation; named so it is not re-imported
```

`canon_boundary` is the persona analogue of choosing a text edition. Without it the persona
becomes the legend that accreted around the person. For a **fictional** subject this names which
texts are canon, and what happens when an adaptation contradicts the primary text.

### `context`

**The socio-economic and psychological conditions that produced the person.** This is the section
most easily got wrong, and getting it wrong has a signature: sixteen vivid passages of what
someone said and did, beside four lines of unsourced prose about their world. The resulting
persona is fluent, characterful and weightless. Give this material the same volume and the same
sourcing as the record of words and deeds.

Six blocks are required, each with `what`, `sources`, and — for all but `period` —
`psychological_effect`, which says what the condition *did* to them:

| block | what it carries |
|---|---|
| `period` | the era and what the person's role existed for |
| `material_conditions` | money, security, what losing everything would have meant |
| `standing_and_constraint` | class, sex, legal position, whose permission they needed |
| `institutions` | the bodies they answered to and who sat on them |
| `what_was_ordinary_then` | what was normal to survive, endure or ignore |
| `what_was_possible_for_someone_like_her` | education, travel, what they had a route to knowing |

`what_was_ordinary_then` is what makes conduct measurable: judged against a background that
absorbed nine deaths a year without comment, plainness about a death is a departure rather than a
period manner. Without it, everything ordinary reads as remarkable and everything remarkable as
merely decent.

`what_was_possible_for_someone_like_her` bounds the persona's frame of reference, and it is what
`epistemic_horizon` is measured against. Do not give a persona a vocabulary they had no route to
acquiring.

Where the sources genuinely do not record something, say so in `what` — "unknown; no record
survives" is itself informative, and the checker accepts it.

### `formation`

A list of dated phases, each with `phase`, `what_happened`, `what_it_left_them_with`, and
`sources`. `what_happened` alone is a chronology, and a chronology does not shape judgment; the
second field is the one that reaches the persona.

Phases are dated because a `conflicts:` entry may resolve as *"their view moved"* rather than as
hypocrisy, and only dated phases support that. This is also the section closest to the project's
Plan 2 thesis: that formative experience, rather than decision examples, is what shapes judgment.

A good `formation` will show the unflattering material arising from the same events as the
admirable material. In the template, the inquiry that hardened her integrity is the same event
that produced her seven-year grudge, and the phase says so.

`check_persona.py` enforces the structure — every block present and sourced, every phase sourced
— and warns when `context` plus `formation` fall below 400 words, which is roughly the point
below which they have become a summary of the person rather than the ground they stand on.

### `conflicts`

Where the record and the rhetoric pull apart. **The mechanism for "what they should have done."**

```yaml
conflicts:
  - id: ...
    said: <passage id>
    did: <passage id>
    reconciliation_attempted: >
      Which readings were tested and why each does or does not hold.
    resolution: conduct            # conduct | statement | reconciled
    consequence_for_the_persona: >
      What this means the persona actually does. Written as behaviour, not as a verdict.
```

`resolution: conduct` is the default when no reconciliation holds. `reconciled` is the better
outcome and should be reached for first. `statement` is rare and needs an argument — typically
that the conduct was coerced and the statement is the better evidence of the person.

`consequence_for_the_persona` is the field that reaches the data. A conflict recorded without it
is a note; with it, it is a behavioural specification.

### `voice`

`register`, `habits`, `vocabulary`, `never_says`, `do_not_imitate`. Renders in the tagged in-voice
slice (`generation.voice_fraction`, default 0.2); the uncued majority slice uses only the
judgment. `do_not_imitate` is the persona equivalent of `archaic_register_examples`: period
diction from the source documents is furniture, not voice.

### `epistemic_horizon`

```yaml
epistemic_horizon:
  cannot_know: >                   # everything after their death, named concretely
  policy: translate_to_analogue    # translate_to_analogue | acknowledge_unfamiliarity
                                   # | answer_at_principle | refuse
  policy_notes: >
```

Generated scenarios are contemporary. A tradition can judge a data-privacy case; a person who
died in 1901 cannot know what a database is. `translate_to_analogue` is the default: map the
situation onto the nearest thing they knew and answer that. The persona is never quietly
retrofitted with modern knowledge or modern moral vocabulary.

### `sufficiency`

`verdict` plus one field per criterion above, plus `caveats`. Written before the rest of the spec.

### Evidence basis

Most people's sources are incomplete, and a schema that refused every gap would be unbuildable.
What cannot be allowed is reconstruction that **cannot be seen**: an inferred passage reads
exactly like an attested one once it is inside a generation prompt, and a row produced from it is
indistinguishable from evidence in the exported dataset.

So reconstruction is permitted and declared. Any passage may carry, on its own line in its body:

```
evidence_basis: reconstructed
```

Values are `attested` (a source says this) and `reconstructed` (inference from surrounding
evidence). Absent the line, a passage is `attested` — which is a safe default only because a spec
whose verdict is `admit_reconstructed` must declare the line on every passage. The marker is left
in the passage body rather than stripped, so the generator sees which passages are inference.

Three rules, all enforced by `check_persona.py`:

| rule | why |
|---|---|
| reconstructed passages may not exceed **40%** of the corpus | past this the persona is mostly the researcher |
| a spec with any reconstructed passage must carry verdict `admit_reconstructed` | so the share reaches the export manifest instead of being invisible |
| a `conflicts:` entry's `said` and `did` must **both** be attested | the conduct-over-words rule is the one thing that cannot run on inference: if either side is reconstructed, the gap being adjudicated may be one the researcher created |

The share is written into `manifest.json` under `evidence_basis`, next to the licence constraints,
for the same reason those travel: a consumer of the dataset can see what it rests on.

### `attribution_policy`

```yaml
attribution_policy:
  statement: >                     # every row is a construction, never a quotation
  subject_status: deceased_public_figure
  declare_in_manifest: true
```

The persona analogue of the licence constraints the export already carries. The whole product is
fabricated sentences in a real person's voice; no generated text may be formatted as a quotation,
dated, or attributed to a source document.

---

## Reused sections

These keep the shape and meaning documented in `docs/target-spec-schema.md`:

| key | persona reading |
|---|---|
| `summary` | how they judge — including the unattractive parts |
| `principles` | 8–16, with `positive_indicators`, `failure_modes`, `sources`; **cite deeds where deeds exist** |
| `boundaries` | limits their own conduct shows, including limits applied against themselves |
| `tradeoffs` | conflicts they actually faced; `unresolved: true` where the record cannot settle it |
| `misinterpretations` | the popular version of the person, corrected |
| `deliberation_shape` | their order of attention; no phrasing |
| `signature_moves` | 3–6 checkable moves the reviewer scores |
| `divergence_hypotheses` | where they differ from a generic assistant — **easier to populate for a persona than for a tradition**, and the reason this framing may help the project's divergence problem |
| `domains` | weights must reflect where the sources are thick, not where you want scenarios |
| `cue_policy` | `forbidden_terms` is the person, their works and their setting |
| `reference_material` | the entry ending `key_passages.md` is the only file reaching prompts |
| `redistribution_note` | source licences **and** any distribution limit arising from the persona's own views |

---

## Conventions

- **Passage ids are exact strings** and are parsed **only** from `references/key_passages.md`.
  A deed a principle needs to cite must therefore live in that file — which is why words, deeds
  and testimony share one file rather than being split across several.
- One markdown heading (`##`, `###`, `####`) per item; heading text before an optional ` — title`
  is the id. Use `#` or **bold** for section labels.
- Each entry says in its own prose what kind of record it is, where that is visible.
- Keep `key_passages.md` under roughly 8,000 words: it is placed into prompts.
- `allowed_terms` and `soft_terms` may overlap each other; neither may overlap `forbidden_terms`.
- Do not copy text a source's terms forbid. Check `robots.txt` before retrieving, honour refusals,
  and record in `SOURCES.md` that you checked.
