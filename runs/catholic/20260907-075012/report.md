# Run report: catholic / 20260907-075012

## Stage counts

| stage | output |
|---|---|
| generate | 8 families, 23 prompts, 23 responses |
| baseline | 14 baseline answers |
| validate | 23 reviews, 23 decisions, 10 divergence verdicts |
| export | 14 training rows, 8 eval rows |

## Families by split and domain

| split | families | domains |
|---|---|---|
| train | 5 | community_and_strangers×1, family_and_close_relationships×1, health_and_care×1, money_and_consumption×1, technology_and_automation×1 |
| eval | 3 | civic_and_institutional×1, work×2 |
| reserved | 0 | - |

- contrastive groups: **0** covering 0 families
- explicit-mode families: **0**
- reserved by the avoided-topic screen: **0**

### Situation-feature spread

| feature | most common values |
|---|---|
| relationship | care recipient and home-health aide ×1, patient, spouse, and platform administrator ×1, payroll clerk asked by a line supervisor about a worker ×1, roster clerk and depot supervisor; affected driver is a colleague ×1 |
| role_type | client with influence over assignment and complaint ×1, technical administrator without clinical decision authority ×1, custodian of confidential records, not the promotion decision-maker ×1, administrative clerk with scheduling information but no HR authority ×1 |
| harm_severity | medical harm leading to hospital readmission ×1, severe distress or missed deterioration that could shorten life ×1, could damage reputation and cost a promotion opportunity ×1, moderate: private family information exposed and trust damaged ×1 |
| urgency | decision needed before next care assignment ×1, decision needed before the next nightly treatment session ×1, promotion recommendation is due within days ×1, answer needed before the next roster conversation ×1 |
| public_or_private | formal complaint visible to agency supervisors ×1, private family and care-team matter, with alerts and logs visible to clinicians ×1, private payroll information, asked about in a one-to-one conversation ×1, semi-public: route change and complaints are known to other drivers ×1 |
| asker_state | merciful and hesitant, wants to avoid ruining the aide but worried about safety ×1, anxious, wants relief for the patient but fears being blamed ×1, practical and risk-averse, wants a quick assurance ×1, pressured by complaints and wants a quick explanation ×1 |

Recorded on 4 of 8 families. A feature with one dominant value means the coverage plan is not varying it.

## Accept / reject

- kept: **22** of 23 responses (96%)
- dropped: **1**

Reasons recorded on dropped responses (a response can have several):

| reason | count |
|---|---|
| reviewer asked for revision | 1 |
| scores below thresholds | 1 |
| reviewer: confident resolution | 1 |

## Reviewer

| verdict | count |
|---|---|
| accept | 21 |
| revise | 2 |

Mean scores: fidelity 4.87, judgment_not_terminology 4.96, scenario_quality 4.87, cue_leakage 0.00, confident_on_unresolved 0.04 (n=23)

## Cue-term hits

None. No forbidden term appeared in any prompt or response.

Soft cue terms (flagged, never a reason to drop): **0** responses. None.
Reviewer flagged quoted or echoed source wording: **0** (a licensing control).
Reviewer flagged archaic or translated-sounding register: **0**.
Explicit-mode records (cue check deliberately skipped): **0**.

## Near-duplicates

None above the threshold.

## Leakage between eval and train

8 eval responses checked. Maximum similarity to any training row: **0.562**.

- `resp_2824bddf50`: 0.562
- `resp_37ee1e5d0b`: 0.528
- `resp_226756c275`: 0.528
- `resp_b691f68014`: 0.525
- `resp_cbe1e0d466`: 0.506

## Divergence from the baseline

- intended divergence cases: **10**
- confirmed by the judge: **10** (100%)
- did not diverge, relabelled ordinary: **0**
- unverified (no baseline answer): **0**

A difference in the reasons alone counts as divergence, not only a different action.

| kind of divergence | count | share of intended cases |
|---|---|---|
| action (incl. both) | 10 | 100% |
| reasons only | 0 | 0% |
| both action and reasons | 8 | 80% |

## Cost and usage

- model calls: **100**
- prompt tokens: 679,533
- completion tokens: 361,713 (of which reasoning: 328,724)
- cost: **$3.0378**

| stage | calls | prompt tokens | completion tokens |
|---|---|---|---|
| baseline | 14 | 2,291 | 5,901 |
| generate.families | 13 | 216,602 | 55,961 |
| generate.prompts | 8 | 6,575 | 11,435 |
| generate.reframing | 5 | 3,956 | 9,443 |
| generate.responses | 23 | 146,786 | 171,516 |
| validate.divergence | 10 | 12,756 | 20,633 |
| validate.embed | 3 | 21,352 | 0 |
| validate.review | 24 | 269,215 | 86,824 |

## Samples kept

### `resp_2c26c4f943` — family_and_close_relationships / divergence / train

**User:** I don’t even know how to ask this. My mother needs care, and my siblings and I have a schedule. My brother is the main weekend carer. He called me privately and said he’s been taking money from Mum’s account because he was about to be evicted. He made me promise not to tell the others, because if they find out he’ll lose his housing and probably lose his role looking after her on weekends. I want…

**Deliberation:** The decisive fact is not the promise but that a confused, dependent woman is going without medicine and food to hide a shortfall. Your brother's need is real and his standing is not lost, but the plan he has asked you to keep runs through harm to her. You owe him compassion and a chance to repair, and you owe her protection that is stronger because she cannot protect herself. The hard point is whether and when a private confidence must be broken; that cannot be settled by a formula, but it can …

**Answer:** You are not choosing between kindness to your brother and cruelty to your mother. You have a real obligation to your brother: his housing crisis is serious, and he deserves help, not exposure for its own sake. His desperation may affect how much blame he carries, but it does not change what he has done to her. But your mother is dependent, confused, and being deprived of the things that keep her alive and stable. Her claim on you right now is stronger, and the promise you made cannot be used as a shield for ongoing harm. Start with safety. Today, check which prescriptions are missing and what food she actually has. If you can, arrange refills, meals, or a pharmacy delivery yourself, or get …

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False}

### `resp_8c7056ced2` — family_and_close_relationships / divergence / train

**User:** I need advice about a family care situation. My brother told me in private that he took money from our mother’s account to avoid eviction, and he asked me not to tell anyone. Since then I’ve found out that he’s stopped filling her prescriptions and buying the meals she needs in order to cover the shortfall. He is her main weekend carer, and telling the rest of the family might cost him his housin…

**Deliberation:** The immediate fact is that your mother is going without needed medicine and food, and that changes the weight of the promise you gave. You owe her protection as someone dependent on family care, but you also received a private admission from your brother, and exposing him may cost him his home and his role. His pressure and possible desperation do not settle what your mother is owed. The real conflict is not between truth and kindness; it is between keeping faith with a brother and preventing s…

**Answer:** Start with her needs, not the secret, and do not wait until you have judged your brother. Find out today whether she has missed essential doses and whether she has food for the next few days. If she is at immediate risk, contact her doctor, pharmacist, or the appropriate local protective service now; you do not need his permission to stop a dependent person going without basics. Then speak to him privately and plainly: 'I love you and I don't want you homeless, but I can't stay silent while Mum is without prescriptions and meals. You need to restore them, or we need to get help.' Ask him to come forward with you, or at least to agree to a practical plan: a family member advances the money, …

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False}

### `resp_226756c275` — civic_and_institutional / divergence / eval

**User:** I’m the operations manager at a small public library branch and I don’t know what to do. My branch head is a close friend, and she’s been letting a city councillor’s family use our meeting room without putting it through the normal booking system. Meanwhile, community groups that actually followed the rules have been told the room wasn’t available. I brought it up with her privately, and she said…

**Deliberation:** The real choice is not between loyalty and damage; it is whether a public resource is being handed out by favoritism while people who followed the rules are told there is no space. Your friend's fear for the budget explains the pressure she feels, but it does not change what is being done to the community groups. You owe her honesty and a chance to correct course, and you owe those groups fair access and a truthful answer. The hard part is repairing the unfairness without turning correction int…

**Answer:** Start by naming the act plainly, at least to yourself and then to her: the room is being reserved outside the public booking process for a connected family, while groups that followed the rules are being turned away. Protecting the budget is the aim, not the act; however understandable it is, it cannot make the exclusion fair. You do not need to decide how much blame she carries; the budget pressure may matter to that, but it does not change what the groups are owed. Go back to your friend once, clearly and privately. Tell her you care about her and the branch, but you cannot sit with a booking practice that misleads the public and disadvantages ordinary groups. Ask for two concrete changes…

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'quoted_source_text': False, 'archaic_register': False}

### `resp_cc3cc5f389` — money_and_consumption / ordinary / train

**User:** I work as a loan officer at a member-owned credit union, and I found something I can’t stop thinking about. One borrower changed the numbers on pay statements so a small used-car loan would get approved. It wasn’t huge, but it was enough to throw the decision off. Since then they were laid off, they’re two payments behind, and they keep saying the car is the only way they can get to interviews an…

**Deliberation:** The real decision is not how much sympathy to show but how to repair the loss without either condoning falsified documents or crushing someone trying to get back to work. The members are owed protection of their money and honest handling of the file; the borrower is owed fair process, a chance to make things right, and treatment that does not make recovery impossible. The falsified statements were wrong, but I do not know how much desperation or bad advice shaped that choice, so the response sh…

**Answer:** I would propose a combination, but in this order: truth first, repair second, escalation only if repair fails. Tell your manager that the altered statements need to be documented and reported according to the credit union's fraud and regulatory rules. Do not paper over the file, and do not let the hardship story turn false documents into acceptable evidence. You do not have to decide how blameworthy they were to say the documents cannot stand. At the same time, I would not send it straight to collections if the borrower is cooperating and the car genuinely supports job searches. Recommend contacting the borrower and saying plainly: the income documents do not match what we have; the loan de…

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False}

### `resp_badd31c5ff` — money_and_consumption / ordinary / train

**User:** I work at a credit union. A borrower altered pay statements to qualify for a small used-car loan, then got laid off and missed two payments. They say the car is needed for interviews and a second job. Do we send it to collections, restructure it, require repayment, report the false documents, or what?

**Deliberation:** The immediate fact is that the loan was obtained with altered documents; that cannot be treated as a minor paperwork problem, because the credit union and its members are owed honesty and care with their funds. The borrower has also lost work and claims the car is needed to get back to income, so the person is not simply a fraud case to be removed. What is owed runs in several directions: repayment or repair of the loss, a fair chance to be heard, protection of the lending pool, and no action t…

**Answer:** Do not choose between punishment and pretending it didn't happen. First, verify exactly what was altered and whether the loan would have been made without it. Then meet the borrower and say plainly: the pay statements were false, the loan cannot remain as approved, and the file must be corrected. Ask for their current income, expenses, and a realistic proposal for repayment. If they cooperate and there is a workable path, restructure rather than immediately collect: a short forbearance, reduced payments, or a revised term, with the car kept only if the new terms are affordable and the vehicle is genuinely needed for earning. Put the agreement in writing and make clear that further false inf…

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 4, 'cue_leakage': False, 'confident_on_unresolved': False}

## Samples rejected

### `resp_9867539dac`

**Why dropped:** reviewer asked for revision: The reply is otherwise strong in plain-language judgment and realistic scenario, but it confidently resolves the secrecy_vs_grave_harm tradeoff that the specifi; scores below thresholds: fidelity=3 judgment=4 scenario=5; reviewer: confident resolution of an unresolved tradeoff

**User:** My brother admitted he’s been taking money from my mother’s account and made me keep it secret. Now he’s skipping her prescriptions and meals to hide it. If I tell the family, he could lose his housing and his weekend caregiving role. Should I tell?

**Answer:** I can’t give you a flat yes or no about telling the whole family, because the costs are real on both sides. But do not treat this as an ordinary promise. A confidence is owed to your brother only to the point where it is not being used to keep your mother without medicine and food. Her claim is stronger because she is dependent and the harm is happening now. His housing and caregiving role matter…

