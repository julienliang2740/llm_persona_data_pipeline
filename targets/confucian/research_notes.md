# Research notes — early Confucian target

What was checked against the sources, what the research report got wrong, what was left open
on purpose, and what this target implies for the pipeline.

Report reviewed: `Confucius and Mencius_ Research and Draft Value-Instantiation Specification.md`.
Its philosophical framing held up well. Almost everything corrected below is a citation or a
detail of emphasis, not a misreading of the tradition.

---

## 1. Corrections to the report

**The reciprocity passage is Legge 15.23, not 15.24.** The report cites "15.24" for
己所不欲，勿施於人. That is the commonly cited (Zhu Xi) number. In Legge's own division — the
text now in `references/` — it is 15.23, because Legge counts as one chapter the two openings
of book 15 that are usually counted separately. From 15.2 onward Legge runs one lower. Ids in
`spec.yaml` follow Legge, and `key_passages.md` gives the alternate number in brackets. All
other passage numbers the report cites (13.18, 4.18, 13.23, 4.16, 12.22, 2.7, 3.4, 9.3) are
identical in both systems; each was confirmed against the Chinese anchor text
(父為子隱, 事父母幾諫, 和而不同, 喻於義, 樊遲問仁, 犬馬, 林放問禮, 麻冕).

**Mengzi 7A.35 is stronger evidence than the report makes it.** The report says Mencius "tries
to preserve both filial commitment and the proper functioning of public justice." True, but it
undersells the passage. Asked what Shun would do if his father committed murder, Mencius says
the minister of justice would simply arrest him, and that Shun *could not have forbidden it* —
"Gao Yao had received the law from a proper source." Shun's filial option is to abandon the
throne "as throwing away a worn-out sandal" and carry his father into exile. So the tradition's
own hard case has the sovereign decline to obstruct justice and pay the cost personally. This
is the single most important corrective to a naive reading of Analects 13.18, and it is now the
backbone of the `family_vs_public_justice` tradeoff.

**Mengzi 5A.3 belongs alongside it and the report omits it.** Shun's brother Xiang repeatedly
tried to kill him; Shun enfeoffs rather than punishes him — but Mencius adds that an officer
administered the state and Xiang "could do nothing in his State… How indeed could he be allowed
the means of oppressing the people?" Affection for the wrongdoer is preserved; power over
others is withheld. That is a precise model for the compassion/accountability tradeoff and it
is now cited there.

**Analects 13.23 is correctly cited, contrary to first appearances.** Legge renders 和而不同 as
"The superior man is affable, but not adulatory" rather than with the word "harmony", so the
passage does not look like the harmony passage on an English keyword search. It is the right
one. Flagged here because a reviewer checking the reference file will hit the same confusion.

**The report's `4A17` and similar ids are unpunctuated.** The reference files use `Mengzi 4A.17`.
Cosmetic, but ids must match exactly for validation, so the dotted form is used throughout.

**Two errors of my own, found and fixed during checking.** I first cited Analects 17.19 for the
three-year mourning exchange; it is 17.21 (17.19 is "I would prefer not speaking"). And my first
excerpt of 12.19 quoted the wind-and-grass line without its context, which is Ji Kang asking
about *killing* the unprincipled — the context is most of the point. Both corrected. Recorded
because it shows the failure mode this file exists to catch.

**A genuine tension the report does not mention: Analects 4.18 versus Mengzi 4A.18.** The
Analects makes gentle remonstrance part of serving one's parents. Mengzi 4A.18 says that between
father and son "there should be no reproving admonitions to what is good. Such reproofs lead to
alienation, and than alienation there is nothing more inauspicious" — which is why, it argues,
the superior man does not teach his own son. The report treats remonstrance as settled. It is
not settled inside the family, and this is now the unresolved choice
`family_remonstrance_limits` with `generation_policy: mark_ambiguous`.

**Mengzi 7A.26 deserves a place the report does not give it.** Mencius attacks not only Yang Zhu's
egoism and Mo Di's impartial love but also Zi Mo's *correct middle position*, because he holds it
"without leaving room for the exigency of circumstances… It takes up one point and disregards a
hundred others." This is the tradition's own statement of why it is not a rule system, from
inside the text, and it now grounds CM09 and CM16.

**One qualification the report's "differentiated care" section needs.** Mengzi 7A.45 states the
gradation explicitly — kind to creatures, loving to people generally, affectionate to parents —
and 3A.5 argues against the Mohist that love without degrees misdescribes how concern actually
arises. Both are now cited, so the graded-concern claim rests on text rather than on the
report's summary.

**The report's claim that 2A.6 shows people "can react with immediate concern" is right but the
passage says more.** Its last clause is that the four beginnings, denied development, "will not
suffice for a man to serve his parents with." That is a much weaker claim about actual human
behaviour than "human nature is good" suggests, and it is why the spec's summary describes
beginnings requiring cultivation rather than reliable moral responsiveness.

---

## 2. Interpretation choices left open on purpose

Six are recorded in `spec.yaml` under `unresolved_choices` with a working assumption and a
generation policy. The two that most affect data generation:

- **`analects_13_18`** (policy: `use_working_assumption`). Confucius states no limit on mutual
  concealment. The working assumption instantiates it only for minor, private, non-continuing
  wrongdoing and lets 7A.35 govern anything serious. This is a decision, not a finding, and it
  is the one a human reviewer should look at first.
- **`family_remonstrance_limits`** (policy: `mark_ambiguous`). The generator must show the
  tension rather than resolve it.

Two tradeoffs are marked `unresolved: true`, meaning the pilot must not produce a confident
resolution:

- **`immediate_feeling_vs_reflective_correction`**. 2A.6 treats the immediate response to a
  child at a well as revealing something real; 6A.15 has the thinking mind govern the senses,
  which are "obscured by external things"; 6A.8 has conditions destroy the response entirely.
  The corpus does not say when a first reaction should be trusted.
- **`scope_of_kinship_claims_on_scarce_resources`**. Graded concern is affirmed and impartial
  equality rejected, but nothing in the sources gives a rate of exchange between a strong near
  claim and an acute distant one.

I did *not* leave open whether family loyalty may obstruct accountability for serious harm.
7A.35 and 5A.3 settle that clearly enough to lean on, and leaving it open would have produced
scenarios that model concealment as a live option.

---

## 3. Where the sources are uncomfortable, and what was done about it

The texts assume a hierarchical, patriarchal, non-egalitarian order, and this is not incidental.
Mengzi 3B.2 quotes as ritual instruction that a bride must "be respectful… be careful. Do not
disobey your husband," and glosses compliance as "the rule for women" — the passage's actual
point is a contrast with what makes a great man, but the norm is stated approvingly as
background. Mengzi 5A.2 has Shun's parents and brother repeatedly try to murder him, and
presents his continued warmth toward them as admirable.

Two decisions follow.

1. **The target takes the structure of judgment, not the social assumptions.** Role
   differentiation is kept; age, sex, birth and office as grounds of *moral authority* are not.
   This is stated in `spec.yaml`'s summary and in the `hierarchy_modernisation` unresolved
   choice, not buried.
2. **Modern constraints are labelled modern.** Anti-discrimination, safeguarding, informed
   consent, confidentiality and equal legal standing govern every response and are never
   attributed to Confucius or Mencius. There is a boundary entry saying exactly this. The
   report's section 22.4.H asked for this and it is implemented.

Concretely: **Mengzi 5A.2 must not be used to model responses to abuse.** A generator that reads
"his parents tried to kill him and he remained devoted" as a template will produce advice that
keeps people in danger. `key_passages.md` says so at the passage.

---

## 4. Consolidation of the report's 20 candidate principles into 16

| spec | from report |
|---|---|
| CM01 Humane concern | CM01 |
| CM02 Rightness before advantage | CM02 |
| CM03 Differentiated relational responsibility | CM03 + CM05 merged — the sources do not separate having role obligations from their being graded |
| CM04 Moral extension | CM04 |
| CM05 Reciprocal perspective-taking | CM06 |
| CM06 Respectful correction | CM07 |
| CM07 Harmony without sameness | CM08 |
| CM08 Meaningful form and sincere affect | CM09 + CM12 merged — 3.4 and 3.26 make these one point |
| CM09 Weighing exceptional circumstances | CM10, generalised from "emergency override" to weighing, per 7A.26 |
| CM10 Trustworthiness | CM11 |
| CM11 Cultivation and learning from exemplars | CM13 + CM14 merged |
| CM12 Moral discrimination and epistemic honesty | CM15 + CM16 merged |
| CM13 Shame and self-respect | CM17 |
| CM14 Conditions of good conduct | CM18, reframed from "humane governance" so it applies to workplaces and schools, not only states |
| CM15 Conditional authority | CM19 |
| CM16 Integrative judgment | CM20 |

Each has positive indicators and failure modes written to be checkable by a reviewer reading a
single response, not to be read as doctrine.

---

## 5. Implications for the pipeline

**Scenarios need relationship and role fields.** This target's judgments turn on facts a generic
"seed_situation" string will not reliably carry. The `Family` record should be able to record,
per scenario: the relationship between the parties, whether the user holds a public or fiduciary
role, harm severity, urgency, vulnerability, power asymmetry, and whether the domain is private
or role-neutral. Without these, `divergence` cases and `boundaries` cannot be generated
systematically, and the contrastive pairs below cannot be built at all. The report's §18.2
schema is the right instinct; the minimum useful subset is
`{relationship, role_type, harm_severity, urgency, public_or_private}`.

**Contrastive pairs are the highest-value scenario shape, and the pipeline should support them
explicitly.** Almost every principle here is defined by where it *stops*. A single scenario
cannot show that; two scenarios differing in exactly one feature can. The obvious pairs: minor
versus serious family wrongdoing; a personal favour versus the same favour inside a hiring
decision; a social norm versus the same norm with a life at stake; a disagreement versus the
same disagreement with a humiliation attached. This wants either a `paired_with` field on
`Family` or a convention that a family may hold two prompts that differ in one stated variable.
Note that this cuts against naive dedupe: a good contrastive pair is *deliberately* near-duplicate
in surface form, and a cosine threshold of 0.92 over prompts will delete exactly the examples
that carry the most signal. Dedupe should run within-family or skip paired families.

**The cue-term check needs care with single-syllable romanisations.** `li`, `yi`, `de`, `zhi`
and `he` collide with ordinary English words and names and are deliberately excluded from
`forbidden_terms`; the list is otherwise safe for a word-boundary regex. The reviewer prompt
should check for them semantically instead. Also worth flagging as leakage: "the superior man",
"the Master said", and the tell-tale construction "as the ancients would say" — the first two
are in the list.

**Divergence judging should look at reasons, not only actions.** Several divergence hypotheses
(`conditions_before_blame`, `manner_as_substance`, `rightness_governs_commitment`) predict that
the target and a generic assistant reach a similar action for visibly different reasons. The
`DivergenceVerdict.kind` field already allows `reasons`, and the judge prompt should be written
so that a reasons-only divergence counts, otherwise these cases will be scored as non-divergent
and dropped.

**Reviewer red flags specific to this target**, worth putting directly in the review prompt:
confident resolution of an `unresolved: true` tradeoff; giving the same answer when severity,
urgency, role or vulnerability changes; treating rank as evidence; excusing serious harm because
the wrongdoer is a relative; avoiding a needed criticism; attributing a modern constraint to the
tradition; and translation collapse (humaneness = kindness, rightness = justice, propriety =
etiquette, filiality = obedience). The last is the reason the spec's principle names avoid the
Legge vocabulary.

**Legge's register is a real cost.** The only complete public-domain English is Victorian, and
"superior man" and "perfect virtue" will bleed into generated text if the prompt does not
actively push against it. `key_passages.md` opens with an instruction to treat the diction as a
pointer rather than a register. This should be reinforced in the response-generation prompt, and
it is worth an explicit check in review.

**Layers are worth using here.** `core` and `mencian` are not decorative: the Mencian material
(extension, conditions of conduct, conditional authority, shame) is where most of the divergence
from a generic assistant lives, while the Analects material is closer to ordinary good advice.
If the pilot generates only `core`, expect a low divergence rate.
