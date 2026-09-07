# Research notes — Theravāda target

What was checked against sources, what changed, what was left open, and what the pipeline needs to
do differently as a result. Written against `theravada_buddhist_ethical_and_practical_thought.md`
(the research report). Work done 7 September 2026.

Method note: the report cites SuttaCentral for almost every canonical claim. Because SuttaCentral
asks that its content not be used for generative-AI datasets (see `SOURCES.md` §1), every claim was
re-verified against a different permitted copy of the same text — a public-domain print translation,
a CC BY-NC or CC BY-SA translation, or the public-domain Pāli — rather than against SuttaCentral.

---

## 1. Verified

- **MN 9** classifies conduct as unwholesome and names greed, hate and delusion as its roots, with
  the wholesome roots as their absence. Chalmers (1926): *"its roots are — greed, hate and delusion"*;
  Pāli *lobho akusalamūlaṃ, doso akusalamūlaṃ, moho akusalamūlaṃ*.
- **MN 19** contains the habit principle. Thanissaro: *"Whatever a monk keeps pursuing with his
  thinking & pondering, that becomes the inclination of his awareness."* Pāli confirms
  *bahulamanuvitakketi anuvicāreti tathā tathā nati hoti cetaso*. The four-part fault test —
  affliction of self, of others, of both, and obstruction of discernment — is also as described.
- **MN 61** has the before / during / after structure, an explicit stop rule mid-action, and
  disclosure plus future restraint afterwards. Pāli *paccavekkhitvā paccavekkhitvā*.
- **AN 6.63** contains *"Intention, I tell you, is kamma"* — *Cetanāhaṃ bhikkhave kammaṃ vadāmi*.
- **AN 3.100** is the salt-crystal discourse and does undermine one-act-one-fixed-result accounting;
  the differentiating variable is the agent's development in body, virtue, mind and discernment.
- **AN 3.65** gives the four tests, including *"criticized by the wise"*, and is not an endorsement of
  private intuition. Pāli *mā anussavena, mā paramparāya…*
- **DN 16** carries the virtue → collectedness → wisdom → release refrain, repeated at several stops.
  Pāli *iti sīlaṃ, iti samādhi, iti paññā*.
- **DN 26** has the poverty → theft → punishment → armed violence sequence, and it begins from a
  king who "did provide the due watch and ward and protection, but on the destitute he bestowed no
  wealth." Pāli *No ca kho adhanānaṃ dhanamanuppādāsi… dāḷiddiyaṃ vepullamagamāsi*.
- **DN 31** employer duties are exactly the five the report lists: work according to strength, food
  and wages, care in sickness, sharing unusual delicacies, leave at times. Pāli *yathābalaṃ
  kammantasaṃvidhānena, bhattavetanānuppadānena, gilānupaṭṭhānena, acchariyānaṃ rasānaṃ saṃvibhāgena,
  samaye vossaggena*.
- **MN 117** distinguishes right view with effluents from noble right view, and the mundane form
  explicitly includes *atthi ayaṃ loko, atthi paro loko… atthi sattā opapātikā*. The report's claim
  that this makes the naturalising choice substantive rather than cosmetic is correct.
- **MN 44** groups the eight factors under the three trainings, in the direction the report states.
- **SN 42.3** condemns the warrior's state as *"already seized, debased, & misdirected"* by the
  intention that the enemy be destroyed.
- **MN 21** sets the simile-of-the-saw standard, in a public-domain translation.
- **Visuddhimagga IX.98-101** gives the near and far enemies as the report describes, for
  loving-kindness, compassion and equanimity.
- **The Journal of Buddhist Ethics articles all exist.** Gethin, "Can Killing a Living Being Ever Be
  an Act of Compassion?", vol. 11 (2004). Keown, "On Compassionate Killing and the Abhidhamma's
  'Psychological Ethics'", vol. 23 (2016). And — the claim most worth checking — **the 2026
  Karunanayaka article is real**: "Beyond 'Mixed Motives': Cetasika Micro-Dynamics and Theravāda
  Moral Dilemmas", *Journal of Buddhist Ethics* vol. 33, posted 18 May 2026, by Indrajith P.
  Karunanayaka, Independent Researcher. Its abstract says compassion and the intention to deceive
  "cannot blend into a single mixed state", which is what the report claims.
- **SuttaCentral's AI request exists and is current**, in the wording quoted in `SOURCES.md`.
- **ancient-buddhist-texts.net is CC BY-SA 3.0**, as the report says, with named third-party
  exceptions that were avoided.
- **SLTP Pāli is public domain**, as the report says.

---

## 2. Corrected

**MN 58 is a six-case analysis over three dimensions, not a "four-way" one.** The report lists four
criteria: true/false, beneficial/harmful, pleasing/displeasing, timely/untimely. The discourse has
three binary tests — factual, beneficial, welcome — yielding six enumerated cases, and *timeliness is
not a fourth test of whether to speak*. It is a constraint on when, and the Pāli attaches *kālaññū*
to exactly two cases: true-and-beneficial-and-unwelcome, and true-and-beneficial-and-welcome. Two
consequences the report misses. First, timing applies even to welcome truths. Second, case [5] —
true, useless, pleasant — is left unsaid, which means the discourse forbids a class of harmless
pleasant remarks that a generic assistant would produce freely. Both are now in TH03.

**The child-and-the-object example runs the other way.** The report says "Prince Abhaya proposes a
case where an adult might remove a dangerous object from a child's mouth". The Buddha proposes it,
having noticed the baby on the prince's lap, and Abhaya answers that he would remove a stick or
piece of gravel *"even if it meant drawing blood… Because I have sympathy for the young boy."* The
correction matters because the point is not that a bystander offered a rationalisation; it is that
the Buddha elicited the principle from the prince's own conduct.

**MN 117's own account of wrong livelihood is not about trade categories.** The report cites MN 117
for right livelihood and AN 5.177 for harmful trades, which is accurate as far as it goes, but does
not say what MN 117 actually contains: *"Scheming, persuading, hinting, belittling, & pursuing gain
with gain."* That is about obtaining advantage through manipulation, and it lands far more directly
on persuasion design, dark patterns and engagement extraction than the five-trades list does. TH15
now leads with it.

**The near-enemy table omits sympathetic joy.** The report's table covers loving-kindness, compassion
and equanimity. Buddhaghosa gives all four: gladness has household-based joy as its near enemy and
boredom or aversion as its far enemy. Restored in `key_passages.md`.

**MN 61's after-clause is asymmetric.** The report says "harmful bodily and verbal conduct afterward
is to be disclosed". Correct, and the omission matters: for *mental* action the instruction is not
disclosure but to feel distressed and ashamed and then to exercise restraint. So the repair sequence
is not "confess everything"; disclosure is owed where an act affected someone. This is now explicit
in TH13, and it is what stops the target from generating indiscriminate self-exposure advice.

**AN 3.100 does not support a naturalised reading.** The report uses the salt-crystal discourse to
argue against mechanical karmic bookkeeping, which it does. But the discourse makes that point
entirely inside the rebirth frame — the trifling deed "takes him to hell". Citing it as evidence that
the tradition is really about psychological conditioning would be a misuse. Noted at the passage.

**Dhammapada 201 is not word-for-word "Victory breeds enmity".** The Pāli *jayaṃ veraṃ pasavati*
supports either rendering; Ānandajoti has "The victor generates hatred". Not an error, but the
report presents a translator's phrasing as if it were the text.

**The report's licensing table understates two problems.** It lists Access to Insight as "inspect
each item's rights" without noting that the Buddhist Publication Society items there (MN 9, DN 31)
carry a free-distribution licence whose derivative-work conditions are awkward for model training,
and it does not flag that CC BY-NC and CC BY-SA material cannot be combined into one redistributable
work. Both are now in `SOURCES.md` §4.

---

## 3. Not verified

- **DN 26's later sections** beyond the poverty sequence were not read closely; only §§10-16 were
  extracted and checked.
- **The Vinaya third pārājika analysis** the report describes was not independently verified; no
  Vinaya source was acquired. It is not cited anywhere in `spec.yaml`.
- **Abhidhamma primary sources** (Dhammasaṅgaṇī, Atthasālinī, Abhidhammatthasaṅgaha) were not
  acquired. The commentarial layer in this target rests on one Visuddhimagga passage, verified
  through a copyrighted translation and paraphrased from the Pāli.
- **The modern scholarship characterisations** (Heim, Keown, Harvey, Hallisey, Crosby, Braun, Sharf,
  McMahan) were not checked against the books. Only the three Journal of Buddhist Ethics abstracts
  were read. The spec does not rest on any of the book claims.
- **MN 7 and MN 52** on the divine abidings, cited by the report, were not acquired.
- **OCR fidelity.** The four public-domain files are uncorrected optical character recognition. Every
  passage quoted from them was read in context, but the files as wholes contain errors.
- **SLTP transcription.** Cross-checked against English translations only, not against a printed
  critical edition, exactly as the SLTP project itself advises against relying on.

---

## 4. Choices deliberately left open

The four the lead directed, plus four more that emerged:

1. **Naturalisation (Configuration B).** Adopted as the pilot's working assumption and recorded in
   `spec.yaml` as a *fidelity cost*, not a wording choice. MN 117 is the passage that makes this
   substantive: canonical ordinary right view names the other world and spontaneously reborn beings
   explicitly. The cosmological material is preserved in the spec and the references rather than
   deleted, so a Configuration A run is possible later without re-acquiring anything. The nearest
   canonical support for the naturalised reading is AN 3.65's second assurance, and it is offered as
   one of four, not as a substitute.
2. **Compassionate killing** — `mark_ambiguous`. Gethin and Keown disagree in print and the pilot
   should not silently pick one.
3. **Protective deception** — `mark_ambiguous`. Same, with the 2026 article as a recent proposal
   rather than a resolution.
4. **Livelihood causal threshold** — `mark_ambiguous`. AN 5.177 gives five flat categories and no
   theory of degrees.
5. **Abortion** — `avoid`. No source acquired, and translating monastic law into lay ethics is an
   interpretive act the pilot should not make unsupervised.
6. **Coercive political action** — the structural-causes principle is confident; what to do about it
   politically is not.
7. **Commentarial authority.** The near-enemy analysis is admitted; the stronger Abhidhamma claim
   that particular mental factors are mutually incompatible is not treated as settling anything.
8. **Licence combination.** Whether a published dataset may mix CC BY-NC 4.0 and CC BY-SA 3.0 text is
   flagged in `SOURCES.md` §4 for a human, not decided here.

---

## 5. Implications for the pipeline

These are requests to the implementation, in rough order of how much they change existing plans.

**Responses need an internal before / during / after shape for action-advice cases.** Not as a visible
template — that would be a cue — but the deliberation field should forecast the affliction, name what
evidence would mean stop, and say what review comes after. Suggest the response generation prompt
require this for any family whose seed situation involves the user taking an action, and that the
reviewer check for the missing middle checkpoint specifically. It is the one most likely to be dropped.

**The scenario schema needs the asker's own state as a variable.** TH02 and several divergence
hypotheses turn on it. `Family` should carry something like `asker_state:
{compulsion|aversion|status_defence|fear|confusion|none|unstated}` so the generator can vary it
while holding the situation fixed, and so the counterfactual-pair construction below has an axis to
move along. Without this the target's most distinctive behaviour cannot be generated on purpose.

**Counterfactual pairs are the right unit for this target and should be first-class.** The report's
suggestion is sound and this target makes it sharper: pairs that hold the situation fixed and vary
exactly one of act type, state acted from, foreseeable affliction, habit effect, or identity
investment. Suggest `Family` gain an optional `pair_id` and `varied_factor`, and that export keep
pairs in the same split. This trains factor sensitivity instead of lexical association, which is the
whole point of a target whose vocabulary is forbidden.

**The cue-term check needs three behaviours the current regex plan does not have.** (a) Whole-token
matching, so "mindfulness" fires but "mindful" does not, and "monk" does not fire on "monkey".
(b) Multi-word phrase matching for the eightfold-path factor names, whose component words are
ordinary. (c) A deliberate allow-list: `craving`, `attachment`, `suffering`, `compassion`,
`equanimity` and `intention` must NOT be flagged, because TH05 and TH07 require the model to draw
distinctions using exactly those words. The reasoning is in `cue_policy.notes`.

**One check the cue list cannot do.** No SuttaCentral-derived text may enter the pipeline, including
via the generator model's own recall of modern translations. Suggest the reviewer prompt include:
if the response quotes scripture-sounding phrasing that matches nothing in `references/`, flag it.
This is a licensing control, not a quality control.

**`unresolved: true` needs to survive into the reviewer's rubric as a scored dimension, not just a
flag.** Seven of thirteen tradeoffs here are unresolved, which is a high proportion, and the
characteristic failure of a strong generator model is a fluent, balanced, *conclusive* answer. The
`confident_on_unresolved` boolean in the planned `Review` record is the right hook; it needs a
positive counterpart too, because a response that presents the conflict honestly and still gives
concrete help with the decidable parts is the target behaviour, and a response that just refuses is
not.

**Divergence judging should be able to return "same action, different reasons".** Several hypotheses
here — conditioning-without-desert, judged-as-a-pattern, useless-truth-withheld — predict that the
target and the base model recommend similar actions for visibly different reasons, or that the target
adds a consideration rather than reversing the conclusion. The planned `DivergenceVerdict.kind` field
already has `reasons`; make sure the judge prompt actively looks for it rather than defaulting to
`none` when the actions match.

**Non-commercial provenance must reach the manifest.** Twelve of twenty grounding files are CC BY-NC
4.0. `manifest.json` should carry a `license_constraints` field derived from `reference_material`, so
that anyone who picks up the trained adapter later can see the restriction without reading this
directory.

**Domain weights assume modern secular settings.** Every domain in `spec.yaml` is deliberately
era-neutral and none references a religious context. If the generator starts producing scenarios set
in temples, retreats or communities of practitioners, that is a cue leak in scenario construction
rather than in wording, and the cue-term check will not catch it. Worth one line in the family
generation prompt.
