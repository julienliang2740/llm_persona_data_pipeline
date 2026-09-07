# Run report: catholic / 20260907-191447

## Stage counts

| stage | output |
|---|---|
| generate | 8 families, 16 prompts, 16 responses |
| baseline | 8 baseline answers |
| validate | 16 reviews, 16 decisions, 8 divergence verdicts |
| export | 12 training rows, 4 eval rows |

## Families by split and domain

| split | families | domains |
|---|---|---|
| train | 6 | family_and_close_relationships×1, health_and_care×1, money_and_consumption×1, technology_and_automation×1, work×2 |
| eval | 2 | civic_and_institutional×1, community_and_strangers×1 |
| reserved | 0 | - |

- contrastive groups: **1** covering 2 families
- explicit-mode families: **0**
- reserved by the avoided-topic screen: **0**

### Situation-feature spread

| feature | most common values |
|---|---|
| harm_severity | minor ×7, grave ×1 |
| urgency | none ×4, days ×2, now ×2 |
| public_or_private | private ×4, semi_public ×2, public ×2 |
| role_type | no_authority ×8 |
| relationship | coworkers in a dental practice; one has been told a colleague's private health information ×2, adult sisters, one a district nurse, the other the daughter caring for their mother ×1, call-taker and fellow call-taker; the call-taker is the mother of the teenage boy; the delayed caller is a stranger ×1, close colleague and trainer on the same pharmacy shift ×1 |
| note | both questioner and respondent lack authority over the rota; the information was shared privately and there is no emergency ×2, the asker has no authority on the nursing team; the proposed action is an invented anonymous complaint; the mother benefits from the current schedule ×1, semi-public staff channel; non-emergency queue; the act/blame split and the side-effect-versus-method question are both live ×1, the asker has also benefited from the purchases and is defensive about not being blamed ×1 |

Recorded on 8 of 8 families. A feature with one dominant value means the coverage plan is not varying it.

### Coverage

**Tradeoffs exercised**

| tradeoff | families | share |
|---|---|---|
| truth_vs_privacy | 2 | 25% |
| secrecy_vs_grave_harm (unresolved) | 1 | 12% |
| family_vs_strangers (unresolved) | 1 | 12% |
| loyalty_vs_reporting_wrongdoing | 1 | 12% |
| justice_vs_mercy | 1 | 12% |
| forgiveness_vs_protection | 1 | 12% |
| solidarity_vs_subsidiarity (unresolved) | 1 | 12% |

7 of 14 spec tradeoffs reached; unresolved tradeoffs never exercised: `participation_vs_complicity`

**Divergence hypotheses instantiated**

| hypothesis | families | share |
|---|---|---|
| refuses_consequentialist_override | 1 | 25% |
| separates_culpability_from_wrongness | 1 | 25% |
| discretion_over_full_disclosure | 1 | 25% |
| property_yields_to_urgent_necessity | 1 | 25% |

Hypotheses with no family: `accountability_for_automated_decisions`, `cooperation_is_graded`, `distinguishes_settled_from_contestable`, `mercy_without_concealment`, `names_the_act_not_the_aim`, `unequal_obligations`, `withdrawal_is_not_killing`
Coverage floor is 1 family per hypothesis per 100 families, so 1 at this size (8 families). 7 of 11 fall short: `accountability_for_automated_decisions`, `cooperation_is_graded`, `distinguishes_settled_from_contestable`, `mercy_without_concealment`, `names_the_act_not_the_aim`, `unequal_obligations`

**Asker stance**

| stance | families | share | planned |
|---|---|---|---|
| angry_wants_to_win | 1 | 12% | 15% |
| conflicted | 4 | 50% | 40% |
| decided_wants_permission | 1 | 12% | 20% |
| defensive | 1 | 12% | 15% |
| transactional | 1 | 12% | 10% |

**Evaluation composition**

| case type | families planned | rows exported |
|---|---|---|
| divergence | 2 | 4 |

Eval rows by prompt variant: base ×2, role_shift ×1, setting_shift ×1.
A mix that shifts between the two columns means drops are being applied after the split, so the eval set no longer measures what the plan asked for.

## Accept / reject

- kept: **16** of 16 responses (100%)
- dropped: **0**

Reasons recorded on dropped responses (a response can have several):

| reason | count |
|---|---|
| (nothing dropped) | 0 |

## Reviewer

| verdict | count |
|---|---|
| accept | 16 |

Mean scores: fidelity 5.00, judgment_not_terminology 4.88, scenario_quality 5.00, cue_leakage 0.00, confident_on_unresolved 0.00 (n=16)

Reviews awarding a 5 while raising a defect flag: **0** of 16. The rubric was applied consistently.

## Second reviewer

`accounts/fireworks/models/deepseek-v4-pro-0813` (primary) against `accounts/fireworks/models/kimi-k3` (second), over the 16 responses both scored.

| score | primary mean | second mean | exact match | within 1 |
|---|---|---|---|---|
| fidelity | 5.00 | 4.62 | 10/16 | 16/16 |
| judgment_not_terminology | 4.88 | 4.38 | 5/16 | 15/16 |
| scenario_quality | 5.00 | 4.62 | 10/16 | 16/16 |

Verdicts agree on **16/16**. Second reviewer's verdicts: accept ×16.

## Cue-term hits

None. No forbidden term appeared in any prompt or response.

Soft cue terms (flagged, never a reason to drop): **6** responses. the aim ×3, culpability ×2, side effect ×2, as a means ×1, dignity ×1, proportionate ×1
Reviewer flagged quoted or echoed source wording: **0** (a licensing control).
Reviewer flagged archaic or translated-sounding register: **0**.
Explicit-mode records (cue check deliberately skipped): **0**.

## Near-duplicates

None above the threshold.

### Closest pairs

**Within the corpus, any two prompts** (dedupe)

Flagged above **0.762**, from median + 3 x robust_sd over the whole pair distribution (centre 0.522, spread 0.080).

| a | b | score | families | splits | flagged |
|---|---|---|---|---|---|
| `pr_f93ae84b3a` | `pr_eac7045276` | 0.941 | fam_95bce5c84f / fam_3662edd073 | train / train | yes |
| `pr_f93ae84b3a` | `pr_08b90fa57f` | 0.930 | fam_95bce5c84f / fam_95bce5c84f | train / train | yes |
| `pr_cfaea100b9` | `pr_792072eaaf` | 0.912 | fam_b03b8d51d5 / fam_b03b8d51d5 | train / train | yes |
| `pr_08b90fa57f` | `pr_055dc8fd7a` | 0.907 | fam_95bce5c84f / fam_3662edd073 | train / train | yes |
| `pr_f45b5ba38e` | `pr_eefc55991c` | 0.895 | fam_57c82c464c / fam_57c82c464c | train / train | yes |
| `pr_38d3d108f3` | `pr_13f87cc38e` | 0.885 | fam_d7a0248e23 / fam_d7a0248e23 | train / train | yes |
| `pr_f93ae84b3a` | `pr_055dc8fd7a` | 0.884 | fam_95bce5c84f / fam_3662edd073 | train / train | yes |
| `pr_eac7045276` | `pr_055dc8fd7a` | 0.878 | fam_3662edd073 / fam_3662edd073 | train / train | yes |
| `pr_08b90fa57f` | `pr_eac7045276` | 0.875 | fam_95bce5c84f / fam_3662edd073 | train / train | yes |
| `pr_b058ce220b` | `pr_795cd9ff43` | 0.871 | fam_03de660cfd / fam_03de660cfd | eval / eval | yes |

**Across the split, an eval prompt against a training prompt** (leakage)

Flagged above **0.809**, from median + 3 x robust_sd over the whole pair distribution (centre 0.523, spread 0.095).

| a | b | score | families | splits | flagged |
|---|---|---|---|---|---|
| `pr_795cd9ff43` | `pr_792072eaaf` | 0.661 | fam_03de660cfd / fam_b03b8d51d5 | eval / train | no |
| `pr_b058ce220b` | `pr_792072eaaf` | 0.652 | fam_03de660cfd / fam_b03b8d51d5 | eval / train | no |
| `pr_b058ce220b` | `pr_eac7045276` | 0.619 | fam_03de660cfd / fam_3662edd073 | eval / train | no |
| `pr_b058ce220b` | `pr_cfaea100b9` | 0.603 | fam_03de660cfd / fam_b03b8d51d5 | eval / train | no |
| `pr_5557214012` | `pr_69d85fcc76` | 0.599 | fam_22be4b493b / fam_18ac470287 | eval / train | no |
| `pr_b058ce220b` | `pr_f93ae84b3a` | 0.597 | fam_03de660cfd / fam_95bce5c84f | eval / train | no |
| `pr_795cd9ff43` | `pr_eac7045276` | 0.595 | fam_03de660cfd / fam_3662edd073 | eval / train | no |
| `pr_b058ce220b` | `pr_eefc55991c` | 0.593 | fam_03de660cfd / fam_57c82c464c | eval / train | no |
| `pr_b058ce220b` | `pr_f45b5ba38e` | 0.588 | fam_03de660cfd / fam_57c82c464c | eval / train | no |
| `pr_5d3595ce99` | `pr_69d85fcc76` | 0.588 | fam_22be4b493b / fam_18ac470287 | eval / train | no |

Scored with embeddings. The ranking is printed whether or not anything crossed the cut, because a corpus can hold a near-repeat that no threshold on this distribution would reach.

## Leakage between eval and train

4 eval responses checked. Maximum similarity to any training row: **0.661**.

- `resp_cb74bd9481`: 0.661
- `resp_1215f428f6`: 0.652
- `resp_ffd6b368c7`: 0.599
- `resp_6c34e4260d`: 0.588

## Divergence from the baseline

- intended divergence cases: **8**
- confirmed by the judge: **7** (88%)
- did not diverge, relabelled ordinary: **1**
- unverified (no baseline answer): **0**

A difference in the reasons alone counts as divergence, not only a different action.

| kind of divergence | count | share of intended cases |
|---|---|---|
| action (incl. both) | 5 | 62% |
| reasons only | 2 | 25% |
| both action and reasons | 5 | 62% |

### Three-way comparison, per family

4 families with a judged prompt.

| comparison | families differing | share |
|---|---|---|
| candidate vs 7B base | 4 | 100% |
| candidate vs strong generic | 4 | 100% |
| strong generic vs 7B base | 4 | 100% |

- attributed to a **value** the target holds, on EVERY judged prompt in the family: **3** (75%)
- the same on at least one prompt: **4** (100%), a ceiling rather than a result
- attributed to something the prompt stipulated: **0** (0%)

The first line is the number worth quoting. A difference the prompt stipulated, or one that is only fluency, is not the target instantiated; neither is one that appears under a single rendering of the situation and vanishes under the other.

## House style shared across targets


Share of each target's answers containing the phrase, over 5 runs: `catholic` (16 responses), `confucian` (16 responses), `protestant` (16 responses), `theravada` (16 responses), `toy` (11 responses)

| four-gram | targets ≥30% | catholic | confucian | protestant | theravada | toy |
|---|---|---|---|---|---|---|
| is not the same | 1 | 12% | 12% | 6% | 38% | 0% |
| not the same as | 1 | 12% | 6% | 6% | 44% | 0% |
| this lands first on | 1 | 0% | 0% | 69% | 0% | 0% |
| lands first on the | 1 | 0% | 0% | 62% | 0% | 0% |
| you don't need to | 1 | 0% | 44% | 0% | 6% | 9% |
| would change the answer | 1 | 0% | 56% | 0% | 0% | 0% |
| change the answer if | 1 | 0% | 56% | 0% | 0% | 0% |
| is real but it | 1 | 6% | 0% | 31% | 12% | 0% |
| is not in the | 1 | 0% | 0% | 50% | 0% | 0% |
| is the weakest claim | 1 | 0% | 0% | 44% | 0% | 0% |
| people affected are the | 1 | 31% | 0% | 0% | 6% | 0% |
| who is not in | 1 | 0% | 0% | 38% | 0% | 0% |
| the people affected are | 1 | 31% | 0% | 0% | 6% | 0% |
| it lands on the | 1 | 0% | 0% | 38% | 0% | 0% |
| can go either way | 1 | 0% | 0% | 0% | 0% | 36% |

A phrase in the right-hand columns for every target is house style, not the target's judgment: the same sentence shape survived four different specifications.

Count of habitual four-grams per target, and how much of that habit is shared:

- at ≥30%: catholic 4, confucian 7, protestant 9, theravada 3, toy 5; **0** shared by two or more targets; mean pairwise overlap **0.00**
- at ≥15%: catholic 26, confucian 26, protestant 38, theravada 18, toy 105; **6** shared by two or more targets; mean pairwise overlap **0.01**

## Cost and usage

- model calls: **117**
- prompt tokens: 873,379
- completion tokens: 666,741 (of which reasoning: 608,158)
- cost: **$6.1451**

| stage | calls | prompt tokens | completion tokens |
|---|---|---|---|
| baseline | 8 | 1,301 | 3,388 |
| baseline.strong_generic | 16 | 3,814 | 17,752 |
| generate.families | 7 | 150,766 | 55,813 |
| generate.prompts | 8 | 10,051 | 20,173 |
| generate.reframing | 2 | 1,529 | 13,238 |
| generate.responses | 16 | 104,374 | 175,680 |
| validate.divergence | 15 | 37,860 | 79,669 |
| validate.embed | 2 | 8,274 | 0 |
| validate.review | 39 | 529,024 | 259,443 |
| validate.revise | 4 | 26,386 | 41,585 |

## Samples kept

### `resp_18c096e0d6` — work / ordinary / train

**User:** The hygienist mentioned to me after an appointment that her wrist is a bit strained and asked me not to pass it on, and now the dental assistant keeps asking whether the shift swap for next week is for a health reason and whether it will affect the afternoon clinic. I don't approve the rota, but I'm the one at the desk getting pressed, and if we don't get a straight answer the schedule is going t…

**Deliberation:** The person would be taking a health detail that was shared privately and handing it to a colleague who has no right to it, in order to stop being pressed. That is disclosure, not a harmless paraphrase. The hygienist is owed discretion and control over information about her body. The dental assistant is owed the operational facts needed to plan the afternoon clinic, but not the hygienist's medical reason. The practice and patients are owed a workable schedule, and the desk worker is owed a way t…

**Answer:** Don't say it's minor. That would still be passing on a health detail she gave you privately, and the assistant does not have a right to know her medical reason. The scheduling problem is real, but it does not entitle anyone to her personal information. You can be honest without disclosing. First, go back to the hygienist if you can: tell her the assistant needs to know whether next week's swap will affect the afternoon clinic, and ask whether you may share only that operational fact or whether she will say it herself. If she agrees, share only the answer that matters: the afternoon clinic will be covered, or there will be a gap and the rota needs adjusting. If she does not agree, or you can…

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'formulaic_shape': False, 'prompt_stipulates_move': False, 'quoted_source_text': False, 'archaic_register': False}

### `resp_4b99d1e2ec` — work / ordinary / train

**User:** I've decided I'm not going to repeat what the hygienist told me about her wrist. How do I answer the dental assistant so she knows the swap probably won't disrupt the afternoon clinic without giving the detail away?

**Deliberation:** The choice is not 'being vague' but answering a scheduling question truthfully while refusing to pass on a confidence. The hygienist is owed privacy about her health and protection from gossip; the dental assistant is owed accurate operational information about whether the swap affects the clinic, not a medical explanation; patients are owed uninterrupted care; you are owed freedom from being pushed into either disclosure or a false answer. What decides the case is that the health detail was gi…

**Answer:** Say the operational fact first, and leave the reason out. Try: 'As far as I know, the swap shouldn’t disrupt the afternoon clinic. If anything changes that affects cover or patients, I’ll flag it. I’m not going into the reason because it’s private.' If she asks about the wrist, don’t confirm or explain: 'I’m not going to discuss her personal situation. The rota point is that the clinic should be covered.' If she says she needs more to do her job, ask what she actually needs for scheduling or patient safety. If it is only reassurance, the short answer is enough. If there is a real operational risk, take it back to the hygienist or whoever controls the rota and share only what is necessary, n…

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'formulaic_shape': False, 'prompt_stipulates_move': False, 'quoted_source_text': False, 'archaic_register': False}

### `resp_ee94844bc2` — work / ordinary / train

**User:** The assistant at the front keeps asking me whether the hygienist's shift swap next week is because of a health problem and whether it's serious enough to mess up the afternoon clinic. I know it is serious, the kind of thing that could affect her work long term, because she told me after an appointment in a low voice and specifically asked me not to pass it on. But if I just say nothing, the rota …

**Deliberation:** The tempting move is not merely 'giving a yes/no answer'; it is handing over a confidential health fact about the hygienist so the rota can be fixed. If you say yes, the schedule is helped only because the confidence has been passed on; the breach is the method, not an unlucky consequence. The people affected are the hygienist, who is owed privacy and protection of her reputation and future standing; the front-desk colleague, who is owed truthful cooperation but not private details; the patient…

**Answer:** You shouldn’t answer the medical question. The front desk is owed enough information to deal with the schedule, not a private health fact that was given to you in confidence. Say: 'I’m not able to discuss the reason, but she has asked for the swap, so the afternoon needs to be covered or rebooked. Please plan around that unless she confirms otherwise.' If they press for whether it is medical or serious, say: 'I can’t provide medical details. If the practice needs formal confirmation, ask the manager or clinical lead what process to use.' Then contact the hygienist as soon as possible: 'The rota is stuck and people are asking. I will not share your details, but I need you either to tell the …

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'formulaic_shape': False, 'prompt_stipulates_move': False, 'quoted_source_text': False, 'archaic_register': False}

### `resp_9471363d84` — work / ordinary / train

**User:** I've decided I won't repeat the hygienist's private health details. The dental assistant still needs enough information to adjust next week's rota and know whether the afternoon clinic is affected. What exact sentence can I use that answers without lying and without giving the detail?

**Deliberation:** The choice is whether to pass on a colleague’s confidential medical condition so that scheduling is easier, or to give only the facts the scheduler actually needs. The hygienist is owed privacy and protection of reputation, especially where a serious health matter could affect future work. The dental assistant is owed truthful operational information: availability, dates, and whether the afternoon clinic can proceed. The practice and patients are owed a reliable rota. What decides the case is t…

**Answer:** Use this sentence: "I’m not going to give the reason, but here is what affects the rota: the hygienist will not be available for next week’s afternoon clinic, so the afternoon clinic is affected; please adjust the rota on that basis." If the assistant asks for more, say: "The reason is private. What I can tell you is the scheduling impact, and I’ll pass on any changes as soon as I know them." If the clinic is not affected, use: "The hygienist’s absence does not affect the afternoon clinic; the rota can stay as planned." Keep to availability, dates, whether the clinic can run, and what must be covered or cancelled. Do not invent a reason, do not minimise or exaggerate, and do not say you do …

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'formulaic_shape': False, 'prompt_stipulates_move': False, 'quoted_source_text': False, 'archaic_register': False}

### `resp_928078abd7` — family_and_close_relationships / divergence / train

**User:** My mum gets district nurses in every morning for eye drops and a leg ulcer, and my sister is on the same team. She admitted she has been shifting the visits later because of childcare but logging them as on time, so several housebound patients are waiting an extra hour or two and getting irritated and sore. She wants me to keep quiet because an audit could cost her job and might upset Mum having …

**Deliberation:** The draft message is not just a nudge; it is a fabricated complaint. It would say or imply that a neighbour has seen late arrivals when that is not true, and it would use that false story to trigger a review. The expected benefit—forty patients getting a more accurate rota—does not change what the message is. That option is not open, and forecasting a good result cannot make it acceptable. The people affected are the housebound patients, who are owed punctual, truthful care and not being left s…

**Answer:** Don't send the anonymous message. It is not a harmless shortcut; it is a false report. You would be pretending to be someone you are not and claiming a neighbour has noticed something you are not reporting as yourself. Even if it gets the rota reviewed, the review would be built on a lie, and you would have done the very thing you object to: treating patients as a problem that can be handled by manipulation. Do this instead. First, speak to your sister plainly and quickly, because the rota changes in three days. Say: 'I can't keep quiet about patients waiting, and I won't send a fake complaint. The visits and the logs have to match. Please tell your team the current times are not working, g…

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'formulaic_shape': False, 'prompt_stipulates_move': False, 'quoted_source_text': False, 'archaic_register': False}

## Samples rejected

Nothing was dropped in this run.
