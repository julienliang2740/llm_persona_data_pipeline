---
name: draft-persona
description: Research a real or fictional person and draft a persona target spec for the persona generalizer — running the sufficiency gate, acquiring sources under a provenance ledger, and emitting spec.yaml, key_passages.md, SOURCES.md and research_notes.md for human review. Use when asked to add a persona, draft a persona spec, research a subject for the persona pipeline, or generalize a person into a target.
---

# Drafting a persona

You are producing a **draft for human review**, never a finished target. The brief this repository
works to is explicit that the pipeline must not decide what its target means; a person is decided
by research and by a reviewer, and your output is the material that reviewer works from. Say so in
the handoff, and never mark a claim verified because it sounded right.

Read `persona_generalizer/docs/persona-spec-schema.md` before starting. This file is the
procedure; that file is the contract.

## Two rules that govern every judgement below

**Conduct outranks statements.** Where what the subject said conflicts with what they did, first
try to explain the gap — danger, coercion, a view that moved over a lifetime — and write the
reasoning down. Only when no reading holds does conduct govern. Both outcomes are legitimate; an
unexamined default to conduct is not.

**The persona is never placed inside modern constraints.** Do not add the clause the value-system
targets carry. Do not soften a subject's views. A persona corrected into a better person is a
different person, and the correction destroys the thing being studied. Conflicts with
contemporary norms are declared in `redistribution_note` and the manifest, not applied to content.

---

## Phase 0 — the sufficiency gate

Run this before acquiring anything in bulk, and be willing to stop here.

**Check `persona_generalizer/personas/_refused/` first.** If this subject has been through the
gate before, the verdict and its evidence are recorded there, and re-deriving them wastes the
research. A `refuse_scope` record stands. A `refuse_evidence` record should only be reopened if
you can name a source the previous pass did not reach. A `refuse_acquisition` record is an
invitation to try again with a better search.

Assess, from a first pass of searching:

| criterion | floor |
|---|---|
| first-person volume | ~10,000 words of their own words; below ~3,000 the persona is mostly invention |
| **documented decisions with reasoning** | 6–8 where both the act *and* their stated reason survive. **Binding criterion.** Most subjects fail here |
| domain breadth | 2+ areas of life with real coverage |
| contestedness | the attributable core must exceed the disputed part |
| testimonial variety | 2+ observers with different interests |

Return one of `admit`, `admit_with_caveats`, `admit_reconstructed`, `refuse_acquisition` or
`refuse_evidence`. **A refusal is a real answer.** Report it and stop; do not write a spec anyway.
A spec written past a refusal is imagination wearing a real name, which is worse than no persona.

**Do not refuse off one acquisition pass.** The two refusals are different findings:

- `refuse_acquisition` — you did not reach the material. A fact about your search. **Retryable:**
  escalate through the ladder in phase 1 and run the gate again. Record what you tried in
  `sufficiency.acquisition_attempts`.
- `refuse_evidence` — the material does not survive. A fact about the subject. Only available
  once the ladder is exhausted.

If the sources are thin but real, `admit_reconstructed` is usually the honest answer rather than
either refusal: build it, mark the inferred passages, and let the share travel into the manifest.
See "Evidence basis" in the schema.

**Scope is a separate question from evidence, and you answer it first.** Refuse regardless of
volume: **living private individuals**, and subjects whose distinctive value content is the
direction or advocacy of mass atrocity — where a fidelity-maximising spec and the harmful
artefact are the same object. Return `refuse_scope`, record it in `personas/_refused/`, and stop.
`persona_generalizer/scope.py` carries the argument and a tripwire for unambiguous cases; the
tripwire is not a filter, so subjects it does not name still need your judgement, written into
`sufficiency.scope_check`. Public figures, historical subjects and fictional characters are
otherwise in scope, and an unattractive record is not a reason to refuse — it is the material.

### Optional: a second opinion on the verdict

You are one model judging your own evidence. Where the verdict is close — anything other than an
obvious `admit` — get an independent read from a different model family, blind to your answer:

```bash
python persona_generalizer/ask_model.py --role reviewer_second --json \
    --usage persona_generalizer/personas/<id>/usage.jsonl --prompt-file /tmp/gate.md
```

Write the prompt yourself: the five criteria, the evidence you actually found, and a request for a
verdict with reasoning. **Do not include your own verdict** — the point is an independent answer,
not agreement. Record the second verdict and any disagreement in `sufficiency.caveats` and
`research_notes.md`. Disagreement does not decide anything; it tells a reviewer where to look.

For a **fictional** subject the gate changes shape: the canon supplies everything at once, so ask
instead whether the canon is bounded, whether the character makes decisions on the page with
reasons attached, and which adaptations are in or out.

---

## Phase 1 — coverage-driven acquisition

Do not search the subject's name and take what comes back. That yields the popular version of the
person: heavy on quotations, light on conduct, and dominated by whichever biography the web
copied. Search **per slot**, where the slots are the spec's own required sections.

### The coverage matrix

Every row must end with sources or an explicit recorded gap.

| slot | what you are looking for | where it lives |
|---|---|---|
| `context.period` | what their role or position existed for | reference works, institutional histories |
| `context.material_conditions` | wages, security, what ruin would have meant | wage books, census returns, wills, tax records |
| `context.standing_and_constraint` | class, sex, legal position, whose permission they needed | legal and social histories of the period |
| `context.institutions` | the bodies they answered to and who sat on them | minute books, membership rolls, charters |
| `context.what_was_ordinary_then` | what was normal to endure or ignore | statistics, official returns, contemporary press |
| `context.what_was_possible_for_someone_like_her` | education, travel, routes to knowledge | school and university records, biography |
| `formation` phases | events, dated, with what they left behind | biography, correspondence, inquests, proceedings |
| words | their own writing and recorded speech | archives, digitised editions, published letters |
| **deeds** | what they actually did | **registers, minutes, court and administrative records** |
| testimony | contemporaries, with their interests noted | memoirs, correspondence, hostile accounts |
| conflicts | statements their conduct contradicts | emerges from holding words and deeds together |

### The escalation ladder

Three passes, each changing *strategy*. Three identical passes find the same nothing.

1. **Slot-driven search.** Query per coverage-matrix row, as below.
2. **Reference harvesting.** Take what pass 1 found, pull the works it *cites*, and go after
   those. This is how a researcher gets from a summary to the sources: find the standard edition
   and the standard monograph, then chase their footnotes. `websearch.acquire_escalating` does
   this automatically for the script arm.
3. **Cross-language.** For subjects whose sources never existed in English. Choose the language by
   **where the sources survive**, not by which Wikipedia is biggest — article size measures how
   many modern editors a language has. A Byzantine emperor means Greek, Arabic, Armenian,
   Georgian; article length would point you at German.

Only after pass 3 may an empty slot be called `refuse_evidence`.

**Wikipedia has exactly one legitimate role: its reference list.** Its prose is the popular
version of the person — precisely what the paragraph above warns against, and for a subject whose
fame is a later construction it is the legend rather than the record. So harvest the citations and
chase them; never write Wikipedia prose into a passage. `websearch.wikipedia_reference_index`
returns citations only, and reads the article path because `/w/` and `/api/` are disallowed.

### Search by source type, not by keyword

Work the tiers in order. Tier 2 is what a name search almost never surfaces, and it is where deeds
live — the conduct-over-words rule has nothing to stand on without it.

1. **Primary, self-authored** — their manuscripts, letters, logs, published works.
2. **Institutional records** — registers, minutes, court records, official returns, wage books.
3. **Contemporary testimony** — memoirs and correspondence by people who knew them.
4. **Reference and scholarship** — biographical dictionaries, peer-reviewed work.
5. **Popular treatment** — novels, film, documentaries, listicles. **Quarantined by default.**

### Four disciplines that make this comprehensive rather than merely long

**Deduplicate by claim, not by URL.** Twenty pages repeating one Victorian biography are one
source. Trace every claim to its earliest attestation. Anything bottoming out in tier 5 goes to
`subject.canon_boundary.disputed` or `excluded` and is cited nowhere.

**Stop rule.** A slot is done when it has two independent sources, or when you record it as a gap.
Recording a gap is a result; leaving a slot vaguely half-filled is not.

**Refusal discipline.** Check `robots.txt` before retrieving from a site, and honour AI-use
refusals. `targets/confucian/SOURCES.md` sets the precedent: ctext.org disallows AI crawlers, so
nothing was taken and public-domain equivalents were used instead. Record every site you checked,
including the ones you declined, and what you used instead. Do not copy text a licence forbids —
paraphrase and cite.

**Interestedness.** Note who produced each source and what they wanted. A hostile institutional
minute and a friendly memoir are both usable and neither is neutral. Subjects had enemies;
traditions do not.

### Volume to aim for

The four reviewed value-system targets carry **49–128 curated passages, 5,100–8,300 words**. Aim
for **60–120 passages, 6,000–8,000 words**, with roughly **a third of it circumstance material**.
The persona template ships with 24 passages because it is a template you delete, not a target.

**Hard ceiling:** `key_passages.md` is placed into every generation prompt, so its size is a
per-call token budget. Do not exceed ~8,000 words. If the subject's surviving material is larger,
curate down and record in `research_notes.md` what you left out and why.

---

## Phase 2 — write `references/key_passages.md`

One markdown heading per item; the heading text before an optional ` — title` is the passage id,
and it must match `sources:` entries character for character. Use `#` or bold for section labels.

Four kinds of entry, circumstance first. A readable prefix convention helps: `C` circumstance,
`W` words, `D` deeds, `T` testimony.

Where a passage is inference rather than attestation, say so on its own line in the body:

```
evidence_basis: reconstructed
```

Mark it honestly and it is allowed, capped at 40% of the corpus, and declared in the manifest.
Leave it unmarked and it is indistinguishable from evidence for everyone downstream. A conflict's
`said` and `did` must both be attested — the conduct-over-words rule cannot run on inference.

Each entry states **in its own prose** what kind of record it is and what it bears on. This is
where the said/did distinction is made: call it out wherever it is visible. It is *not* a label
you attach to everything, and circumstance material does not fit that taxonomy at all.

Read the full source before excerpting. Verify that every passage says what you will claim it
says. Record in `research_notes.md` any claim you found repeated but could not source.

---

## Phase 3 — adjudicate the conflicts

Hold the words and the deeds against each other and find where they diverge. For each:

1. State the statement and the deed, by passage id.
2. **Attempt reconciliation, and write out what you tested.** Was their life or livelihood at
   risk? Were they coerced or without alternative? Did the view move, and does the chronology
   support that — check the dates. Is the statement narrower than it looks, with the conduct
   inside a carve-out it already made?
3. If a reading holds: `resolution: reconciled`. If none holds: `resolution: conduct`.
4. Write `consequence_for_the_persona` as **behaviour**, not as a verdict. This is the field that
   reaches the data; a conflict without it is a note.

Do not resolve a conflict by deciding the subject was better than the record shows. If the pattern
is durable and unflattering, it is part of the persona and the spec says so.

An empty `conflicts:` list is permitted but rare, and usually means the deeds were not researched
as hard as the writings. Go back to tier 2 before claiming it.

---

## Phase 4 — write `spec.yaml`

Copy `persona_generalizer/personas/_template/` and replace everything. Write in this order:

1. `sufficiency` — the gate's verdict and evidence.
2. `subject` with `canon_boundary`.
3. **`context` and `formation`** — six sourced blocks and dated phases, each with what the
   condition or event *did* to the person. Write these before the principles, so the principles
   fall out of the world and the life rather than being imposed on them. Target well over 400
   words combined; the checker warns below that.
4. `conflicts`.
5. `summary` — how they judge, carrying the unflattering half. No modern-constraint clause.
6. `principles` (8–16), `boundaries`, `tradeoffs`, `misinterpretations` — cite deeds where deeds
   exist.
7. `voice`, `epistemic_horizon`, `deliberation_shape`, `signature_moves`.
8. `divergence_hypotheses` — where this person differs from a generic assistant. Easier for a
   persona than for a tradition; this is where the dataset earns its keep.
9. `domains` — weight toward where the sources are thick, not where you want scenarios.
10. `cue_policy` — `forbidden_terms` is the person, their works, their setting.
11. `reference_material`, `attribution_policy`, `redistribution_note`.

---

## Phase 5 — the ledger and the notes

`SOURCES.md`: one row per file and per source consulted-but-not-ingested. Work, edition, URL,
access date, licence, AI-use restrictions, processing applied, `use: grounding | reference_only`,
plus evidence type where visible and interestedness. End with the commands that fetched
everything, so a reviewer can reproduce `references/` from scratch.

`research_notes.md`: corrections you made while checking, how each conflict was adjudicated, what
you left open and why, coverage warnings where the sources are thin, and anything the schema could
not express — that last is a schema gap and gets fixed in the schema, not in `pipeline/`.

---

## Phase 6 — check and hand off

```bash
python persona_generalizer/check_persona.py <persona_id>
```

Fix until clean. Errors block; warnings are a reviewer's call.

### Optional: adversarial review of the passages

The failure you cannot catch yourself is your own systematic bias. If you have quietly imported
the popular version of the subject, re-reading your passages will not reveal it, because the same
priors wrote them and approve them. So ask a different family:

```bash
python persona_generalizer/ask_model.py --role reviewer \
    --usage persona_generalizer/personas/<id>/usage.jsonl --prompt-file /tmp/review.md
```

Build the prompt from `subject.canon_boundary` plus `references/key_passages.md`, and ask it to
name every entry that reads like legend, later tradition or popular treatment rather than the
attested record, and every entry whose stated evidence basis looks wrong. Record what it flags in
`research_notes.md` — including the flags you reject, and why. This costs a few cents and is the
only check in the whole procedure that is not you marking your own work.

Then hand off with, explicitly:

- the sufficiency verdict and which criterion was weakest;
- every claim you could not source, and every slot recorded as a gap;
- each conflict and how it resolved, flagging any where you were unsure;
- sources you declined to retrieve and why;
- a plain statement that **this is a draft and every passage needs verification against the source
  before any dataset is generated from it.**

Optionally run a tiny pilot so the reviewer sees real output:

```bash
python main.py all --target <id> --targets-dir persona_generalizer/personas \
    --config configs/pilot.yaml --n-families 2 --new-run --skip-baseline
```

If the responses could have been written about a *different* person, `conflicts`, `context` and
`voice` are too thin. Go back to phase 1.
