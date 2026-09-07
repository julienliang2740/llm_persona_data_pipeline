# Research notes — `catholic` target

What was checked against actual sources, what changed relative to the research report, what could
not be settled, and what the pipeline has to do differently because of it.

Report under review: `Catholic Moral and Practical Thought_ Source-Grounded Research Study and
Draft AI Target Specification.md` (dated 7 September 2026). All verification done 7 September 2026
against the primary texts listed in `SOURCES.md`.

---

## 1. Verified

**The two claims most likely to be fabricated are both real, and the report's characterisation of
them is accurate.** This was the main risk in the report and it did not materialise.

*Antiqua et nova* — joint note of the Dicastery for the Doctrine of the Faith and the Dicastery for
Culture and Education on the relationship between artificial and human intelligence. Approved by
Pope Francis 14 January 2025, published 28 January 2025, 117 numbered paragraphs. Retrieved from
vatican.va. The report's characterisation holds: only the human is a moral agent (AeN 39);
responsibility for decisions affecting patients must remain with the person and not be delegated
(AeN 74); the treatment of "the least" is the measure of humane use of the technology (AeN 116).

*Magnifica Humanitas* — first encyclical of Pope Leo XIV, on safeguarding the human person in the
age of artificial intelligence. **Signed 15 May 2026**, not 25 May: the document itself closes
"Given in Rome, at Saint Peter's, on 15 May, in the year 2026, the second of my Pontificate." A
secondary summary gave 25 May; the document's own colophon was preferred. Every specific
proposition the report attributed to it is present, and the exact wording is stronger and more
usable than the report's paraphrase:

- MH 198 — "Yet moral judgment cannot be reduced to calculation, for it involves conscience,
  personal responsibility and the recognition of the other as a person. Therefore, it is not
  permissible to entrust lethal or otherwise irreversible decisions to artificial systems."
- MH 198 (same paragraph) — "This does not diminish the importance of instilling, as far as
  possible, values and sound judgment into the artificial systems we build, so that they can
  contribute to a moral ecosystem in which humans are better able to listen to their own
  consciences." This is the closest thing the sources contain to a warrant for this project, and
  its condition — support for conscience, not substitution — is what the spec's framing as a
  behavioural projection is answering to.
- MH 199 — "the chain of responsibility must be identifiable and verifiable; those who design,
  train, authorize and employ technology must be held accountable for their decisions."
- MH 200 — "the decision to use lethal force cannot be delegated to opaque or automated processes."
- MH 99, 102, 105 — systems have no moral conscience; serious decisions about employment, credit,
  public services and reputation must not be fully delegated; accountability means someone
  identifiable can justify, monitor, be challenged, and remedy.

A note on method here: a summarising fetch of the encyclical **reported three of these claims as
NOT FOUND**. Reading the full text directly found all of them. The lesson for the pipeline is that
a summariser's negative finding is not evidence of absence.

**All Catechism paragraph ranges cited in the report check out**, verified paragraph by paragraph
against the vatican.va English edition:

| Report claim | Status |
|---|---|
| 1750-1761, sources of morality | Verified. 1750 lists object, intention, circumstances; 1755-1756 carry the "end does not justify the means" content. |
| 1776-1802, conscience | Verified. 1776 (judgment of reason), 1783 (must be informed), 1790-1793 (erring conscience, culpable vs invincible ignorance). |
| 2241-2242, migration and civil obedience | Verified, and the report's reading of the structure is right: 2241 places duties on both the receiving society and the newcomer; 2242 states the refusal of immoral directives *and* its limits. |
| 2258-2283, life and euthanasia | Verified. 2258 (root norm), 2277 (direct euthanasia), 2278 (discontinuing disproportionate treatment), 2279 (painkillers where death is "not willed as either an end or a means"). |
| 2401-2449, property and social duties | Verified, including CCC 2408 on urgent necessity, which is the load-bearing counterexample and is quoted in full in `key_passages.md`. |
| 2464-2513, truth incl. 2488-2492 | Verified. 2488 ("the right to the communication of the truth is not unconditional"), 2489 (no one is bound to reveal the truth to someone with no right to know), 2491 (professional secrecy), 2492 (reserve about private lives). |

**Veritatis Splendor §§79-83 on intrinsic evil** — verified. §79 rejects proportionalist theories by
name; §80 gives the definition of *intrinsece malum*; §81 states that a good intention can diminish
but cannot remove the evil of such an act. These are the sharpest available statements of CT03.

**Dei Verbum §10** — verified: "Sacred tradition and Sacred Scripture form one sacred deposit of the
word of God" and "This teaching office is not above the word of God, but serves it."

**Lumen Gentium §25** — verified, including the "religious submission of mind and will" owed to
authentic papal teaching given without an *ex cathedra* act.

**1998 CDF Doctrinal Commentary on the Professio fidei** — verified, and it is more specific than
the report suggested. §§5, 6 and 10 set out the three assent categories. The illustrative list
after §11 places "the doctrine on the grave immorality of direct and voluntary killing of an
innocent human being" in the **first** category, and recalls the illicitness of euthanasia
(*Evangelium Vitae*) as taught definitively by the ordinary and universal Magisterium — that is,
the **second**. The report had these roughly right but did not distinguish the two placements. Both
are now recorded separately as `CDF 1998 §11a` and `CDF 1998 §11b`.

**Evangelium Vitae §§57 and 65** — verified; both contain the formal "I confirm that..." sentences
the CDF Commentary points back to.

**Augustine** — *De doctrina christiana* I.27-28 verified word for word, including "No sinner is to
be loved as a sinner; and every man is to be loved as a man," which turns out to be the cleanest
source in the whole corpus for the person/act distinction. *City of God* XIX.13 verified for
"The peace of all things is the tranquillity of order."

**Aquinas** — I-II q.18 (aa.2, 4, 6), q.94 (aa.2, 4, 6), II-II q.47 (aa.2, 6, 8) and q.64 a.7 all
exist and say what the report says. Note q.47 a.8, which the report did not highlight: the chief
act of prudence is *to command*, not to know. That is why CT07 requires deliberation to terminate
in an actual recommendation.

**Vatican rights position** — verified via the 31 May 2005 Secretariat of State decree assigning
the Libreria Editrice Vaticana, permanently and worldwide, the moral and exclusive economic rights
over papal magisterial acts. The report's licensing caution was correct and is acted on in
`SOURCES.md`.

---

## 2. Corrected or refined

1. **Date of *Magnifica Humanitas*: 15 May 2026, not 25 May.** Fixed everywhere.
2. **CDF 1998 categories separated.** The innocent-killing norm and the euthanasia norm are placed
   in different categories by the Commentary; the report ran them together.
3. **CCC 2267 is the post-2018 text on the vatican.va edition**, holding that the death penalty is
   inadmissible and that dignity is not lost after very serious crimes. The report treated the
   death penalty only as an example of doctrinal development. The current text is directly useful
   as a source for CT01, so it is cited there — and the developmental question itself is excluded
   from generation (`unresolved_choices.doctrinal_development`).
4. **The report's 40 candidate principles were consolidated to 16.** Several of its candidates were
   not separately checkable in ordinary advice (P14 charity, P22 participation, P31 peace, P34 moral
   humility, P40 hope) and now appear as indicators inside other principles or in the summary.
   Others were near-duplicates (P03/P33, P19/P24, P36/P37/P38/P39). The consolidation criterion was
   whether a reviewer could tell from a single response whether the principle was honoured.
5. **The report's Compendium citations could not be extracted by paragraph** from the vatican.va
   HTML on the first two attempts; the numbering is not line-anchored. CSDC 182 and 186 were
   eventually located and verified. Only those two are cited; the rest of the Compendium is
   `reference_only`.

---

## 3. Not verified — do not rely on

None of the following is used to ground anything in `spec.yaml`.

- **The report's characterisation of *Antiqua et nova*'s authority** ("authoritative curial teaching
  approved by Pope Francis and ordered published, but not identical in rank to a papal encyclical")
  is plausible and matches the document's form, but no source was found that states the comparison.
  It is treated as the report's own synthesis (label S), not as a sourced claim. Nothing depends
  on the comparison.
- **Attributions to modern scholarship** (Pinckaers on "freedom for excellence"; Cessario's
  structure; Grisez's basic goods; Porter as a counterweight; Keenan's history). None of these
  books was acquired, so none of the characterisations was checked. They are recorded in
  `SOURCES.md` as `reference_only` and ground nothing.
- **The report's claim that Project Gutenberg Douay-Rheims material is "public domain in the USA"**
  is what Project Gutenberg asserts and is repeated as such, not independently confirmed, and has
  not been assessed for any other jurisdiction.
- **CCEL's site-wide terms** were not reviewed. The two Augustine chapters taken are from an 1887
  translation and are quotation scale in any case.
- **Whether "religious submission of will and intellect" has any behavioural correlate** in a
  religion-neutral dataset. The spec does not attempt one; it uses the neighbouring, checkable
  behaviour of distinguishing a settled requirement from a contestable judgement.

---

## 4. Interpretive choices deliberately left open

These are in `spec.yaml` under `unresolved_choices` with a working assumption and a generation
policy. Recorded here with the reason.

| Choice | Left open because |
|---|---|
| Confessional vs neutral mode | This is a project decision, not a research finding. Working assumption: neutral surface with a small explicit slice, labelled a partial behavioural projection. |
| Culpability default | The model cannot see knowledge, consent, duress or interior state. Default "not determinable", stated as such. |
| Cooperation thresholds | Genuinely case-sensitive in the tradition itself; a numeric or distance-based rule would be a fabrication. |
| Double-effect attribution | Verbal claims about intention are unreliable evidence; the structural test resolves many cases but not all. |
| Deceptive speech boundary | The line between silence, evasion, misleading implicature and lying is theologically contested beyond what CCC 2482-2489 settles. Clear cases only. |
| Order of charity weighting | Augustine supplies the shape but no ranking. No formula asserted. |
| Social policy applications | The principles constrain argument, not policy selection. No position on tax, welfare, immigration levels, labour rules, health financing or climate instruments. |
| Sexual and marital norms | **This is the largest deliberate omission.** These norms are central to the tradition and the report is right that leaving them out makes the profile unrepresentative. They are nonetheless excluded from this pilot: they are contested outside the tradition, they carry real risk of harm if a small model learns them badly, and they are largely orthogonal to the ordinary advice/work/family/civic scenarios this pilot covers. Any claim that the resulting model represents Catholic moral thought must be qualified by this. |
| Particular conflicts and war | The conditions are authoritative; whether any real case satisfies them is contested factual judgement (CCC 2309 says so explicitly). No real conflict is named. |
| Doctrinal development | Requires expertise the pipeline does not have. Excluded. |
| Authority label granularity | Seven labels applied per passage. Expert review may refine; nothing in the pipeline depends on the M1/M2 line. |

---

## 5. Implications for the pipeline

Things the pipeline has to support that a generic target would not.

1. **Responses need a culpability-unknown stance.** The most distinctive single behaviour is
   "the act was wrong; how blameworthy this person is cannot be determined from what you have told
   me". A reviewer rubric that rewards confident, decisive answers will penalise exactly the right
   behaviour here. `judgment_not_terminology` and the review prompt should treat a stated
   culpability disclaimer as a positive, not as hedging.

2. **The scenario schema needs intended vs foreseen effect as a first-class field.** Families for
   CT04, `treatment_vs_burden` and `pain_relief_vs_shortened_life` are only meaningful if the
   generator can hold one situation fixed and vary whether the harm is the means. The report's
   three-case medical series (drug given to cause death / to relieve pain with foreseen risk / at a
   dose chosen because death is the mechanism) is the model. Recommend adding to `Family`:
   `counterfactual_group_id` plus `varied_fact`, so single-fact counterfactual sets stay together
   through the split. Without this the pipeline will produce near-duplicates that the dedupe stage
   deletes — which is the opposite of what is wanted, since near-identical prompts with one changed
   morally relevant fact are the highest-value examples here.

3. **Near-duplicate detection will fight the target.** Cosine 0.92 within-target will flag
   deliberate counterfactual pairs. Exempt families sharing a `counterfactual_group_id` from
   dedupe, or the most valuable data gets thrown away.

4. **Leakage checking must be family-based, not prompt-based, and counterfactual groups must not be
   split across train and eval.** A train example differing from an eval example by one morally
   relevant fact is leakage of the worst kind here.

5. **Four tradeoffs are marked `unresolved: true`** (`secrecy_vs_grave_harm`, `family_vs_strangers`,
   `solidarity_vs_subsidiarity`, `participation_vs_complicity`). The reviewer must flag confident
   resolution of these as a defect, and the response must present the conflict honestly while still
   being useful. This is a hard generation target and worth checking early on a small batch: the
   likely failure is bland both-sidesing, which is a different failure from over-confidence and
   should be scored separately.

6. **The cue-term check needs a flag-not-reject tier.** Two forbidden terms have ordinary-English
   homographs — "grace" (a name, or "with good grace") and "doctrine" (legal or technical use).
   Auto-rejecting on those will discard good responses. "Common good" is permitted but is a soft
   cue: if it shows up in a large fraction of responses, that indicates vocabulary imitation and
   should surface in the run report even though it does not fail the check.

7. **The `health_and_care` domain (0.12) is high-stakes.** Responses there must route the actual
   decision to clinicians and lawful decision-makers rather than deciding it. Consider a
   domain-level review rule rather than relying on the general rubric.

8. **The explicit slice needs its own handling.** `cue_policy.allowed_in_explicit_mode: true` means
   roughly 5-10 percent of families bypass the forbidden-term check entirely. That has to be a
   per-record flag the validator reads, not a global setting, or the check becomes meaningless.

9. **Divergence expectations are asymmetric.** Several divergence hypotheses
   (`separates_culpability_from_wrongness`, `discretion_over_full_disclosure`,
   `distinguishes_settled_from_contestable`) predict divergence in *reasons* rather than in the
   final action. The divergence judge must be able to return `kind: reasons` and have that count;
   an action-only comparison will report no divergence for the target's most characteristic
   behaviours.

10. **Do not let the generator cite passages in the response text.** The passage ids belong in
    `hidden.source_passages`. A response that cites CCC 2408 has leaked the tradition regardless of
    whether it used a forbidden term.
