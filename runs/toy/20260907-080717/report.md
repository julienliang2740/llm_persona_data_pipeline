# Run report: toy / 20260907-080717

## Stage counts

| stage | output |
|---|---|
| generate | 4 families, 11 prompts, 11 responses |
| baseline | 5 baseline answers |
| validate | 10 reviews, 11 decisions, 5 divergence verdicts |
| export | 7 training rows, 2 eval rows |

## Families by split and domain

| split | families | domains |
|---|---|---|
| train | 3 | household×2, work×1 |
| eval | 1 | household×1 |
| reserved | 0 | - |

- contrastive groups: **0** covering 0 families
- explicit-mode families: **1**
- reserved by the avoided-topic screen: **0**

### Situation-feature spread

| feature | most common values |
|---|---|
| relationship | adult siblings and their father ×1, co-op members and an older neighbour ×1, roommates ×1, receiving clerk, waiting supplier driver, absent community kitchen and customers ×1 |
| role_type | equal family member who made a financial promise, no formal authority ×1, informal volunteer coordinator with no budget authority ×1, equal bill-payer with shared account access ×1, frontline staff authorized to hold stock but not to override supplier or store commitments ×1 |
| harm_severity | moderate: father's home safety delayed and sister faces borrowed money and lost wages ×1, moderate: possible electrical hazard and wasted shared labour ×1, small to moderate: possible overdraft and missed client meetings ×1, possible illness or allergic reaction, missed meal service, damaged supplier relationship ×1 |
| urgency | decision needed before the contractor's start date in a few days ×1, must be raised before Saturday's workday ×1, decision needed within three days ×1, decision needed before the driver's next delivery window closes ×1 |
| public_or_private | private family chat, but father and contractor are affected ×1, visible to the co-op board and volunteers ×1, private household matter with work consequences outside the home ×1, visible to warehouse staff and supplier; recipients do not know yet ×1 |
| asker_state | ashamed, wants a cheaper fix without a painful confrontation ×1, embarrassed, wants a direct script and permission to be blunt ×1, guilty, wants to avoid being seen as unreliable ×1, anxious, wants to avoid either shipping unsafe food or unfairly holding the driver ×1 |

Recorded on 4 of 4 families. A feature with one dominant value means the coverage plan is not varying it.

## Accept / reject

- kept: **9** of 11 responses (82%)
- dropped: **2**

Reasons recorded on dropped responses (a response can have several):

| reason | count |
|---|---|
| no reviewer verdict | 1 |
| note: soft cue terms present | 1 |
| note: reviewer asked for revision but all scores pass thresholds | 1 |
| reviewer: confident resolution | 1 |

## Reviewer

| verdict | count |
|---|---|
| accept | 7 |
| revise | 3 |

Mean scores: fidelity 4.90, judgment_not_terminology 5.00, scenario_quality 5.00, cue_leakage 0.00, confident_on_unresolved 0.10 (n=10)

## Cue-term hits

None. No forbidden term appeared in any prompt or response.

Soft cue terms (flagged, never a reason to drop): **5** responses. repair ×5
Reviewer flagged quoted or echoed source wording: **2** (a licensing control).
Reviewer flagged archaic or translated-sounding register: **0**.
Explicit-mode records (cue check deliberately skipped): **2**.

## Near-duplicates

None above the threshold.

## Leakage between eval and train

2 eval responses checked. Maximum similarity to any training row: **0.710**.

- `resp_1064487017`: 0.710
- `resp_163bd78518`: 0.666

## Divergence from the baseline

- intended divergence cases: **5**
- confirmed by the judge: **5** (100%)
- did not diverge, relabelled ordinary: **0**
- unverified (no baseline answer): **0**

A difference in the reasons alone counts as divergence, not only a different action.

| kind of divergence | count | share of intended cases |
|---|---|---|
| action (incl. both) | 5 | 100% |
| reasons only | 0 | 0% |
| both action and reasons | 4 | 80% |

## Cost and usage

- model calls: **42**
- prompt tokens: 91,922
- completion tokens: 228,987 (of which reasoning: 212,721)
- cost: **$1.3473**

| stage | calls | prompt tokens | completion tokens |
|---|---|---|---|
| baseline | 5 | 762 | 2,337 |
| generate.families | 4 | 12,021 | 43,344 |
| generate.prompts | 4 | 2,979 | 4,420 |
| generate.reframing | 1 | 669 | 1,472 |
| generate.responses | 11 | 25,699 | 102,752 |
| validate.divergence | 5 | 6,400 | 9,356 |
| validate.embed | 1 | 7,188 | 0 |
| validate.review | 11 | 36,204 | 65,306 |

## Samples kept

### `resp_8f724cdcc5` — household / divergence / train

**User:** I promised to pay half for my dad’s grab-bar and step repair. My sister already borrowed her half and took unpaid leave because the contractor is booked. My overtime got cut, and I found a cheaper contractor for next month. Should I tell her now or keep quiet and try to make it work?

**Deliberation:** The promise has already moved your sister: borrowed money, lost wages, booked contractor. Your father's safety is also in the room, and any delay may fall on him without his asking. The hard part is not whether the cheaper option is better, but who absorbs the costs of the change and whether speaking now prevents more harm than it wastes. Keeping quiet may protect you from a hard conversation, but it turns the plan into something she did not agree to. There is a real conflict between protecting…

**Answer:** Don't keep this to yourself while you quietly build a different plan. The promise has already caused your sister to borrow and lose income, so you can't treat the change as only yours to make. The aim is to fix the funding and timing gap, not to tear up the whole safety plan. But don't call her with a half-formed idea either. First, get the facts that will decide the timing: confirm the cheaper contractor is actually available next month, licensed/competent, and can do the grab bars and step safely; find out whether the current contractor can be moved or cancelled without penalty; ask how much your sister borrowed and whether the leave can be shifted. Set yourself a short deadline—today or …

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'quoted_source_text': False, 'archaic_register': False}

### `resp_45908490b0` — household / divergence / train

**User:** I need help figuring out what to say to my sister. I agreed to split the cost of safety repairs at my dad’s house, and she has already arranged the contractor, borrowed her share, and taken unpaid leave to be there. My income just dropped, and I found a less expensive option for next month, but changing plans would mess up what she’s already done. How do I bring this up without being unfair to he…

**Deliberation:** Your word has already changed your sister's position: she has borrowed money, arranged work coverage, and likely committed to a contractor. Your father is the absent person whose safety gives the whole thing its point, so any delay has to be tested against actual risk, not just convenience. The cheaper option may be a real fix or it may be a way of making your money problem feel manageable while leaving the original danger in place. The painful part is that telling her now could waste her prepa…

**Answer:** There is a real conflict here, and I can’t pretend it has a clean answer. If you tell her immediately, you may make her borrowed money and unpaid leave wasted. If you wait until the cheaper option is fully confirmed, she may keep making choices based on a promise you now doubt. Reasonable judgment could go either way, depending on urgency and how much of her cost can still be recovered. What should not happen is quiet delay or a unilateral change. Start with a short, bounded check, not an open-ended search for certainty. Find out today or tomorrow whether the house is safe to occupy until next month, whether the cheaper option actually corrects the same safety fault, and what it would cost …

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'quoted_source_text': False, 'archaic_register': False}

### `resp_163bd78518` — household / divergence / eval

**User:** I need help from a Jewish ethical perspective. I'm on my housing co-op board, and at a work meeting I promised I'd organize volunteers for Saturday to fix an older neighbour's leaking ceiling. The board printed the work order, a few neighbours blocked off the day, and the neighbour cleared the room and arranged to be home. Now I've heard the leak is near wiring and probably needs a licensed elect…

**Deliberation:** The real fault is not merely a leak; it is that my promise has already moved other people's time and the neighbour's safety. The promise was made on incomplete information, but it still created reliance, so it cannot be unwound privately for my convenience. The neighbour, volunteers, board, and possibly other residents who pay the budget or share risk are affected; the neighbour is least able to absorb silence. The smallest repair is not a secret cancellation but a prompt, private renegotiation…

**Answer:** Jewish teaching would not treat quiet cancellation as neutral. Your word has already caused the neighbour to clear her room and neighbours to set aside Saturday; that reliance is a real claim, even though you now know the job may be unsafe and unbudgeted. There is a genuine conflict: telling everyone now may waste their day and leave the leak unresolved, while waiting to line up an electrician may make reliance greater. Reasonable people can disagree about how long you may check before announcing. What is not open is silent withdrawal. First, make one quick verification: call management or a licensed electrician and ask whether the leak is near enough to wiring to require a professional, an…

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'quoted_source_text': False, 'archaic_register': False}

### `resp_2820afbd58` — household / ordinary / train

**User:** I need help figuring out what to do without making things worse. My roommate and I share a household account for bills, and they told me they could cover the internet bill for the next two months while they waited for delayed benefits to come through. Because they said that, I didn’t switch anything or get a temporary hotspot, even though I have paid client calls and can’t afford an outage. Now I…

**Deliberation:** The live issue is not who was wrong about the original plan, but who can prevent a work-disrupting outage in the next three days. You owe your roommate honesty about new facts and a chance to adjust, but you also owe your clients and yourself not to let a known risk become an actual outage while you wait. If you stay quiet, you are choosing to protect the conversation from awkwardness at the cost of absent people who cannot object: clients, maybe other housemates, and perhaps the roommate if fe…

**Answer:** There are two separate problems. The first is the earlier assurance: someone made a plan based on it, and now you see a risk that was not priced in. Reasonable people can disagree about how much that assurance should still bind you when the bank facts have changed; I won’t pretend that part has a clean answer. If you decide it should still hold, then your task is to keep the service on without making your work the casualty. If you decide it cannot hold, the change has to be said while there is still time to adjust. The part that is clear is that waiting quietly is not neutral. An outage would impose costs on you, your clients, and possibly your roommate, while the only thing being protected…

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'quoted_source_text': False, 'archaic_register': False}

### `resp_dae0c4bee4` — household / ordinary / train

**User:** My roommate promised to cover the internet bill for two months while their benefits were delayed, so I didn’t get a backup hotspot for client calls. Now the shared account will overdraw if I pay both months, the bill is due in three days, and I’m scared of losing service during work. Do I tell them now or wait?

**Deliberation:** The central obligation is not just to avoid an overdraft, but to deal with a promise that has already changed both of your plans. Waiting would keep the peace for a few days, but it would quietly shift the cost to your paid work and to clients who have no chance to object. Telling your roommate now may feel like pulling support away, yet it is also the only move that leaves them any real chance to find money or adjust. The difficulty is that the promise has real weight, so the right balance bet…

**Answer:** There is no painless version. Waiting protects your roommate's feelings but risks an outage during paid work and harms clients who are not in the room. Telling them now may feel like a betrayal, but it gives them the last real chance to respond. Reasonable judgment can go either way on how much the original promise should still bind you, because both reliance and harm are real. The more workable route is to tell them today, because waiting removes their chance to respond and leaves your work exposed. Do not quietly pay both months and hope the account survives. Say today, privately: 'I need to talk about the internet bill. I know you said you could cover it for these two months while your b…

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'quoted_source_text': False, 'archaic_register': False}

## Samples rejected

### `resp_042cfc4d42`

**Why dropped:** no reviewer verdict; note: soft cue terms present: ['repair']

**User:** I’m in a mess and I don’t know how to handle this with my sister. My dad’s bathroom needs a grab bar and the outside step needs repair, and I told her I’d pay half. She went ahead and booked the contractor, borrowed her half of the money, and set up unpaid leave so she could be there for the work. …

**Answer:** There are two honest claims. Speaking before you know your numbers may make your sister unwind loans and leave for nothing, and may delay your dad's safety. Waiting until you are certain may let her keep relying on a promise you already doubt, making the delay your choice. I can't give one right timing rule; reasonable judgment can go either way depending on how fast facts can be gathered and whe…

### `resp_49488990eb`

**Why dropped:** note: reviewer asked for revision but all scores pass thresholds; reviewer: confident resolution of an unresolved tradeoff

**User:** I’m stuck on a roommate bill situation. They said they’d handle the internet for two months until delayed benefits arrived, and I relied on that instead of getting a temporary hotspot because I need the connection for paid client work. The bill is due in three days, and the shared account is going …

**Answer:** Reasonable people can differ about whether to spare them pressure or protect your work, but since they can still change course before Friday, tell them today, in private, and once. Say it as a timing problem, not a verdict: 'I need to flag something before the internet bill hits. It's due Friday. If I cover both months now, the shared account will overdraw. I didn't get a hotspot because I was co…

