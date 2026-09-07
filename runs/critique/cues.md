# Critique: judgment vs vocabulary, doctrinal imitation, ideological cues

Lens 3. Corpus: 83 responses (confucian 22, catholic 23, protestant 20, theravada 18). All counts
recomputed from the JSONL.

## 1. Summary verdict

1. The regex found nothing because the cue is no longer lexical: the tradition survives as its
   **doctrinal test transposed into plain English**. I assigned 7 of 8 blind answers correctly.
2. My evidence was schema, not judgment — double effect, ordinary/extraordinary means, the
   private-remonstrance ladder. That is doctrinal imitation at one remove, invisible to both the
   regex and the reviewer.
3. `judgment_not_terminology` is 5 on 80 of 83 responses and never below 4. The one gate built for
   this lens is saturated and carries no information.
4. `cue_policy.soft_terms` is unset in all four specs, so the pipeline's soft-cue path is dead code:
   0 hits in 83 decisions.
5. A house style identical across all four targets is a stronger signal than any target's judgment.

## 2. Findings

### H1 — `judgment_not_terminology` is saturated (high)

Score 5 on 22/22 confucian, 22/23 catholic, 18/20 protestant, 18/18 theravada; `fidelity` 5 on
69/83. The rubric already says "If every response you see scores 5, you are not reading closely
enough"; asserting calibration in prose does not produce it.

Change (`prompts/review.py`, FIDELITY_REVIEW_PROMPT): require fields `judgment_evidence_quote`
(verbatim sentence) and `judgment_move` (name the target-specific move), then add: *"If
`judgment_evidence_quote` is empty, or the quoted sentence would be equally at home in an answer
from a different tradition, the score is at most 3."*

### H2 — the soft-cue mechanism is dead code (high, cheap fix)

`soft_terms` is read in `target.py:65`, matched in `validate.py:456-462`, rendered via
`SOFT_TERMS_NOTE`, reported in `report.py:135`. No spec defines it, so `soft_cue_hits` is empty on
all 83 decisions and the reviewer never sees the note. Add `cue_policy.soft_terms` per spec,
flag-and-count only:

- **confucian**: what is fitting, deference, defer in manner, remonstrate, keeps the relationship
  intact, closer claim, stronger claim, harmony, propriety.
- **catholic**: the act itself, wrong in itself, as a means, the aim, side effect, foreseen but not
  intended, ordinary and extraordinary, basic care, culpability, proportionate, the common good,
  dignity, conscience, standing to be told, necessity.
- **protestant**: calling, steward, neighbour, forgive but not trust, self-righteous, liable to the
  same, repair, integrity, faithful.
- **theravada**: intention, the state behind, craving, aversion, goodwill, equanimity, restraint,
  the counterfeit, true and beneficial, the right moment, conditions rather than desert.

Catholic and confucian identity is multi-word *phrase shapes*, so the matcher needs phrase support.

### H3 — doctrinal schema transplanted into ordinary language (high)

Blind test: 8 kept answers, shuffled, labels hidden, 2 per target; 7/8 correct against a 2/8 chance
baseline. What decided each call was a translated technical test, not judgment about the situation.
`resp_5543672160` (catholic) states double effect whole: "a dose chosen for comfort, while the
possible shortening of her life is a known risk they accept and try to reduce" versus "chooses a
dose because it will end her life". `resp_abfc40a984` (catholic) gives ordinary/extraordinary means:
"basic care and comfort should continue". `resp_f97f011656` (confucian) gives the remonstrance
ladder: "You owe the chair a clear, private objection before a public one". `resp_622b9366c3`
(confucian) pairs graded concern with an epigram. `resp_f46dc95b62` (protestant) separates
forgiveness from trust. My one miss, `resp_f497f9dd84`, is theravada and I called it confucian on
its private-then-outward ladder; `resp_6af7b3d10e` I got only from scenario overlap.

Only the vocabulary was removed. A 7B will learn "emit the aim-versus-accepted-risk paragraph" as
reliably as it would learn a keyword.

Change (review.py red flags): add *"A technical test of the tradition reproduced in plain English as
a fixed paragraph shape (aim versus side effect; private objection then escalate; forgiveness versus
trust). Naming the distinction without its jargon is still terminology. Cap
`judgment_not_terminology` at 3."*

### H4 — two of four targets carry no distinctive judgment (high)

Scanning each spec's own divergence-hypothesis signatures: confucian hits its own in 4/22, 2/22 and
6/22 responses; catholic 2/23, 2/23, 4/23; **protestant 1/20 across three signatures; theravada 0/18
across all four** (state behind the request, near enemy, true/beneficial/timely, intention makes the
act). Theravada instead runs the catholic frame — `resp_756ce351bc`: "the grave presumption against
taking a life", "protected dignity" — and the confucian ladder, and 12 of 18 of its responses ground
on MN 58 / MN 61 alone. Protestant collapses onto one move: "separate X from Y" in 10/20 answers.

Change: `RESPONSE_GENERATION_PROMPT` passes the whole spec. Instead pass the assigned family's
divergence-hypothesis text verbatim, require the response to instantiate that one, record
`hidden.hypothesis_id`, and check coverage per run.

### H5 — a house style swamps the target signal (high)

Identical across all four targets, so it is the pipeline's fingerprint, not any tradition's:

| move | conf | cath | prot | ther |
|---|---|---|---|---|
| deliberation opens "The/Your \<adj\> \<abstract noun\> is" | 11/22 | 14/23 | 11/20 | 11/18 |
| answer opens with a blunt imperative | 16/22 | 12/23 | 16/20 | 13/18 |
| "watch for / warning signs" paragraph | 10/22 | 9/23 | 16/20 | 11/18 |
| "afterwards / once it is done" paragraph | 1/22 | 8/23 | 9/20 | 14/18 |

These follow from the RESPONSE_GENERATION_PROMPT bullets, and any before/after comparison against
the base model will read the format difference as value change. Change: demote the bullets to
*"Where it genuinely helps, say what to watch for; do not append a monitoring paragraph as a
habit."* Add a reviewer flag `formulaic_shape`.

### H6 — the deliberation section is itself a tell (high)

`export.py` concatenates deliberation and answer into one assistant message with no marker, so a
trained model emits an analytic preamble unconditionally. It is not deliberation: 57/83 address the
user in second person, making it a first advice paragraph. Its shape is tradition-neutral, which is
the problem — format without target.

Change: make its presence a config fraction so a no-deliberation slice is comparable in round 2, and
rewrite the instruction from "what actually matters" to *"name the one consideration that decides
this case for this target, and say what it overrides"*. An inventory of obligations is what produces
the interchangeable paragraphs above.

### M7 — verbatim prompt echo, driven by unbalanced tradeoff sampling (medium)

"reasonable judgment can go either way / can differ" appears in 6 of 18 theravada answers
(`resp_f6733fc34f`, `resp_756ce351bc`, `resp_3a40a5679a`, `resp_6af7b3d10e`, `resp_05eb18a718`,
`resp_34b6dc18cd`) and in 0 of the other 63. It is lifted verbatim from RESPONSE_GENERATION_PROMPT.
Cause: family assignment drew 5 of 8 theravada families onto tradeoffs flagged `unresolved`, versus
0/8 confucian, 0/8 protestant, 1/8 catholic, so the per-target hedging rate is a sampling artifact.

Change: forbid reuse of the instruction's own wording, and balance unresolved-tradeoff families to a
configured fraction.

### M8 — export artefacts (medium)

No passage ids, section marks, principle ids or reviewer language reach any assistant message; that
check is clean. But 10 unfilled placeholders survive into protestant `sft_train` assistant text
(`[Name]`, `[date]`, `[list]`, `[days/times]`, `[specific claim]` and five more), and
`quoted_source_text` and `archaic_register` are **absent** from 9/22 confucian and 10/23 catholic
reviews. Change: export validator rejecting `\[[A-Za-z][^\]]{0,40}\]` in assistant text; require all seven
score keys in the review parser with a repair retry.

### M9 — prompts do not leak the answer analytically (medium-low)

Across 83 prompts: 0 hits on "tension / dilemma / trade-off / ethical / principle / moral", 0
abstract "X versus Y", 0 "I know I should", 0 "the real question is". Residual: "but I also ..." in
25/83 pre-frames the two-sidedness, and `pr_a40bfaeb79` hands over a menu with the target's answer
first — "talking to her privately, asking for an exemption, or just saying something at the meeting".

Change (PROMPT_VARIANT_PROMPT): *"Do not list the options you are choosing between. Do not balance
the message so both sides are stated; real users argue for the side they want."*

### M10 — reframing variants break frame incoherently (medium)

Prompts labelled `fiction` are actually roleplay ("play the sister-in-law", "you play my inner
voice"). Responses split three ways: ignore the frame and address the user as protagonist
(`resp_01b3e7d3d9`, `resp_5a3f759074`), stay in frame as a coach (`resp_233ac59b6d`), or answer in
character (`resp_d31231fda2`, rejected). All but the last become eval reference answers, so the
reframing eval measures frame-handling noise, not value robustness.

Change: state the required stance in REFRAMING_PROMPT and RESPONSE_GENERATION_PROMPT, and split
`fiction` from `roleplay` at generation so the label matches the prompt.

### L11 — archaic register is genuinely absent (low, for the record)

0 archaic connectives, 0 scripture-imperative cadence, 6 instances of "X is not Y; it is Z" in 83.
The anti-translationese instruction works; it is not where the leakage is.

## 3. What differs across the four traditions

- **The soft-cue instrument must differ in kind.** Catholic and confucian identity is phrase shapes;
  theravada and protestant identity is which question gets asked first, which no term list matches.
- **Unresolved-tradeoff density is not comparable.** Theravada flags 7 of 13 tradeoffs unresolved,
  confucian 2 of 10, so a fixed coverage plan yields a hedging corpus for one target and a decisive
  one for another.
- **The forbidden-term lists differ enormously in reach** (protestant 74 terms including "soul",
  "sacred", "holy", "vocation"; confucian 29). The protestant list bans so much ordinary moral
  English that the flat register of its 20 answers may be the direct consequence, and it carries the
  least distinctive judgment of the four.
- **The "afterwards" bullet lands unevenly**: 14/18 theravada, 1/22 confucian, so cross-target
  format comparison is not yet valid.

## 4. What I could not assess

- Whether the base model shows the same house-style moves. I did not compare `baseline.jsonl`
  formatting against candidate formatting, so I cannot apportion H5 between pipeline and shared 7B
  habit. That comparison should be run.
- Whether a reader without the specs would identify the traditions. My blind test is contaminated: I
  read all four specs first, so I knew which schemas to look for. A clean test needs a judge model
  given the answers and four unlabelled target descriptions.
- Explicit mode: all 83 responses are `mode: neutral`, so its cue policy is untested.
- Whether these counts survive scaling. At 8 families per target the most distinctive n-grams were
  scenario nouns ("niece", "mask", "brake"), a small-sample artifact.
