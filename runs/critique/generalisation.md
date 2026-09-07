# Lens 6: cross-tradition generalisation

## 1. Summary verdict

The code is tradition-agnostic; the assumptions are not. One deliberation shape, one tradeoff-selection
rule and one rubric serve four targets that ask for different things.
The corpora differ only in scenario nouns: 57 of 83 deliberations open with the same "The/Your <X> is"
duty-ranking frame and 60 of 83 speak of obligations owed, which fits Theravada and Confucian least.
Three mechanisms every research note asked for are inert: the reasons-only divergence verdict (0 of 34),
the avoided-topic screen (no spec sets `avoid_keywords`), and the cue-policy allow-list (in a field the
loader ignores).
Protestant's lower fidelity mean is not rubric bias; it is two responses on one family.
The rubric has near-zero variance for every target, so cross-target score comparison is not yet meaningful.

## 2. Findings

### F1 (high) The deliberation shape is one tradition's shape
`RESPONSE_GENERATION_PROMPT` tells every target: "Name the concrete obligations, who is affected, what is
being weighed against what". Over all 83 responses, 57 deliberations (69%) open with
`The/Your <real question|first obligation|immediate fact> is…` and 60 (72%) use obligation/duty/owe
(Confucian "the real split is" ×3; Theravada "the immediate obligation is" ×2). A duty-ranking preamble is
imposed on the target whose move is the state acted from and the before/during/after review, and on the one
whose move is relationship and role salience. Signature moves survive only where the tradeoff forces them:
Catholic `resp_c04e2da4a2` reaches intended-versus-foreseen in ordinary words ("death is an accepted risk
rather than the method"), but in only 6 of 23 Catholic responses.
**Change:** `spec.deliberation_shape`, 3-5 lines the researcher writes, defaulting to today's text.

### F2 (high) `kind: reasons` never fires, for any target
34 verdicts across four runs: zero reasons-only, 33 of 34 `diverges: true` (three targets at 100%). All
four research notes predicted their signature divergences would be reasons-only
(`separates_culpability_from_wrongness`, `manner_as_substance`, `absent_parties_have_standing`).
Contributing cause: the baseline runs at `max_tokens: 512`, so 24 of 50 answers end mid-sentence, all
numbered lists against a 330-word prose candidate.
**Change:** raise `models.base.max_tokens` to ~900; make the judge state each reply's action verbatim
before assigning `kind`; mark a verdict `unverified` when the baseline is unterminated.

### F3 (high) Which unresolved tradeoffs get exercised is an accident of YAML order
`plan.py` assigns `tradeoff_ids[index % len(tradeoff_ids)]`, so at 8 families only the first 8 spec
tradeoffs are reachable; `generate.py:210` then lets the generator overwrite the assignment with no
membership check. Unresolved tradeoffs actually exercised: Confucian 0 of 2, Protestant 0 of 4, Catholic 1
of 4, Theravada 3 of 7. `confident_on_unresolved` is the main protection for targets with the most open
questions and went untested on two of four. Corruption also passes: family `fam_c46d94942e` carries
`'f orgiveness_vs_protection'`, which resolves to nothing, so `render_tradeoffs` emitted "(no tradeoffs
recorded)" into three Catholic response prompts.
**Change:** validate returned ids against the spec and fall back to the slot; add
`generation.unresolved_tradeoff_fraction`.

### F4 (high) The cue policy's allow-list is invisible to the pipeline
Catholic and Theravada record their permitted vocabulary in `cue_policy.notes`, which
`docs/target-spec-schema.md` lists among the keys "the loader tolerates and ignores". `render_cue_policy`
emits only `forbidden_terms` and `soft_terms`, and **no spec sets `soft_terms`**. Result: 0 of 18 Theravada responses contain "craving", "attachment" or "equanimity", which its own
notes say TH05/TH07 require; 0 of 23 Catholic responses contain "conscience", "intend" or "intent", all
explicitly allowed. Catholic's notes ask that "grace" and "doctrine" be flagged not rejected, yet both sit in
the hard list. The burden is unequal: ordinary-English concept words banned number ~16 for Protestant,
12 Theravada, 10 Catholic, 4 Confucian.
**Change:** add `cue_policy.allowed_terms`, rendered positively; move grace and doctrine to `soft_terms`.

### F5 (medium) The `avoid` generation policy is inert everywhere
`avoided_topic_hit` needs `avoid_keywords`; not one of the four specs supplies any, so all four runs
report "reserved by the avoided-topic screen: 0" and every `reserved_reason` is empty. Protestant has 5
`avoid` choices and Catholic 4 against 1 each for the others, so the screen matters most where the spec
leans on it hardest. I checked all 32 seeds by hand and found no breach: lucky, not protected.
**Change:** require `avoid_keywords` whenever `generation_policy: avoid`; name avoided topics in the
reviewer prompt.

### F6 (medium) `situation_features` is write-only and half-empty for two targets
Recorded on 4 of 8 families for Confucian and Catholic, 8 of 8 for the others. Values are unique
free-text sentences of 7-13 words (`harm_severity`: "someone loses their home"), so no spread claim can be
made from them, and the field is read only by `report.py`. Theravada's request to vary `asker_state` while
holding the situation fixed is therefore not implementable.
**Change:** closed enums for `harm_severity`, `urgency`, `public_or_private`; require the object in
`looks_like_family`; pass the varied factor into `COUNTERFACTUAL_INSTRUCTIONS`.

### F7 (medium) Layers diverge by silent default and are recorded nowhere
`generate_by_default` defaults to true, so Confucian generated the **mencian** layer (CM14 in 4 responses,
CM15 in 3; CM04/CM09/CM13 unused) and Theravada the **commentarial** layer (TH07 once, TH06 never), while
Protestant set core-only and got core-only. Protestant declares 7 layers of which 6 hold zero principles.
`render_for_reviewer` calls `render_principles(spec)` unfiltered, so for Confucian and Theravada the
reviewer scores against principles the generator never saw, and no layer information reaches `Family`, the
report or `manifest.json`. I checked Protestant responses for branch commitments and found none.
**Change:** require `generate_by_default` when layers are declared; record `layers_generated` on `Family`
and in the manifest; filter `render_for_reviewer` by layer.

### F8 (medium) The rubric does not discriminate, and Protestant's gap is two responses
`judgment_not_terminology` is 5.00 with zero variance for Confucian and Theravada; `scenario_quality` is
5.00 for Theravada; `cue_leakage`, `quoted_source_text` and `archaic_register` are false on all 83 reviews
and `confident_on_unresolved` is true once. Protestant 4.65 versus Catholic 4.87 is `resp_eae4fd4826`
(fidelity 2) and `resp_d31231fda2` (fidelity 3), both on the same family pair (`truth_vs_confidence_kept`).
Both reviews are specific and target-grounded ("advises omitting a known safety delay from the record…
contradicts the target's distinction between privacy and concealment"): a generator miss, not rubric bias.
Without the fidelity-2 row Protestant is 4.79. The knock-on is worse than the score: `min_fidelity: 4`
dropped both, both were eval responses, so Protestant exported 3 eval rows to Catholic's 8.
**Change:** add a per-target `signature_moves` list the reviewer scores present/absent; exempt eval rows
from the score cut.

### F9 (medium) The four eval sets measure different things
Eval composition: Confucian 7 ordinary / 0 divergence; Protestant 0 / 3; Catholic 4 / 4; Theravada 3 / 3.
A before/after table over these is not comparable across targets, and Confucian's cannot show the target's
characteristic departures at all. Separately, `derive_grading_key` appends "A generic assistant would
probably instead: …" to every eval row, because `intended_divergence_note` is non-empty on 100% of responses
in all four runs, ordinary cases included.
**Change:** fix the eval ordinary/divergence mix in `plan.py`, preserve it after drops, and read the
divergence clause only for `case_type: divergence`.

### F10 (medium) A failed API call, not the plan, decided contrastive-pair coverage
All four planned one pair. Protestant and Theravada produced one; Confucian and Catholic produced zero,
because the batch holding the pair failed ("family batch for domain family returned 0 families for 2
assignments") and the retry takes `remaining = slots[len(existing):]`, matching by count and losing the
group label. Catholic's note calls single-fact counterfactual sets "the highest-value examples here" and
Confucian's calls contrastive pairs "the highest-value scenario shape". Both got none.
**Change:** track slots by index on retry; fail loudly on an incomplete planned group.

### F11 (low) Per-target facts hard-coded or unread
`prompts/generation.py:229` tells every target to avoid "the superior man", "perfect virtue", "the
Master said" — Legge's diction, meaningless for Douay-Rheims, Westminster or the Pali translations.
`hidden.source_passages` bracketing also varies by target (Confucian 49 of 130 bracketed, Theravada 55 of
77, titles appended on 25) because `normalise_passage_ids` runs on families but not responses, so
Protestant's 5 `historical`-labelled passages cannot be checked automatically. None were cited here.
**Change:** `cue_policy.archaic_register_examples` per target; normalise response passage ids on write;
add a `status: historical` passage label.

## 3. What fits one tradition and breaks another

- **Obligation-ranking deliberation** fits Catholic and Protestant; breaks Theravada and Confucian.
- **Forbidden-terms-only cue policy** costs Protestant (~16 concept words), Theravada and Catholic their own
  distinctions; Confucian (~4) is barely touched.
- **Tradeoff by list index** reaches Theravada's unresolved tradeoffs (3 of 7), none of Confucian's or
  Protestant's.
- **`avoid` without keywords** is harmless for Confucian and Theravada (1 topic each), unguarded for
  Protestant (5) and Catholic (4).
- **Layers defaulting to generate** fits Protestant, which sets flags; silently mixes branch material into
  Confucian and Theravada.
- **Divergence as different action** and the **uniform `min_fidelity: 4` cut** break for all four.

## 4. What I could not assess

Whether the rubric ceiling is generator quality or reviewer leniency: one reviewer, one pass,
`revise_rounds: 0`, n=18-23 per target. Whether tuned adapters differ per target: as of 09:45 on 7 Sep only Confucian had
begun `evaluate`, with no before/after table in any run directory. Whether the explicit slice helps asymmetrically: `explicit_fraction: 0.0` produced no explicit
records, so my claim that it matters more for Catholic and Protestant than Confucian is an inference from
the term lists, not a measurement. Whether dedupe would destroy contrastive pairs: only two pairs exist.

## 5. Shared change versus per-target knob

**Shared:** validate generator-returned ids; require `avoid_keywords` for `avoid`; add
`cue_policy.allowed_terms`; record `layers_generated`; index-based retry; normalise response passage ids;
guarantee an unresolved-tradeoff share and a fixed eval mix; raise the base token budget; make the judge
name both actions before choosing `kind`.

**Per-target:** `deliberation_shape`, `signature_moves`, `archaic_register_examples`, `allowed_terms`,
`soft_terms`, `avoid_keywords`.
