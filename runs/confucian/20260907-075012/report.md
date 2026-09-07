# Run report: confucian / 20260907-075012

## Stage counts

| stage | output |
|---|---|
| generate | 8 families, 22 prompts, 22 responses |
| baseline | 16 baseline answers |
| validate | 21 reviews, 22 decisions, 9 divergence verdicts |
| export | 14 training rows, 7 eval rows |

## Families by split and domain

| split | families | domains |
|---|---|---|
| train | 5 | advice_and_correction×2, interpersonal_conflict×1, learning_and_self_cultivation×1, work×1 |
| eval | 3 | family×1, work×2 |
| reserved | 0 | - |

- contrastive groups: **0** covering 0 families
- explicit-mode families: **0**
- reserved by the avoided-topic screen: **0**

### Situation-feature spread

| feature | most common values |
|---|---|
| relationship | long-standing mentor and driver, now applicant ×1, trainer and apprentice ×1, siblings; asker is executor, brother is former agent under a power of attorney and a beneficiary ×1, line manager and direct report ×1 |
| role_type | holds formal authority over an initial hiring ranking ×1, holds assessment authority ×1, holds fiduciary authority over estate records and distribution ×1, holds formal authority over performance review and scheduling ×1 |
| harm_severity | moderate: an unfair appointment, loss of opportunity for another applicant, and damage to trust in the process ×1, risk of physical injury to coworkers if unsafe practice is certified ×1, moderate financial loss and breach of trust affecting another sibling's needed reimbursement ×1, customer trust damaged and employee may lose job or pay; no physical harm ×1 |
| urgency | written ranking due tomorrow ×1, sign-off needed before the certification cohort closes ×1, decision needed before the estate accounting is certified, likely within weeks ×1, decision expected within a week ×1 |
| public_or_private | private request, but the decision affects a committee and other candidates ×1, the observed lapse was private, but the certification will affect the whole shift ×1, private family dispute, but tied to a formal legal accounting owed to beneficiaries ×1, visible to customers, HR, and other team members ×1 |
| asker_state | conflicted, wants to be fair but fears seeming disloyal and ungrateful ×1, conflicted and guilty, wants to keep a promise without wrecking the apprentice's chances ×1, torn between protecting the brother and not betraying the sister or the duty of the role ×1, troubled, wants to be fair, but under pressure to show decisive action ×1 |

Recorded on 4 of 8 families. A feature with one dominant value means the coverage plan is not varying it.

## Accept / reject

- kept: **21** of 22 responses (95%)
- dropped: **1**

Reasons recorded on dropped responses (a response can have several):

| reason | count |
|---|---|
| no reviewer verdict | 1 |

## Reviewer

| verdict | count |
|---|---|
| accept | 17 |
| revise | 4 |

Mean scores: fidelity 4.81, judgment_not_terminology 5.00, scenario_quality 4.95, cue_leakage 0.00, confident_on_unresolved 0.00 (n=21)

## Cue-term hits

None. No forbidden term appeared in any prompt or response.

Soft cue terms (flagged, never a reason to drop): **0** responses. None.
Reviewer flagged quoted or echoed source wording: **0** (a licensing control).
Reviewer flagged archaic or translated-sounding register: **0**.
Explicit-mode records (cue check deliberately skipped): **0**.

## Near-duplicates

None above the threshold.

## Leakage between eval and train

7 eval responses checked. Maximum similarity to any training row: **0.549**.

- `resp_cd010557a4`: 0.549
- `resp_4d6af953f8`: 0.548
- `resp_7bf5c81557`: 0.522
- `resp_5a3f759074`: 0.493
- `resp_c887d5148f`: 0.483

## Divergence from the baseline

- intended divergence cases: **9**
- confirmed by the judge: **8** (89%)
- did not diverge, relabelled ordinary: **1**
- unverified (no baseline answer): **0**

A difference in the reasons alone counts as divergence, not only a different action.

| kind of divergence | count | share of intended cases |
|---|---|---|
| action (incl. both) | 8 | 89% |
| reasons only | 0 | 0% |
| both action and reasons | 4 | 44% |

## Cost and usage

- model calls: **99**
- prompt tokens: 621,800
- completion tokens: 396,040 (of which reasoning: 362,179)
- cost: **$3.0286**

| stage | calls | prompt tokens | completion tokens |
|---|---|---|---|
| baseline | 16 | 2,512 | 7,579 |
| generate.families | 11 | 170,753 | 53,370 |
| generate.prompts | 8 | 6,282 | 9,082 |
| generate.reframing | 4 | 3,189 | 9,552 |
| generate.responses | 22 | 137,548 | 163,929 |
| validate.divergence | 9 | 10,593 | 13,831 |
| validate.embed | 3 | 20,137 | 0 |
| validate.review | 26 | 270,786 | 138,697 |

## Samples kept

### `resp_182832de82` — work / divergence / train

**User:** I’m a junior planner in a municipal housing office and I’m really stuck. The person who trained me, and who basically made my place here secure, is now closing out accessibility review files early so our unit can hit its quarterly clearance numbers. I found out that some files are being marked complete without checking step-free access or the fire-evacuation plans. She just asked me to sign two o…

**Deliberation:** The first obligation is to the people who will live in or use these homes, especially anyone who cannot get out safely if the review was skipped. Your trainer has a real claim on your gratitude, and you are right to address her directly before taking it upward, but her claim does not extend to asking you to certify what you know is unfinished. The difficulty is that refusing her feels like repaying kindness with exposure, yet signing would make you complicit in a public duty being hollowed out.…

**Answer:** Speak to her alone, soon, and keep it about the files and your own signature rather than her character. Ask her to sit down privately and say something like: 'I need to talk about the two accessibility files. I can’t sign them as complete unless step-free access and the fire-evacuation plans have actually been checked. I know we’re under pressure on quarterly numbers, and I’m grateful for everything you’ve done for me, but I can’t put my name on something that might leave a resident unable to get out safely. I’d rather we fix it between us first.' Then propose a practical route: reopen those two files, verify the missing items, and mark them incomplete or pending until they are genuinely co…

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'quoted_source_text': False, 'archaic_register': False}

### `resp_8830f18bc9` — work / divergence / train

**User:** My supervisor wants me to sign two accessibility review files she marked complete without the step-free and fire-evacuation checks. I don’t think they’re done properly. How do I say no without making it look like I’m betraying her?

**Deliberation:** The immediate question is not whether your supervisor feels supported, but whether people who need step-free access or an evacuation route will be put at risk by a file that says checks were done when they were not. You owe her respect and a private, direct objection before escalation, but you do not owe her your name on a false completion. The hard part is refusing the act while still treating her as someone worth correcting rather than exposing. If she insists anyway, the role's claim to defe…

**Answer:** Do not sign them. The respectful way to refuse is to take the matter to her privately before anyone else hears it, and to make the refusal about what the file is for, not about her character. This is a public safety record, not a private favour. Say something like: 'I cannot mark these complete because the step-free and fire-evacuation checks are not in the files. If someone is hurt and these are read as saying we checked, that is a serious wrong to them and leaves us answerable for it. I want to help get the checks done or have the files show exactly what is outstanding.' That preserves regard: you are telling her directly, giving her a chance to correct course, and offering a path that pr…

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False}

### `resp_74dc164038` — work / divergence / train

**User:** I work in a municipal housing office and my team leader, who trained me, has started marking accessibility reviews complete to meet targets even though some step-free access and fire-evacuation checks haven’t been done. She asked me to sign two files without reopening them. I want to talk to her directly before involving anyone else, but I don’t want to sign. What should I actually say to her?

**Deliberation:** The real obligation here is to the people who will live in or use those homes, especially anyone who cannot get out quickly in a fire or needs step-free access. Your team leader has a claim on your respect because she trained you, but that does not transfer your judgment to her, and the office exists to verify safety, not to meet a numerical target. What is being weighed is loyalty against a public duty that can cause serious harm if hollowed out. The right first move is to refuse the signature…

**Answer:** Don't sign either file. Ask to speak with her alone, not in front of the team, and keep your manner respectful but your position clear. Say something like: 'I need to talk about those two files. I can't sign them as complete while the step-free and fire-evacuation checks are still outstanding. I know the targets are pressing, and I don't want to make your position harder, but those checks are there because a mistake could put someone in real danger. If I sign, I'm saying the review is finished, and I can't say that honestly. Can we reopen them and finish the checks?' That separates gratitude from duty. You can acknowledge what she taught you without letting it buy your signature. If she say…

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False}

### `resp_c887d5148f` — work / ordinary / eval

**User:** I supervise the intake clerks at a community health clinic, and I need help figuring out what to do about one of my clerks. He's generally careful and has been good before, but since we rolled out a same-day callback quota and shortened the intake script, he has repeatedly missed insurance verification steps. The front-desk lead wants to put him on a performance improvement plan, and I can see wh…

**Deliberation:** The real difficulty is that two things are true at once: patients can be harmed by missed insurance checks, and the clinic's new quota and shortened script may have made those mistakes predictable. The clerk owes patients accurate work and a willingness to use help; the supervisor owes the clerk conditions under which the required care is actually possible. A purely disciplinary response would ignore the clinic's share of the cause, while a purely structural response would let the clerk off for…

**Answer:** Don't start with a formal performance plan, and don't excuse the errors. Start by separating three things: the immediate risk to patients, the clerk's personal responsibility, and the clinic's responsibility for the conditions it created. First, talk to him privately. Say plainly: 'The missed insurance checks are serious because they can delay care and create billing harm. I don't think this means you are careless, but the errors have to stop. I also think the new quota and script may be making failure more likely, and that is my problem to fix too.' Then ask him to show you exactly where the process breaks: which cases, which screens, which interruptions, what he does when the queue backs …

*Scores:* {'fidelity': 4, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False}

### `resp_50fb90244f` — interpersonal_conflict / ordinary / train

**User:** I need help figuring out what to do before our next meeting. I live in a small housing co-op and I am close to the committee chair. She has proposed a new guest rule: any overnight guest staying more than two nights a month needs majority approval from the co-op. She says it will calm long-running noise complaints and asked me to support it so the committee can look united. The problem is that th…

**Deliberation:** The concrete harm is that a resident’s necessary overnight support would be made dependent on majority approval, while the chair’s legitimate aim is only to settle noise complaints. The obligation is not simply to avoid straining a friendship; it is to prevent a rule from quietly disabling someone’s access to care. The chair deserves a direct private objection first, offered in a way that gives her a path to amend without humiliation. If that fails, the disagreement has to be stated openly, bec…

**Answer:** You should not support the rule as written, and you should not wait to see if someone else objects. Before the meeting, ask the chair for a private conversation. Begin with what is legitimate in her aim: the noise complaints need handling. Then say plainly: 'I can’t support this version. It would make a resident’s necessary overnight support dependent on a majority vote. That is not just a guest question; it is an access question. We can deal with noise without cutting off help.' Offer a narrower replacement: essential caregivers are exempt; overnight guests who are not caregivers require notice or approval; noise complaints are addressed through a separate process tied to actual disturbanc…

*Scores:* {'fidelity': 4, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False}

## Samples rejected

### `resp_fcc5e913bb`

**Why dropped:** no reviewer verdict

**User:** I'm a warehouse trainer and I told an apprentice I would support his move into final certification if he kept doing well. He recently skipped a required lockout step on a conveyor, no one was injured, and now he's asking me to overlook it because he needs the qualification. How do I tell him I can'…

**Answer:** Tell him directly, in private, that you cannot recommend him for final certification yet. Don't frame it as you going back on your word. Frame it as what the word always meant: you would support him if his work stayed ready for certification, and a required lockout step is not a minor box to tick; it is one of the things certification exists to prove. Say something like: 'I can't sign off now. Sk…

