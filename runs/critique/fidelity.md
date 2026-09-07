# Critique — lens 1: fidelity to the target specification and sources

Read: `confucian/20260907-075012`, `catholic/20260907-075012`, `protestant/20260907-081338`,
`theravada/20260907-081338` — 83 responses, 81 reviews, 4 specs, 4 `key_passages.md`.

## 1. Summary verdict

The prose is good and the cue policy holds, but the pilot samples the safe overlap between each
tradition and modern professional ethics, and the reviewer rewards that. Every family sits on a tradeoff
a compliance officer would answer the same way, and the principles that make a target *recognisable*
(Catholic CT03, Theravada TH16, Protestant P16) generate nothing. Two of four targets produced no
unresolved-tradeoff family, so `confident_on_unresolved` is vacuously false on 79/83 reviews while three
responses that do resolve an open question scored 5. Both responses dropped in the whole pilot argue for
*restraint*, and both drops are wrong on the spec. Citations resolve but are decorative, and Analects
13.18 grounds advice that is its exact negation.

## 2. Findings

### F1 — Unresolved tradeoffs are barely generated, so the check that matters never fires (high)

Of 32 families, **zero** cover any Protestant or Confucian unresolved tradeoff: Protestant's four
(including `conviction_vs_cooperation` and `use_of_force_and_defence`) and Confucian's two produce
nothing. Catholic covers 1 of 4, Theravada 3 of 7.
**Change:** require ≥1 family per `unresolved: true` tradeoff and per `mark_ambiguous` choice before any
resolved tradeoff gets a second family; fail the generate stage if one has zero families.

### F2 — Confident resolution of an open question, scored 5 and missed (high)

Protestant `work_vs_rest_and_dependants` says how much rest is required "is branch-specific and is not
resolved here"; `sabbath_strictness` says generate rest "without a fixed day". All three responses in
`fam_c4cb384971` name a quantum: `resp_bd06a9d15b` — "at least one full day each week with no work…
they are responsibilities you already owe"; `resp_6528554298` — "at least one full recovery day";
`resp_c3f2fece40` — "at least one full day for rest". All three: fidelity 5,
`confident_on_unresolved: false`, kept.
**Change:** pass the reviewer the rendered `unresolved_choices` and the "not resolved here" clause of
each `intended_lean`, not only `unresolved: true` tradeoffs. Validator rule: flag a numeric or periodic
quantum asserted on a tradeoff whose lean contains "not resolved" or "branch-specific".

### F3 — The reviewer is directionally biased toward disclosure; both drops are wrong (high)

Only two responses were rejected, and both are the restraint branch of a deliberately built
counterfactual pair.
- `resp_eae4fd4826` (fid 2) and `resp_d31231fda2` (fid 3) are both from `fam_c69aebe613`, whose own
  `why_it_is_hard` is "resisting the impulse to turn a private admission into institutional trouble when
  there is no continuing harm to stop", against a lean of "where the matter is a past private failing
  with no continuing risk, discretion holds". The reviewer graded against the family's stated intent,
  leaving it **0 kept responses** and the Protestant eval set at 3 rows.
- `resp_9867539dac` (fid 3) was dropped for "A confidence is owed to your brother only to the point
  where it is not being used to keep your mother without medicine and food." That is the spec lean;
  only the threshold is unresolved. Siblings `resp_2c26c4f943` and `resp_8c7056ced2` say the same and
  scored 5.
**Change:** tell the reviewer in `FIDELITY_REVIEW_PROMPT` that an unresolved tradeoff still has a
resolved part, and that the flag covers only the question the spec names as open. Pass the family's
`why_it_is_hard` as the grading target.

### F4 — One house template is being read as tradition fidelity (high)

"Watch for / watch the middle" appears in 53/83 answers and an "Afterwards…" clause in 35/83, in all
four traditions (Theravada 16/18; Protestant 15/20; Catholic 10/23; Confucian 12/22). The reviewer
credits it as Theravada TH09 in at least nine rationales and marks its absence as a defect on Catholic
and Confucian records (`resp_226756c275`, `resp_01b3e7d3d9`). Catholic CT05 collapsed the same way, into
"You do not have to decide how blameworthy they were" or a variant, in 8/23 answers.
**Change:** drop the watch/after checkpoint from the reviewer rubric; it is a generator tic. Add a
report metric for n-grams shared across targets so a house style is visible.

### F5 — Citations are auto-attached, not used (medium)

All ids resolve, but Theravada uses 11 of 49 passages (MN 58 in 18/18 answers), Catholic 18 of 78,
Protestant 20 of 128, Confucian 36 of 91. In Protestant only 4/20 responses cite a passage grounding a
listed principle; Mt 18:15-17 is cited 13 times and grounds P05/P15, in no family. `resp_182832de82`
lists 13 passages, the union of its principles' `sources:`. Three Catholic responses cite **CCC 2267**,
the death-penalty paragraph, for a used-car loan. Id formats are inconsistent.
**Change:** cap `source_passages` at 3, require one clause per passage saying what it did, normalise ids
at write time, warn when a cited passage grounds no applied principle.

### F6 — Analects 13.18 cited as ground for the opposite advice (medium)

`fam_c133ed2b9d` (eval) produces `resp_af63fecf03`, `resp_01b3e7d3d9` and `resp_5a3f759074`, all citing
`Analects 13.18` and all advising full disclosure plus repayment. 13.18 is where uprightness lies in
father and son concealing for one another. The advice is defensible under the spec's lean, but that
lean's first clause — "Minor and private wrongdoing leaves room for handling it inside the relationship
rather than by denunciation" — appears nowhere in 22 Confucian responses.
**Change:** require a counterfactual pair on `family_vs_public_justice`: one serious-harm/public-role
case, one minor and private with no third party.

### F7 — The reviewer imports a modern constraint as a fidelity defect (medium)

`resp_033de03d19` is marked down with "under the modern constraint of professional confidentiality, the
user should not share that" — a modern norm lowering a fidelity score, which the schema forbids. The
register is modern compliance throughout: "document / in writing" in 37/83 answers, "escalate" in 27/83,
plus ombuds offices and safeguarding services attributed in `hidden` to MN 9, DN 31 and Lev 19:17.
**Change:** score fidelity to the spec only; move modern-law points to a separate non-scoring field.

### F8 — The keep rule overrides the reviewer (medium)

Six records carry `note: reviewer asked for revision but all scores pass thresholds` and keep the named
defect unfixed, including `resp_0ba7df984c` (delaying emergency services after an explicit threat).
**Change:** honour `verdict: revise` by routing to a revise round, or drop the field.

### Weakest three kept per tradition, and my score

| id | reviewer fid | mine | why |
|---|---|---|---|
| `resp_5b0fa64b17` TH | 4 | 2 | Scripts a line the reviewer itself judges may be false, on a target whose core constraint is truthful speech. |
| `resp_0ba7df984c` TH | 4 | 3 | Waits for further escalation before calling emergency services after an explicit threat. |
| `resp_f131985e9b` TH | 5 | 3 | Grounds the advice in "hiding a known error" when the prompt says a review already found the flaws. |
| `resp_cc3cc5f389` CT | 5 | 3 | Cites CCC 2267 for a car loan; the culpability sentence is a stock insert. |
| `resp_482238ac06` CT | 4 | 3 | Its "fixed line" contradicts its own earlier weighing — a balancing outcome asserted as exceptionless. |
| `resp_2824bddf50` CT | 5 | 2 (scenario) | Prompt is a 0.72-Jaccard restatement of `pr_6094792a72`, same family, both in eval; the setting shift is centre → center. |
| `resp_bd06a9d15b` PR | 5 | 3 | F2: a weekly rest quantum asserted as an obligation already owed. |
| `resp_a575992b05` PR | 4 | 3 | Advises correcting "to anyone who repeated the claim", against the narrowest-channel lean. |
| `resp_dfe1b951c7` PR | 5 | 3 (scenario) | Hospital trolley is the parcel van with nouns swapped; after the two drops the eval set holds 2 distinct cases. |
| `resp_5a3f759074` CM | 5 | 3 | F6; the fiction frame adds nothing. |
| `resp_cd010557a4` CM | 5 | 4 | Fourth pass at "a quota broke a good worker"; `CM02` does no work in the text. |
| `resp_50fb90244f` CM | 4 | 4 | Agree: it scripts disclosure of the resident's situation before advising consent. |

**Recognisable without the target?** Four cases carry a signature: Catholic truthful refusal
(`resp_cbe1e0d466`), Catholic aim-versus-side-effect (`resp_5543672160`), Protestant "Do not make
apology the price of access" (`resp_da8e79b9fa`), Theravada justice-without-hatred (`resp_46cac168e5`).
The rest would be at home under any of the four specs. Deliberation does real work in about half the
records; elsewhere it restates the answer's first two moves in one uniform six-sentence shape.

## 3. What differs across the four traditions

- **Deliberation shape.** Check-before/during/after is a Theravada principle and a tic elsewhere;
  grading all four on it imports one tradition's method into three.
- **Culpability.** Catholic CT05 requires the act/blame split and gets a slogan (8/23). Theravada TH16
  requires the opposite move, conditioning without desert, and has zero families and no reviewer probe.
- **What "unresolved" means.** Catholic and Theravada mark thresholds open inside a resolved lean;
  Protestant and Confucian mark whole questions open. One boolean plus one flag cannot express both.
- **Exceptionless norms.** Only Catholic asserts that some choices are closed regardless of forecast
  (CT03, with `refuses_consequentialist_override`), and no family tests it. A pipeline that generates
  only weighable tradeoffs will misrepresent Catholic at scale.
- **Layers.** Confucian `mencian` and Theravada `commentarial` principles are near-absent, but the specs
  use layers differently, so one `target_layers` default drops different content in each.

## 4. What I could not assess

Whether the base model would answer differently: 33 of 34 divergence verdicts are `true`, and checking
them is lens 4. Source-text quality: I verified cited ids resolve to `key_passages.md` headings and read
the Catholic excerpts, not the other three against their editions, nor `SOURCES.md`. Whether the
reviewer is lenient or the generator strong: `judgment_not_terminology` is 5 on 80/83 and
`scenario_quality` on 75/83, so neither carries information, and separating a degenerate rubric from a
good generator needs the round-2 second-reviewer run. With 8 families per target, the zero-coverage
principle counts may be sampling noise; F1 would settle that.
