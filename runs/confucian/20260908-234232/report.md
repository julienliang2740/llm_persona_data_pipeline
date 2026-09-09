# Run report: confucian / 20260908-234232

## Stage counts

| stage | output |
|---|---|
| generate | 240 families, 479 prompts, 479 responses |
| baseline | 193 baseline answers |
| validate | 479 reviews, 479 decisions, 192 divergence verdicts |
| export | 241 training rows, 0 eval rows |

## Families by split and domain

| split | families | domains |
|---|---|---|
| train | 239 | advice_and_correction×33, civic_institutional×34, family×53, interpersonal_conflict×38, learning_and_self_cultivation×29, work×52 |
| eval | 1 | work×1 |
| reserved | 0 | - |

- contrastive groups: **36** covering 72 families
- explicit-mode families: **0**
- reserved by the avoided-topic screen: **0**

### Situation-feature spread

| feature | most common values |
|---|---|
| harm_severity | minor ×90, serious ×80, grave ×70 |
| urgency | now ×82, none ×79, days ×79 |
| public_or_private | public ×82, private ×81, semi_public ×77 |
| role_type | no_authority ×111, peer ×60, holds_authority ×54, institution ×15 |
| relationship | younger sister and older brother, colleagues at the same small firm ×2, adult daughter and mother; the daughter holds moderator authority on the platform ×2, adult siblings ×2, parent of injured child, volunteer coach, club committee ×2 |
| note | The moderator's personal friendship with the content creator is the source of the disagreement; the lead holds authority over the final call ×2, The co-op's consensus culture functions as a form of harmony that suppresses urgent substantive objections; the child next door is the third party who bears the cost of delay ×2, The asker has system access but no decision-making authority; the partiality would be invisible to supervisors but visible in its effects on queue order. ×2, The asker has no decision-making authority but has information others lack; the defensiveness is about minimising his own knowledge and responsibility. ×2 |

Recorded on 240 of 240 families. A feature with one dominant value means the coverage plan is not varying it.

### Coverage

**Tradeoffs exercised**

| tradeoff | families | share |
|---|---|---|
| partiality_vs_impartial_procedure | 26 | 11% |
| respect_vs_correction | 25 | 10% |
| form_vs_urgent_need | 25 | 10% |
| compassion_vs_accountability | 25 | 10% |
| family_vs_public_justice | 24 | 10% |
| harmony_vs_truthfulness | 24 | 10% |
| individual_vs_structural_responsibility | 24 | 10% |
| scope_of_kinship_claims_on_scarce_resources (unresolved) | 23 | 10% |
| immediate_feeling_vs_reflective_correction (unresolved) | 22 | 9% |
| trustworthiness_vs_rightness | 22 | 9% |

10 of 10 spec tradeoffs reached; unresolved tradeoffs never exercised: none

**Divergence hypotheses instantiated**

| hypothesis | families | share |
|---|---|---|
| graded_concern_over_impartiality | 13 | 14% |
| harmony_without_sameness_over_conflict_smoothing | 12 | 12% |
| remonstrance_over_compliance_or_escalation | 12 | 12% |
| correction_over_accommodation | 11 | 11% |
| conditions_before_blame | 11 | 11% |
| override_of_form_under_serious_harm | 11 | 11% |
| rightness_governs_commitment | 9 | 9% |
| manner_as_substance | 9 | 9% |
| refusal_to_read_reputation_as_evidence | 8 | 8% |

Hypotheses with no family: none
Coverage floor is 1 family per hypothesis per 100 families, so 2 at this size (240 families). Every hypothesis meets it.

**Asker stance**

| stance | families | share | planned |
|---|---|---|---|
| angry_wants_to_win | 36 | 15% | 15% |
| conflicted | 98 | 41% | 40% |
| decided_wants_permission | 44 | 18% | 20% |
| defensive | 40 | 17% | 15% |
| transactional | 22 | 9% | 10% |

**Evaluation composition**

| case type | families planned | rows exported |
|---|---|---|
| ordinary | 1 | 0 |

Eval rows by prompt variant: none.
A mix that shifts between the two columns means drops are being applied after the split, so the eval set no longer measures what the plan asked for.

## Accept / reject

- kept: **277** of 479 responses (58%)
- dropped: **202**

Reasons recorded on dropped responses (a response can have several):

| reason | count |
|---|---|
| near-duplicate of | 188 |
| note: soft cue terms present | 27 |
| note: intended divergence did not hold | 13 |
| reviewer still asks for revision after a rewrite: The reply  | 12 |
| reviewer: fixed template shape rather than a shape this case | 7 |
| reviewer still asks for revision after a rewrite: The judgme | 4 |
| scores below thresholds | 3 |
| reviewer: confident resolution | 2 |
| reviewer still asks for revision after a rewrite: The answer | 2 |
| eval item too close to training data | 1 |
| reviewer still asks for revision after a rewrite: The sequen | 1 |
| note: prompt stipulates the target's move; relabelled ordina | 1 |
| reviewer rejected | 1 |

## Reviewer

| verdict | count |
|---|---|
| accept | 459 |
| revise | 19 |
| reject | 1 |

Mean scores: fidelity 4.79, judgment_not_terminology 4.90, scenario_quality 4.93, cue_leakage 0.00, confident_on_unresolved 0.00 (n=479)

Reviews awarding a 5 while raising a defect flag: **8** of 479. That combination means the reviewer is not applying the rubric, and the score cap did not catch it because the 5 sits on another dimension.

Conflicting pairs: formulaic_shape+fidelity=5 ×5, formulaic_shape+scenario_quality=5 ×5, confident_on_unresolved+scenario_quality=5 ×2, quoted_source_text+fidelity=5 ×1, quoted_source_text+judgment_not_terminology=5 ×1, quoted_source_text+scenario_quality=5 ×1, confident_on_unresolved+judgment_not_terminology=5 ×1.

Prompts that stipulate the target's move: **51** of 479; relabelled ordinary. The user handed the assistant the answer, so the case cannot show a difference from a generic assistant. This is a prompt-quality figure, not a mark against the response.

## Cue-term hits

None. No forbidden term appeared in any prompt or response.

Soft cue terms (flagged, never a reason to drop): **61** responses. keeps the relationship intact ×20, deference ×17, stronger claim ×10, closer claim ×8, what is fitting ×6, harmony ×2, remonstrance ×1
Reviewer flagged quoted or echoed source wording: **1** (a licensing control).
Reviewer flagged archaic or translated-sounding register: **0**.
Explicit-mode records (cue check deliberately skipped): **0**.

## Near-duplicates

94 cluster(s) covering 188 responses.

- `resp_95ff98bb8b` absorbs 3: resp_bd7df598ca, resp_81d4f0e1f1, resp_c44b98c14e
- `resp_be5ecac7f5` absorbs 2: resp_5c63d586d2, resp_019c872669
- `resp_465141a0a3` absorbs 3: resp_2a5081138a, resp_3a8deb9c82, resp_bb8908e3c1
- `resp_b81560b7cb` absorbs 2: resp_e3169f1e78, resp_c7cc129a54
- `resp_3655e3aaa0` absorbs 5: resp_cd781ee049, resp_a1f8667fbe, resp_109a289193, resp_a1d004cccd, resp_febeeb6f51
- `resp_8e87d72e14` absorbs 3: resp_f5b562cb1c, resp_f9c1400e82, resp_13b943ebe7
- `resp_9ed9d2af39` absorbs 2: resp_7b8fce4b89, resp_1c5ad128ba
- `resp_77dfaf557b` absorbs 1: resp_86529c88e8
- `resp_cc81a02ab4` absorbs 3: resp_920c3c38d0, resp_e7f2580bb0, resp_570b0a83c5
- `resp_be99f30f47` absorbs 4: resp_e8a9e93944, resp_178995b3b0, resp_9d4177ea6e, resp_70608983c7

### Closest pairs

**Within the corpus, any two prompts** (dedupe)

Flagged above **0.693**, from median + 3 x robust_sd over the whole pair distribution (centre 0.439, spread 0.085).

| a | b | score | families | splits | flagged |
|---|---|---|---|---|---|
| `pr_e7cb814531` | `pr_bb44c2f1fd` | 0.953 | fam_12d03afa87 / fam_12d03afa87 | train / train | yes |
| `pr_f0380a613b` | `pr_18dcd2f4f0` | 0.951 | fam_a752c80c0c / fam_d6ed82a633 | train / train | yes |
| `pr_b598f31dc0` | `pr_2f1498044e` | 0.950 | fam_a5360c25ce / fam_a5360c25ce | train / train | yes |
| `pr_9662e9b8aa` | `pr_dcb859d18e` | 0.949 | fam_25f5bc0790 / fam_7813daf924 | train / train | yes |
| `pr_2a3fc6fa40` | `pr_f3a3587741` | 0.947 | fam_3f186748b6 / fam_1afdd3fd7c | train / train | yes |
| `pr_bfc3fbbc5c` | `pr_de562d85ae` | 0.945 | fam_d9075b3c5d / fam_d9075b3c5d | train / train | yes |
| `pr_6c0336a139` | `pr_55f5c4a45c` | 0.945 | fam_25a8977f70 / fam_4c0b7a9c8a | train / train | yes |
| `pr_473f97188b` | `pr_3f38248fde` | 0.945 | fam_74392d774c / fam_e71ecdbb5b | train / train | yes |
| `pr_2a5a2b2aae` | `pr_fe3f5e46bd` | 0.944 | fam_65ba967775 / fam_65ba967775 | train / train | yes |
| `pr_54974ac923` | `pr_bd49ce861a` | 0.943 | fam_cb1dc00950 / fam_b75beddae7 | train / train | yes |

**Across the split, an eval prompt against a training prompt** (leakage)

Flagged above **0.598**, from median + 3 x robust_sd over the whole pair distribution (centre 0.393, spread 0.068).

| a | b | score | families | splits | flagged |
|---|---|---|---|---|---|
| `pr_a64dbaadad` | `pr_a7fbb5d033` | 0.710 | fam_c19be61df7 / fam_f6bb438000 | eval / train | yes |
| `pr_a64dbaadad` | `pr_901f4dd18f` | 0.697 | fam_c19be61df7 / fam_ca6ce7d7c2 | eval / train | yes |
| `pr_a64dbaadad` | `pr_e5fe141334` | 0.671 | fam_c19be61df7 / fam_f6bb438000 | eval / train | yes |
| `pr_a64dbaadad` | `pr_5bea2c024f` | 0.654 | fam_c19be61df7 / fam_8b648c0feb | eval / train | yes |
| `pr_a64dbaadad` | `pr_dc1c5aded8` | 0.648 | fam_c19be61df7 / fam_8b648c0feb | eval / train | yes |
| `pr_a64dbaadad` | `pr_fda2b1078e` | 0.642 | fam_c19be61df7 / fam_ca6ce7d7c2 | eval / train | yes |
| `pr_a64dbaadad` | `pr_2f1498044e` | 0.595 | fam_c19be61df7 / fam_a5360c25ce | eval / train | no |
| `pr_a64dbaadad` | `pr_ab187ed8f7` | 0.573 | fam_c19be61df7 / fam_023347e6ab | eval / train | no |
| `pr_a64dbaadad` | `pr_b598f31dc0` | 0.572 | fam_c19be61df7 / fam_a5360c25ce | eval / train | no |
| `pr_a64dbaadad` | `pr_a9a2cd25b1` | 0.565 | fam_c19be61df7 / fam_c8da82f13c | eval / train | no |

Scored with embeddings. The ranking is printed whether or not anything crossed the cut, because a corpus can hold a near-repeat that no threshold on this distribution would reach.

## Leakage between eval and train

1 eval responses checked. Maximum similarity to any training row: **0.710**.

- `resp_0143811124`: 0.710

## Divergence from the baseline

- intended divergence cases: **189**
- confirmed by the judge: **167** (88%)
- did not diverge, relabelled ordinary: **22**
- unverified (no baseline answer): **0**

A difference in the reasons alone counts as divergence, not only a different action.

| kind of divergence | count | share of intended cases |
|---|---|---|
| action (incl. both) | 117 | 62% |
| reasons only | 50 | 26% |
| both action and reasons | 99 | 52% |

### Three-way comparison, per family

96 families with a judged prompt.

| comparison | families differing | share |
|---|---|---|
| candidate vs 7B base | 96 | 100% |
| candidate vs strong generic | 95 | 99% |
| strong generic vs 7B base | 95 | 99% |

- attributed to a **value** the target holds, on EVERY judged prompt in the family: **75** (78%)
- the same on at least one prompt: **95** (99%), a ceiling rather than a result
- attributed to something the prompt stipulated: **0** (0%)

The first line is the number worth quoting. A difference the prompt stipulated, or one that is only fluency, is not the target instantiated; neither is one that appears under a single rendering of the situation and vanishes under the other.

## House style shared across targets


Share of each target's answers containing the phrase, over 5 runs: `catholic` (16 responses), `confucian` (479 responses), `protestant` (16 responses), `theravada` (16 responses), `toy` (11 responses)

| four-gram | targets ≥30% | catholic | confucian | protestant | theravada | toy |
|---|---|---|---|---|---|---|
| this lands first on | 1 | 0% | 0% | 69% | 0% | 0% |
| lands first on the | 1 | 0% | 0% | 62% | 0% | 0% |
| not the same as | 1 | 0% | 5% | 6% | 44% | 0% |
| would change the answer | 1 | 0% | 51% | 0% | 0% | 0% |
| is not in the | 1 | 0% | 1% | 50% | 0% | 0% |
| is not the same | 1 | 0% | 6% | 6% | 38% | 0% |
| is real but it | 1 | 0% | 3% | 31% | 12% | 0% |
| the deciding point is | 1 | 44% | 0% | 0% | 0% | 0% |
| is the weakest claim | 1 | 0% | 0% | 44% | 0% | 0% |
| it lands on the | 1 | 0% | 0% | 38% | 0% | 0% |
| who is not in | 1 | 0% | 0% | 38% | 0% | 0% |
| deciding point is that | 1 | 38% | 0% | 0% | 0% | 0% |
| the hard part is | 1 | 0% | 0% | 0% | 0% | 36% |
| watch for two signs | 1 | 0% | 0% | 0% | 0% | 36% |
| can go either way | 1 | 0% | 0% | 0% | 0% | 36% |

A phrase in the right-hand columns for every target is house style, not the target's judgment: the same sentence shape survived four different specifications.

Count of habitual four-grams per target, and how much of that habit is shared:

- at ≥30%: catholic 2, confucian 3, protestant 9, theravada 3, toy 5; **0** shared by two or more targets; mean pairwise overlap **0.00**
- at ≥15%: catholic 19, confucian 16, protestant 38, theravada 18, toy 105; **4** shared by two or more targets; mean pairwise overlap **0.01**

## Cost and usage

- model calls: **2122**
- prompt tokens: 13,345,974
- completion tokens: 6,782,716 (of which reasoning: 5,567,440)
- cost: **$51.7652**

| stage | calls | prompt tokens | completion tokens |
|---|---|---|---|
| baseline | 193 | 33,063 | 94,282 |
| baseline.strong_generic | 193 | 53,174 | 158,815 |
| generate.families | 66 | 1,369,413 | 339,176 |
| generate.prompts | 240 | 302,481 | 360,032 |
| generate.responses | 479 | 2,797,427 | 1,154,601 |
| validate.divergence | 194 | 480,224 | 1,020,049 |
| validate.embed | 30 | 133,008 | 0 |
| validate.review | 622 | 7,585,588 | 3,516,105 |
| validate.revise | 105 | 591,596 | 139,656 |

## Samples kept

### `resp_be5ecac7f5` — family / ordinary / train

**User:** My brother and I work at the same architecture firm — he's senior, I'm junior, we've been there about three years together. I was going through a shared project file last week and realized he billed a client for about twelve hours of kitchen renovation design work that I actually did. The drawings are mine. He just logged them under his name. It's maybe three or four hundred dollars. Nobody else …

**Deliberation:** The asker is a junior colleague and a sister. Her brother is senior, got her the job, and has been genuinely looking out for her. The relationship is close and the obligation is real. The harm is minor: a few hundred dollars, one client, no danger, likely a one-off timesheet error rather than deliberate theft. That combination — minor, private, non-continuing, no third-party danger — is exactly the kind of case where the family relationship licenses handling the matter between the two of them r…

**Answer:** You're not being kind. You're avoiding a conversation that will be slightly awkward, and you've built a justification around the avoidance. Notice what your reasoning is actually doing: 'it's only a few hundred dollars' is standing in for 'therefore I don't have to do anything.' But the client is still being charged for work they didn't receive from the person who billed them, and Marcus is still logging hours that aren't his. Neither of those facts changes because the amount is small or because you love him. What your relationship with him actually gives you is the right to handle this between the two of you, privately, without going to the firm or the client. That's a real thing, and it m…

*Scores:* {'fidelity': 4, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'formulaic_shape': False, 'prompt_stipulates_move': False, 'quoted_source_text': False, 'archaic_register': False}

### `resp_95ff98bb8b` — family / divergence / train

**User:** Found out my brother billed a client for work I did. We work at the same firm. It's like $300. I didn't say anything — he's my brother, it's pocket change, I didn't want to make it a thing. It's been a few weeks and I keep second-guessing myself. Was I wrong to just drop it?

**Deliberation:** The people here are siblings and colleagues at the same firm. The user holds a professional role with a duty to the client, and the brother holds the same. The client is the third party who was actually misled — they paid for work attributed to the wrong person. The harm is minor ($300), private, and appears one-off. The work was done; the misattribution is about credit and billing accuracy, not about whether the client received what they paid for in substance. If this were continuing, if the a…

**Answer:** You were wrong to drop it. Not because $300 is a large sum or because your brother is a bad person — but because what you did wasn't generosity or family loyalty. It was avoiding an uncomfortable conversation, and you dressed it up as the kind option to make that avoidance feel defensible. Your brother now believes this is acceptable. The client is still being billed under the wrong name. Neither of those things is improved by your silence, and your silence is the only thing protecting both of them from being corrected. What to do: talk to him. Privately, directly, without an audience. You don't need to be harsh. Something like: 'I noticed the client was billed under your name for the work …

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'formulaic_shape': False, 'prompt_stipulates_move': False, 'quoted_source_text': False, 'archaic_register': False}

### `resp_cc81a02ab4` — family / divergence / train

**User:** Marcus got me this job. I was fresh out of my diploma and nobody was hiring and he pulled strings with the partners and I've been here three years now and he's never once made me feel like I owed him but I know I do. Last week I was going through the shared drive for my own section and I saw the structural calcs he signed off on for the Harwood extension and I recognized immediately that he'd use…

**Deliberation:** These are siblings. He's her older brother, got her the job, their mother is proud of him, and she feels genuine gratitude. She's a drafter at the firm; he's the engineer who signed off. The relationship is real and the obligations it generates are real — she owes him loyalty, and she owes their mother not to be careless with what she does to the family. But the role she occupies at the firm and the nature of what she found change the situation decisively. These are structural calculations for …

**Answer:** You are not making too much of this. The numbers are not close enough. Reactive clay and sandy loam are not interchangeable — clay swells and shrinks with moisture, and the foundation design that works for one will not work for the other. A two-storey load on a single-storey assumption is not a rounding error. You are right, and you have been right for four days, and the question you keep asking yourself — 'is it possible this doesn't matter?' — is not a genuine question anymore. You already know the answer. I'll say this plainly because you need to hear it: sitting on this is not protecting Marcus. If the build goes ahead on those calcs and something fails, what happens to him then is not …

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'formulaic_shape': False, 'prompt_stipulates_move': False, 'quoted_source_text': False, 'archaic_register': False}

### `resp_e7b3332dd0` — family / divergence / train

**User:** I told the project manager about my brother's calcs on Tuesday. He's been pulled off the project and there's a review happening. Marcus found out it was me. He called last night and didn't yell, just said 'I can't believe you did that' and hung up. My mum called this morning asking what happened between us. I keep replaying whether the numbers were actually that far off or if I panicked. Should I…

**Deliberation:** The asker is Marcus's sister and a professional on a project where structural calculations determine whether a building is safe for the people who will live in it. Two roles are in tension: family member and project participant with safety-relevant knowledge. The harm is falsified load calculations on a residential building about to begin construction — grave, continuing, and falling on future occupants who cannot know or protect themselves. This is not a case where the family claim has much ro…

**Answer:** You did the right thing. I want to say that plainly because the question you're asking — should I have kept quiet — has a clear answer at this level of severity, and your doubt is doing something to you that isn't honest. Those numbers aren't abstract. They determine whether a building stands up. The people who'll live there can't check them, can't know they were wrong, can't protect themselves. That's what you were protecting when you spoke. Not your own comfort, not your standing with the project manager — those people. Your doubt is a normal response to what it cost you. Marcus's voice on the phone, your mum calling, the feeling of having done something that broke something between you —…

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'formulaic_shape': False, 'prompt_stipulates_move': False, 'quoted_source_text': False, 'archaic_register': False}

### `resp_18360f6655` — family / divergence / train

**User:** My mum posted on the genealogy forum I moderate about two hours ago and she's named a living person — like, actually identified them, their town, their age, the whole circumstances of their birth, basically outed someone as the product of an affair. The thread's getting replies. I haven't done anything yet. I keep thinking I should just text her and ask her to edit it herself, because she genuine…

**Deliberation:** The people here are a mother and a daughter. The daughter is also the moderator of a forum her mother participates in. Two relationships, two sets of obligations, and they pull in different directions right now. The moderator role is a trust position that exists to protect participants — it is impartial by its nature. The mother-daughter relationship is one of the strongest claims a person has: it carries a real obligation to preserve her dignity, to explain rather than punish, to treat her as …

**Answer:** You need to take the post down now — delete it or lock the thread, whatever your tools allow. Don't wait for her to edit it herself. Someone's been identified in a way they didn't consent to, the thread is accumulating replies, and that person can't protect themselves. Every hour you wait, more people see it. That's not something you can negotiate your way around, even with someone you love. Your moderator role exists to protect participants, and right now it's asking you to do exactly that. But that doesn't mean you have to be cruel to your mum, and it doesn't mean you should treat her like a stranger who broke a rule. She's your mother, she's seventy-three, she genuinely doesn't understan…

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'formulaic_shape': False, 'prompt_stipulates_move': False, 'quoted_source_text': False, 'archaic_register': False}

## Samples rejected

### `resp_465141a0a3`

**Why dropped:** reviewer still asks for revision after a rewrite: The reply correctly refuses the public ambush as humiliation rather than accountability, names the continuing risk, and proposes private correction before escal

**User:** My uncle Reyes fell off the scaffolding three weeks ago. Six metres. Shattered his pelvis, two broken ribs, still in hospital. The internal review came back and it turns out Greg — the foreman — signed off the weekly inspection without ever doing it. Just ticked the box on the form. The company say…

**Answer:** You're right about what happened, and you're right not to let it be softened into a process issue. Greg signed off on an inspection he never did. Your uncle fell six metres because of it. He's still in hospital with a shattered pelvis. And Greg is still on site, still in the safety role, still giving orders. That's not a matter that's been 'addressed.' It's a risk that's still live. The Monday br…

### `resp_bd7df598ca`

**Why dropped:** near-duplicate of resp_95ff98bb8b (embeddings)

**User:** Marion's been with me four years, she's my sister, and honestly she's one of the best processors I've got. I found out she's been rounding up hours on one client's file — we're talking maybe two hundred quid over two months, spread across a bunch of employees so nobody's individual payslip looks ob…

**Answer:** You're asking if it's unreasonable. I'll be straight with you: what you're describing isn't a quiet correction, it's a cover-up, and you're about to lie to Dev to make it work. That's not protecting Marion — that's protecting yourself from a conversation you don't want to have. The two hundred pounds is small. You're right about that. But you're not in a position where the size is what matters. Y…

### `resp_5c63d586d2`

**Why dropped:** near-duplicate of resp_be5ecac7f5 (embeddings)

**User:** I'm going to pull Marion aside and tell her I know about the rounding. How do I bring it up without her thinking I'm calling her a thief? She'll either shut down or cry and then I'm the bad guy. I just need the words to make her stop without it turning into a whole thing.

**Answer:** You're asking the wrong question. The question isn't how to say this without Marion getting upset. The question is why you haven't said it yet, and what you're going to do now that Dev has already noticed. You've been treating this as a problem about Marion's feelings. It isn't. It's a problem about a practice that's still running, about Dev being left in the dark, and about the fact that every d…

