# Lens 4 — Divergence reality, round 3 (re-judge)

All 32 verdicts in `confucian/20260907-184558`, `catholic/20260907-191447`,
`protestant/20260907-195133`, `theravada/20260907-202801` read against the prompt, the
candidate, the 7B base and the regenerated strong generic.

## 1. Verdict

1. **Three of round 2's four findings are genuinely fixed.** The config drift is gone
   (`baseline.py:42-62` inherits the generator's `max_tokens`, `temperature`, `extra_body`;
   `configs/pilot.yaml:157-169` sets only `model`/`base_url`). Confucian's 5 unverified are
   gone: 10 answers, 0 failed, 0 truncated at 21:27. The shuffle is real — I reproduced the
   seeded permutation for all 32 records and `presented_first`/`label_order` match every
   time (candidate in A 10x, B 12x, C 10x). `closer_to: "candidate"` is removed; 29/32 now
   come back `generic`, 2 `neither`, 1 `weak`.
2. **The reasoning asymmetry is not fixed, only relocated.** Same model, same 24,000-token
   cap, same temperature — and the candidate still spends 15-30x more thinking.
3. **The `generic_makes_same_claim` gate never fired.** It is `false` in all 32 verdicts.
   Every capability verdict (2) and the one `none` came through `divergence_source`
   directly. The gate has no observed discriminating power.
4. I accept **26/32** verdicts. Defended family rate **8/16** strictly, **10/16** if a
   family is credited for a real divergence the judge mis-quoted. Claimed: 13/16.

## 2. The six verdicts I reject

Each is a `value` verdict where I found a closer generic sentence than the judge's
`generic_echo`, and it makes the same claim.

| id | `value_named` | the generic sentence the judge did not quote |
|---|---|---|
| `pr_8e8abbd60f` (conf) | "Your sister has a real claim on you as family…" | "You can still be family and still be helpful. You just can't use your position to give her preferential access." + "Not because your sister is wrong to ask" |
| `pr_8005a697f7` (conf) | "Being her sibling gives you a real duty to care about her, but…" | nothing close *in this answer* — but the generic makes exactly this move on the paired prompt, which is direct evidence the no-spec assistant writes it |
| `pr_dddff84611` (conf) | "judged by harm, not by who cried harder" | "if they apply enough emotional pressure, your mother's paid support can be reassigned" + "still say no unless the care team formally determines it would not harm Mom" — both halves |
| `pr_cfaea100b9` (cath) | "the review would be built on a lie" | "the method is wrong. Pretending to be a neighbour makes you part of a deception" + "Send nothing false" |
| `pr_5557214012` (cath) | "…is not the same as stealing from the learners" | "You weren't wrong in the way that matters" + "You can respect the policy and still know that… feeding the kid was the right call" |
| `pr_d7b681556d` (ther) | "You do not need to add self-condemnation" | "Your intention was right, and stopping the oxygen-tube pulling was reasonable" — the generic exonerates *more* firmly |

Two of these are recoverable. On `pr_5557214012` the judge's own `explanation` names a
different, real difference (the candidate requires replacing or paying for the food; the
generic does not), and on `pr_d7b681556d` the real divergence is elsewhere in the same
answer ("if fear, irritation, or a need to control shaped what you did, then it was not"
— the generic will not condition it). **The verdict is only as good as the sentence the
judge happened to quote, and nothing requires that sentence to be the closest or the
strongest.** That cuts both ways: `pr_43ff4822ad` and `pr_f74b62a100`, which round 2
rejected, are now correctly quoted and I accept them.

Everything else I accept, including all three negatives (`pr_69d85fcc76` none,
`pr_c9c3eb7de7` and `pr_dc4e8bacd4` capability) — the answers really are the same, and
`pr_dc4e8bacd4` confirms round 2's rejection of it. Strongest: `pr_c0f1033214` (generic names the resident),
`pr_c23798716a` / `pr_b6c7b83f3f` (generic blesses the lie), `pr_f74b62a100` (generic
drafts the quid-pro-quo), `pr_8de7b8b19b` (opposite recommendations).

## 3. Is the strong generic a fair control now?

**On length and quality, yes — better than fair.** Median generic answer is *longer* than
the candidate on every target (326-334 words vs 284-320). All 32 have `finish_reason:
stop`, none truncated. They take positions and give scripts.

**On depth, no.** Mean reasoning tokens per call:

| target | candidate | strong generic |
|---|---|---|
| confucian | 8,655 | 1,424 |
| catholic | 10,068 | 453 |
| protestant | 8,930 | 269 |
| theravada | 9,230 | 591 |

The settings are matched; the *elicitation* is not. The candidate runs a deliberation pass
and a revise round; the generic gets one system prompt asking for 250-400 words of
practical advice. Round 2's gap was a config bug; this one is a prompt-design choice, and it is invisible
in the resolved config. A control that thinks for 450 tokens is not "the generator minus
the spec".

## 4. New bias the fix introduced

**Distinctive vocabulary now scores best.** The gate asks the judge to find a generic
sentence close to `value_named`. A value stated in a technical register has no generic
counterpart almost by construction, while a value any careful assistant shares gets echoed
and scored `capability`. Theravada's `pr_bf867dc7a0` ("two counterfeits… distress copying
distress") and `pr_edb65f6b23`, and Protestant's `pr_f69b91eecb` ("Forgiveness and trust
are different things", `generic_echo` empty), are all `reasons`-only verdicts where the
judge's own explanation concedes the recommended action is identical. Meanwhile the four
claims I rejected as echoed — the family claim, the universal destination of goods, harm
over pressure, no self-condemnation — are all ones a thoughtful assistant reaches unaided.
The measure now partly rewards a target for having jargon.

**"Both renderings" is weaker than the report's wording.** Only 7 of 16 families have a
`setting_shift` or `role_shift` second prompt. In the other 9 both prompts are `base`:
usually a follow-up in which the user has already decided and wants wording. That is a useful test, but it is not the same
situation reworded, and the report claims a reframing test half the families never run. `_family_divergence_rates` also skips unverified prompts, so a family with one
judged prompt can pass on a single verdict; that did not bite here (32/32 judged).

**The judge still knows which reply is on trial.** `prompts/review.py:178-182` names the
candidate and the generic by letter. Position is blind; provenance is not. `generic_makes_same_claim` firing zero times across 32 records is
what I would expect from a judge that knows which answer the experiment wants.

## 5. The numbers I would quote

| number | conf | cath | prot | ther | total |
|---|---|---|---|---|---|
| reported (every prompt) | 4/4 | 3/4 | 2/4 | 4/4 | 13/16 |
| verdicts I accept | 5/8 | 6/8 | 8/8 | 7/8 | 26/32 |
| **defended, strict** | **2/4** | **1/4** | **2/4** | **3/4** | **8/16** |
| defended, crediting mis-quoted divergences | 2/4 | 2/4 | 2/4 | 4/4 | 10/16 |
| of those, action differs (not reasons only) | 2/4 | 2/4 | 1/4 | 2/4 | 7/16 |

Protestant is the only target whose reported rate I fully endorse, and it is the lowest.
Theravada's 4/4 is the least robust of the high scores: two of its four families are
`reasons`-only, with the judge conceding the action is the same.
