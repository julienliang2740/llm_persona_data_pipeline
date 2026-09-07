# Round-2 critique — reviewer calibration, judgment vs vocabulary, house style

Lens: round-1 `fidelity.md` + `cues.md`. Corpus: 64 round-2 responses, 63 primary reviews, 64 second
reviews, 4 specs v0.2. Runs `catholic/20260907-191447`, `confucian/20260907-184558`,
`protestant/20260907-195133`, `theravada/20260907-202801`. All counts recomputed from JSONL.

## 1. Verdict

1. **Fixed:** the round-1 generator tics are gone — "watch for / warning signs" 52/83 → **1/64**; the
   rest-quantum-on-an-unresolved-tradeoff error (F2) does not recur; the divergence judge now works and
   correctly calls a candidate identical to the strong generic.
2. **Not fixed:** the reviewer is still not a filter. Across 64 responses and two reviewers, **zero
   rejections**; primary fidelity is 5 on 61/63 and `judgment_not_terminology` 5 on 61/63.
3. **Not fixed:** H3. The quotes that do discriminate discriminate by reproducing the tradition's
   technical test in plain English — the same failure, now with a citation attached.
4. **New problem:** one shared house style became four per-target templates copied verbatim from each
   spec's `deliberation_shape`. That is a stronger learnable cue than what it replaced.
5. **New problem:** `soft_terms` and `allowed_terms` overlap in 3 of 4 specs, so a response was dropped
   for a word its own spec permits.

## 2. Findings

### R1 — Neither reviewer rejects anything (high)

63 primary + 64 second reviews, verdict `accept` on **all 127**. The second reviewer (kimi-k3) uses only
{4,5} (two 3s in 189 scores) and 84 of its 88 disagreements are a uniform one-point drop; it is a
constant offset, not a discriminator, and would keep every row the primary kept. The whole round produced
4 drops: 2 on `formulaic_shape` (`resp_7239dc2185`, `resp_100aaf5fae`), 1 near-duplicate, 1 parse failure
(`resp_5a2cf25fb5`, "no reviewer verdict"). Protestant dropped 0 of 16.
**Change:** force a ranking inside the family. Every family holds exactly 2 responses; make the reviewer
pick the better and quote the sentence that decides it. That extracts signal from a saturated grader at
no generation cost.

### R2 — The evidence quote is honest but does not discriminate (high)

All 63 quotes are verbatim (the 6 apparent misses were dash and curly-quote normalisation). So the field
is not being fabricated. It is simply not selective. Of 20 read closely, ~7 carry a target-specific test:
`resp_928078abd7` "the plan runs through the false report", `resp_acb9a9d5e4`, `resp_2ceda1aaba` "right to
object … wrong to make the first challenge in front of the floor", `resp_92cbcf1c83`, `resp_6de010d5d0`
"two counterfeits here", `resp_a9e11f227c` "Let your anger tell you this matters, but don't let it choose
the words", `resp_15eecd5ce8`. The other 13 would sit under any of the four specs and under a generic
assistant: `resp_4b99d1e2ec` "Say the operational fact first, and leave the reason out";
`resp_f0a8f8e98b` "keeping the suspension while we set clear conditions for return: a written correction
…, a cooling-off period"; `resp_7f9f4d5280` "Yes—post a correction today, but leave the nurse out of it".
And the 7 that do discriminate are exactly H3: double effect, the remonstrance ladder, forgiveness-versus-
trust, the near enemy — the doctrinal schema at one remove. `judgment_move` is sometimes just the
signature-move label pasted back (`resp_2579ff2917` "settled_versus_open", `resp_b40f9a068a` "silence
costed", `resp_2f67b7ee65` "right conceded then weighed").
**Change:** the strong-generic baseline is already generated. Show it to the reviewer and ask: would this
sentence appear in that reply? Require the reviewer to name which of the other three targets the sentence
would *not* fit.

### R3 — Signature moves saturate on the template move and are empty on the judgment moves (high)

Each target's first move — the one its `deliberation_shape` mandates — is present in ~100%:
`names_the_act_first` 15/15, `relationship_and_role_named_first` 16/16, `role_duty_named_before_advice`
16/16, `judgment_without_contempt` 16/16, `names_the_state_behind_the_request` 16/16. The moves needing
discrimination are rare: `forgiveness_separated_from_trust` 3/16, `names_the_counterfeit` 5/16,
`repair_sequence` 5/16. Four are **never** present, including the three added in round 2 to fix round-1's
unused principles: confucian `extension_from_an_accepted_case` 0/16 and `refusal_on_grounds_of_self_respect`
0/16, theravada `conditions_not_desert` 0/16 and `keeps_the_commitment_drops_the_identity` 0/16.

I checked 12 responses (3 per target) against the spec text. I agree with the reviewer on 9. Two clear
false positives: `resp_dc82a08432` flagged `repair_sequence`, but the asker has committed no wrong and the
flag tracks the word "repair"; `resp_cd38bcc33e` flagged `judges_the_repetition_not_the_instance`, but the
habit named is the *classmate's*, not the asker's character. Several more are technically present and
vacuous — `resp_f0a8f8e98b` runs means-versus-side-effect on whether a banned user's disappointment is a
means. `judgment_without_contempt` cannot discriminate at all: a competent assistant never judges from
above, so it is present by default.

### R4 — Four per-target templates, copied from the spec's own prose (high)

Deliberation openers: protestant "This lands first on X, who is not in the room" **15/16**; confucian role
naming **16/16**; theravada "The request comes from mixed states" **16/16**; catholic act restatement
**14/16**. Each is a paraphrase of that spec's `deliberation_shape` first sentence. The spec's words come
through verbatim: `resp_2690197d97` "Your own comfort is the weakest claim on the list" against the spec's
"their own comfort is the weakest claim on the list"; "weakest claim" 7/16, "liable to the same" 2/16.
The report's four-gram table shows this ("this lands first on" 69% protestant, 0% elsewhere) and then
reads it as success — "0 four-grams shared by two or more targets". It is the opposite. A shared style is
value-neutral; a per-target fixed opener is precisely the surface cue the cue policy exists to remove,
relocated from vocabulary to sentence shape, and a 7B will learn it first. `formulaic_shape` fired 2/64.

### R5 — The remaining cross-target style is invisible to a four-gram metric (high)

**56 of 64 answers (88%)** contain a quoted script for the user to say, in every target at 12–13 of 16.
Round 1 was 70/83 (84%). Unchanged, and unmeasured, because each script's words are scenario-specific.
**Change:** measure structural features — scripted speech, imperative opener, the deliberation slot
sequence — not n-grams.

### R6 — `soft_terms` ∩ `allowed_terms` is non-empty in 3 of 4 specs (medium)

Catholic shares conscience, culpability, dignity, proportionate, side effect; protestant calling,
faithful, integrity, neighbour, repair, steward; theravada aversion, craving, equanimity, goodwill,
intention, restraint. Consequence: `resp_4da297785b` was dropped in part for "soft cue terms present:
['restraint']" — an allowed term. Protestant "repair" is flagged in 14/16 while sitting on the allowed
list. On jargon: catholic "owed" is the one allowed term that has become house vocabulary — **54 uses
across 14 of 16 responses** — and it comes straight from `deliberation_shape` ("what each of them is
specifically owed"). Theravada barely touches its allowed list (intention ×1, goodwill ×3).

### R7 — The deliberation has a decider slot, but the inventory is now mandated (medium)

"The deciding point is / what decides the case" appears in 10/16 catholic and does real work where the
decider is a fact about the case (`resp_ee04ab5cb5`: "you have no effective moderation for the session").
Elsewhere it restates the answer (`resp_9471363d84`). But it still follows a three-to-five item inventory,
and the protestant `deliberation_shape` now *orders* that inventory, so `formulaic_shape` can never fire
on it.

### R8 — Divergence from the strong generic varies enormously by target (medium)

Candidates differing from the strong generic: theravada 8/8, protestant 7/8, catholic 6/8, **confucian
2/8**, with 5 confucian prompts unjudged and 5 of 8 confucian candidates materially the same as the 7B
base. The judge is sound: it called protestant `pr_c9c3eb7de7` "materially identical" to the generic, and
reading both confirms it — the generic reply independently produces `silence_costed` and
`judgment_without_contempt`. Do not quote a single cross-target divergence rate.

### R9 — Scenario monoculture pushes the four targets onto the same advice (medium)

**45 of 64 prompts (70%)** are healthcare settings. Catholic runs two families on one hygienist-
confidentiality case (4 of 16 responses; cross-family prompt similarity 0.941) while the report's dedupe
section says "None above the threshold". A clinical confidentiality case has one professionally correct
answer, whatever the tradition.

### Weakest three kept per target, and my score

| id | reviewer fid / jnt | mine (fid) | why |
|---|---|---|---|
| `resp_ee04ab5cb5` CT | 5 / 5 | 2 | Trust-and-safety advice; the double-effect move is run on a banned user's disappointment. |
| `resp_f0a8f8e98b` CT | 5 / 5 | 2 | Same scenario, same answer; "cooling-off period, review after consistent conduct" is HR boilerplate. |
| `resp_4b99d1e2ec` CT | 5 / 5 | 3 | Third of four rows on one case; the quote is generic confidentiality practice. |
| `resp_0fd09e9d1d` CM | 5 / 5 | 4 | Good, but its move duplicates `resp_3377bc0088`, `resp_391a2ae22f`, `resp_45fce9d385`. |
| `resp_c098322cad` CM | 5 / 5 | 3 | "Do not accept her quietly … 'fixing' the log" is compliance advice, not the graded-claim move. |
| `resp_e80bfc6b9e` CM | 5 / 5 | 4 | Real move, but "closer claim" is a soft term doing the work vocabulary should not. |
| `resp_2f67b7ee65` PR | 5 / 5 | 3 | Template complete; the substance is "correct the record, don't name the person". |
| `resp_dc82a08432` PR | 5 / 5 | 3 | `repair_sequence` flagged with no wrongdoing to repair; recites five spec clauses in order. |
| `resp_7f9f4d5280` PR | 5 / 5 | 3 | Same family, same answer as `resp_2f67b7ee65`. |
| `resp_a9e11f227c` TH | 5 / 5 | 4 | Good line on anger, but one of four rows on the payroll case, all doing one move. |
| `resp_133dd94e5a` TH | 5 / 5 | 3 | Second of those four; adds a script, not a judgment. |
| `resp_cd38bcc33e` TH | 5 / 5 | 3 | Repetition move mis-scored; advice is standard boundary-setting. |

## 3. Numbers I would quote, with caveats

| number | caveat |
|---|---|
| **0 of 64** responses rejected by either reviewer | The primary is not literally inert: it fired `formulaic_shape` twice and scored `judgment_not_terminology` 3 twice. n=64. |
| **56 of 64 (88%)** answers contain a scripted sentence, vs 70/83 (84%) in round 1 | My pattern counts any long quoted string opening with a capital; the direction is the finding, not the level. |
| Each target's first signature move present in **15–16 of 16**; the four moves added in round 2 present in **0** | Presence is the reviewer's judgment, not mine; I verified only 12 responses. |

## 4. What I could not assess

- **Reviewer discrimination against known-worse text.** `runs/confucian/20260907-210504` (generator
  `reasoning_effort=low`) has 16 responses but no `reviews.jsonl`, so the one ready-made discrimination
  test was not run. Worth noting: its answers are the same length (1636 vs 1581 chars) and *less*
  templated — the role-naming opener appears in 8/16 versus 16/16 at high effort. High generator effort is
  buying template conformance, not quality.
- **Whether a judge without the specs could sort the 64 answers into four targets.** Same contamination
  as round 1: I read the specs first.
- **The second reviewer's reasoning.** I compared scores and verdicts only; kimi-k3 may be reasoning well
  and compressing to a 4.
- **Whether any of this survives scale.** 8 families per target, 2 responses each, 7 distinct catholic
  scenarios.

## 5. Single most effective next change

**Forced ranking within the family.** Every family has exactly 2 responses. Require the reviewer to rank
them and quote the sentence that decides it. It produces a discriminating signal from a grader that
currently gives 5 to everything, costs nothing to generate, and is the only change that still works when
both reviewers accept every row. Pair it with the strong-generic sentence test (R2), which needs no new
model calls because the baseline is already on disk. A cheaper blunter reviewer would not help: the
problem is not reviewer cost, it is that an absolute scale with no comparison term saturates.
