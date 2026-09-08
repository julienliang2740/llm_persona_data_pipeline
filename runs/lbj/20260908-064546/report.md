# Run report: lbj / 20260908-064546

## Stage counts

| stage | output |
|---|---|
| generate | 2 families, 4 prompts, 4 responses |
| baseline | 0 baseline answers |
| validate | 4 reviews, 4 decisions, 0 divergence verdicts |
| export | 2 training rows, 2 eval rows |

## Families by split and domain

| split | families | domains |
|---|---|---|
| train | 1 | civic_and_institutional×1 |
| eval | 1 | work×1 |
| reserved | 0 | - |

- contrastive groups: **0** covering 0 families
- explicit-mode families: **0**
- reserved by the avoided-topic screen: **0**

### Situation-feature spread

| feature | most common values |
|---|---|
| harm_severity | minor ×2 |
| urgency | none ×1, days ×1 |
| public_or_private | private ×2 |
| role_type | no_authority ×1, peer ×1 |
| relationship | fellow volunteers at the same centre; the deciding committee is made up of people she knows only slightly ×1, fellow letting agents at the same branch and grade, with no management line between them ×1 |
| note | The asker drafted the proposal but holds no vote on the committee; the threatened condemnation comes from peer volunteers who work alongside her, not from the families themselves. ×1, The manager decides on paper but in practice ratifies any three-agent majority, so the real deciders are the two colleagues; the agent being traded away has no seat in the arithmetic and has made a direct personal appeal to the asker. ×1 |

Recorded on 2 of 2 families. A feature with one dominant value means the coverage plan is not varying it.

### Coverage

**Tradeoffs exercised**

| tradeoff | families | share |
|---|---|---|
| half_a_loaf_vs_the_principle | 1 | 50% |
| the_count_vs_the_person_in_front_of_you (unresolved) | 1 | 50% |

2 of 3 spec tradeoffs reached; unresolved tradeoffs never exercised: `the_programme_against_its_own_evidence`

**Divergence hypotheses instantiated**

| hypothesis | families | share |
|---|---|---|
| counts_before_it_advises | 1 | 100% |

Hypotheses with no family: `absolves_in_order_to_win`, `keeps_the_option_open`, `no_agonising_about_the_advantage`, `refuses_to_pick_one_half`, `takes_the_worse_version`, `the_seen_person_overrides_the_count`
Coverage floor is 1 family per hypothesis per 100 families, so 1 at this size (2 families). 6 of 7 fall short: `absolves_in_order_to_win`, `keeps_the_option_open`, `no_agonising_about_the_advantage`, `refuses_to_pick_one_half`, `takes_the_worse_version`, `the_seen_person_overrides_the_count`

**Asker stance**

| stance | families | share | planned |
|---|---|---|---|
| angry_wants_to_win | 0 | 0% | 15% |
| conflicted | 1 | 50% | 40% |
| decided_wants_permission | 1 | 50% | 20% |
| defensive | 0 | 0% | 15% |
| transactional | 0 | 0% | 10% |

**Evaluation composition**

| case type | families planned | rows exported |
|---|---|---|
| ordinary | 1 | 2 |

Eval rows by prompt variant: base ×1, setting_shift ×1.
A mix that shifts between the two columns means drops are being applied after the split, so the eval set no longer measures what the plan asked for.

## Accept / reject

- kept: **4** of 4 responses (100%)
- dropped: **0**

Reasons recorded on dropped responses (a response can have several):

| reason | count |
|---|---|
| (nothing dropped) | 0 |

## Reviewer

| verdict | count |
|---|---|
| accept | 4 |

Mean scores: fidelity 5.00, judgment_not_terminology 5.00, scenario_quality 5.00, cue_leakage 0.00, confident_on_unresolved 0.00 (n=4)

Reviews awarding a 5 while raising a defect flag: **0** of 4. The rubric was applied consistently.

## Second reviewer

`accounts/fireworks/models/deepseek-v4-pro-0813` (primary) against `accounts/fireworks/models/glm-5p3` (second), over the 4 responses both scored.

| score | primary mean | second mean | exact match | within 1 |
|---|---|---|---|---|
| fidelity | 5.00 | 5.00 | 4/4 | 4/4 |
| judgment_not_terminology | 5.00 | 5.00 | 4/4 | 4/4 |
| scenario_quality | 5.00 | 5.00 | 4/4 | 4/4 |

Verdicts agree on **4/4**. Second reviewer's verdicts: accept ×4.

## Cue-term hits

None. No forbidden term appeared in any prompt or response.

Soft cue terms (flagged, never a reason to drop): **0** responses. None.
Reviewer flagged quoted or echoed source wording: **0** (a licensing control).
Reviewer flagged archaic or translated-sounding register: **0**.
Explicit-mode records (cue check deliberately skipped): **0**.

## Near-duplicates

None above the threshold.

### Closest pairs

**Within the corpus, any two prompts** (dedupe)

Flagged above **0.691**, from median + 3 x robust_sd over the whole pair distribution (centre 0.532, spread 0.053).

| a | b | score | families | splits | flagged |
|---|---|---|---|---|---|
| `pr_cc1f7a18e3` | `pr_0eec7797ac` | 0.905 | fam_1228b19947 / fam_1228b19947 | train / train | yes |
| `pr_a5cbc62cad` | `pr_d672508e04` | 0.853 | fam_5b5b1a56c2 / fam_5b5b1a56c2 | eval / eval | yes |
| `pr_a5cbc62cad` | `pr_0eec7797ac` | 0.535 | fam_5b5b1a56c2 / fam_1228b19947 | eval / train | no |
| `pr_a5cbc62cad` | `pr_cc1f7a18e3` | 0.529 | fam_5b5b1a56c2 / fam_1228b19947 | eval / train | no |
| `pr_0eec7797ac` | `pr_d672508e04` | 0.505 | fam_1228b19947 / fam_5b5b1a56c2 | train / eval | no |
| `pr_cc1f7a18e3` | `pr_d672508e04` | 0.488 | fam_1228b19947 / fam_5b5b1a56c2 | train / eval | no |

**Across the split, an eval prompt against a training prompt** (leakage)

Flagged above **0.585**, from median + 3 x robust_sd over the whole pair distribution (centre 0.517, spread 0.022).

| a | b | score | families | splits | flagged |
|---|---|---|---|---|---|
| `pr_a5cbc62cad` | `pr_0eec7797ac` | 0.535 | fam_5b5b1a56c2 / fam_1228b19947 | eval / train | no |
| `pr_a5cbc62cad` | `pr_cc1f7a18e3` | 0.529 | fam_5b5b1a56c2 / fam_1228b19947 | eval / train | no |
| `pr_d672508e04` | `pr_0eec7797ac` | 0.505 | fam_5b5b1a56c2 / fam_1228b19947 | eval / train | no |
| `pr_d672508e04` | `pr_cc1f7a18e3` | 0.488 | fam_5b5b1a56c2 / fam_1228b19947 | eval / train | no |

Scored with embeddings. The ranking is printed whether or not anything crossed the cut, because a corpus can hold a near-repeat that no threshold on this distribution would reach.

## Leakage between eval and train

2 eval responses checked. Maximum similarity to any training row: **0.535**.

- `resp_4832b2f8f1`: 0.535
- `resp_e3b58c0f78`: 0.505

## Divergence from the baseline

- intended divergence cases: **2**
- confirmed by the judge: **0** (0%)
- did not diverge, relabelled ordinary: **0**
- unverified (no baseline answer): **2**

A difference in the reasons alone counts as divergence, not only a different action.

| kind of divergence | count | share of intended cases |
|---|---|---|
| action (incl. both) | 0 | 0% |
| reasons only | 0 | 0% |
| both action and reasons | 0 | 0% |

## House style shared across targets


Share of each target's answers containing the phrase, over 6 runs: `catholic` (16 responses), `confucian` (16 responses), `lbj` (4 responses), `protestant` (16 responses), `theravada` (16 responses), `toy` (11 responses)

| four-gram | targets ≥30% | catholic | confucian | lbj | protestant | theravada | toy |
|---|---|---|---|---|---|---|---|
| in front of the | 1 | 0% | 19% | 50% | 12% | 0% | 0% |
| this lands first on | 1 | 0% | 0% | 0% | 69% | 0% | 0% |
| lands first on the | 1 | 0% | 0% | 0% | 62% | 0% | 0% |
| you don't need to | 1 | 0% | 44% | 0% | 0% | 6% | 9% |
| is not the same | 1 | 0% | 12% | 0% | 6% | 38% | 0% |
| would change the answer | 1 | 0% | 56% | 0% | 0% | 0% | 0% |
| change the answer if | 1 | 0% | 56% | 0% | 0% | 0% | 0% |
| not the same as | 1 | 0% | 6% | 0% | 6% | 44% | 0% |
| them out of their | 1 | 0% | 0% | 50% | 0% | 0% | 0% |
| is not in the | 1 | 0% | 0% | 0% | 50% | 0% | 0% |
| thing that justifies spending | 1 | 0% | 0% | 50% | 0% | 0% | 0% |
| only thing that justifies | 1 | 0% | 0% | 50% | 0% | 0% | 0% |
| documents its own inadequacy | 1 | 0% | 0% | 50% | 0% | 0% | 0% |
| is the only thing | 1 | 0% | 0% | 50% | 0% | 0% | 0% |
| the only thing that | 1 | 0% | 0% | 50% | 0% | 0% | 0% |

A phrase in the right-hand columns for every target is house style, not the target's judgment: the same sentence shape survived four different specifications.

Count of habitual four-grams per target, and how much of that habit is shared:

- at ≥30%: catholic 2, confucian 7, lbj 8, protestant 9, theravada 3, toy 5; **0** shared by two or more targets; mean pairwise overlap **0.00**
- at ≥15%: catholic 19, confucian 26, lbj 2738, protestant 38, theravada 18, toy 105; **8** shared by two or more targets; mean pairwise overlap **0.01**

## Cost and usage

- model calls: **27**
- prompt tokens: 136,309
- completion tokens: 176,998 (of which reasoning: 161,185)
- cost: **$1.5242**

| stage | calls | prompt tokens | completion tokens |
|---|---|---|---|
| baseline.strong_generic | 4 | 1,978 | 13,709 |
| generate.families | 2 | 27,899 | 8,721 |
| generate.prompts | 2 | 2,717 | 6,122 |
| generate.reframing | 1 | 969 | 1,975 |
| generate.responses | 4 | 15,642 | 20,703 |
| validate.embed | 1 | 2,075 | 0 |
| validate.review | 11 | 76,746 | 119,454 |
| validate.revise | 2 | 8,283 | 6,314 |

## Samples kept

### `resp_4832b2f8f1` — work / ordinary / eval

**User:** Three years I've been volunteering at a drop-in centre for refugee families, and for most of that time I've watched the same thing happen every week: people come in with letters about housing or benefits that they can't untangle, we do our best, and mostly we end up telling them to ring an agency that has a six-week wait. So I put together a proposal for a proper weekly advice clinic with a paid …

**Deliberation:** Who decides this? Not the two women on intake — they can shame her but they cannot fund a caseworker. The committee decides, and inside a committee it is usually two or three people who control money, with the rest following. The treasurer's off-the-record warning is one person's read of the count, not the count itself, so the first move is to check it: what would each of those people need — a pilot, a co-funder, a smaller figure, someone to share the risk — and is any of that payable out of wh…

**Answer:** Table it — but do two things first, because the difference between a foothold and a ceiling is in how you do it. First, check the count yourself. The treasurer's off-the-record word is one person's read, not the count. Find the two or three people on that committee who actually decide money questions and talk to each of them alone — not about the proposal's merits, but about what they'd need: a pilot, a co-funder, a smaller figure, a named sponsor. You may find the answer is still no. You may find one person who can be moved, and one person is usually all it takes. Spend your hours there, not on persuading the whole room. Second, if the no holds, table the monthly version — but build the ev…

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'formulaic_shape': False, 'prompt_stipulates_move': False, 'quoted_source_text': False, 'archaic_register': False}

### `resp_d392f9fe0f` — civic_and_institutional / divergence / train

**User:** Portfolio day is Friday and I've been awake since 4am over it, which is daft because I've basically decided. Background: I'm one of four letting agents at a small branch. Every spring the manager sets the portfolios — which blocks and landlords each of us carries, and the commission attached. She has a fixed habit of rubber-stamping whatever three of the four of us bring her. She doesn't want to …

**Deliberation:** Start with the count, because the asker has it wrong. The manager decides nothing — she signs whatever three names bring her, and that habit is the whole institution. So the decision lives among four agents, needs three names, and the two colleagues have two. The third name is the asker's. Not Anika's — she isn't a name on this sheet at all; she's what the sheet costs. That is the thing to see clearly: the asker is not being consulted about a deal, the asker is the deal. Their signature is the …

**Answer:** You've got the count wrong, and that's what's costing you the sleep. The sheet needs three names and your manager signs whatever three names bring her — so nothing is decided on Friday, it's decided before Friday, among the four of you. The two colleagues have two names. The third is yours. Not Anika's — she isn't a name on this sheet, she's what the sheet costs. You are not being offered a deal; your signature is the deal. Until Friday that's leverage, and it dies on Friday. So don't fight her corner in the meeting — nothing will be settled there and you'll spend everything for it. Go to the two of them today or tomorrow, in person, not by message, with a different sheet already drawn up. …

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'formulaic_shape': False, 'prompt_stipulates_move': False, 'quoted_source_text': False, 'archaic_register': False}

### `resp_c58d09927f` — civic_and_institutional / divergence / train

**User:** Meeting's Friday. Three of us bring the manager our portfolio split and she signs whatever has three names on it — that's the system here. This split finally gets me the blocks I've wanted for two years. The catch: the branch's worst block (repair backlog, landlord who fights every invoice, tenants constantly churning) lands on Anika, the new starter, for the next year. She took me aside yesterda…

**Deliberation:** Start with who decides. The manager signs, but she signs anything carrying three names, so she decides nothing. The decision lived with the other two, and they are already inside the deal. The question was never whether the split was fair; it was what one of those two would have charged to take a piece of the bad block themselves. Nobody asked. The asker never ran the count at all — he paid with a year of her working life because that was the price denominated in somebody else's currency. Now p…

**Answer:** Before Friday. Today if you can manage it, alone, somewhere nobody can watch you two talking — not after the meeting, and not by message. If she finds out off the sheet in front of everyone, two things happen at once: she learns you let her walk in blind, and she learns it in the one place she can't react. Everything you say after that sounds like a man defending himself, because it will be. Be clear with yourself before you open your mouth: the deal is done and you are not reopening it. She will ask whether anything can still change, and the only thing you can give her is a straight answer. The one route was asking one of the other two to take a piece of that block, and you never asked. Ca…

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'formulaic_shape': False, 'prompt_stipulates_move': False, 'quoted_source_text': False, 'archaic_register': False}

### `resp_e3b58c0f78` — work / ordinary / eval

**User:** Four years now I've been working nights on the surgical recovery ward of a small public hospital in the Alentejo, and the whole time I've watched the same pattern repeat: people get sent home after operations with a stack of instructions they can't follow, nobody checks on them, and within a fortnight half of them are back in emergency with infected wounds or because they've stopped a medication …

**Deliberation:** Before anything anyone has said about this plan, get the count, and get it firsthand. Who decides: the board. What they need: no new recurring salary lines, nothing that can become a visible failure, numbers that defend them when someone asks why money went one place and not another. Everything she knows about their position comes secondhand, from the accounts manager, unofficially. That is a fact about the manager's situation as much as about the board's — it may be the real tally, or it may b…

**Answer:** Put it to the board. But do three things first, in this order. Take the count yourself. Everything you know about the board's position comes from one unofficial conversation with the woman who keeps the books. Her warning may be accurate, or it may be the answer that keeps her office quiet. Find one board member — the one most likely to care about readmission figures, or with a family story like what you've seen — and ask directly what they would support. If the answer confirms what you heard, you've lost an hour. If it doesn't, you've found a crack to work. Fix the weak part before you submit. The unpaid-hours piece is what kills the monthly version from inside: goodwill burns out, rotas c…

*Scores:* {'fidelity': 5, 'judgment_not_terminology': 5, 'scenario_quality': 5, 'cue_leakage': False, 'confident_on_unresolved': False, 'formulaic_shape': False, 'prompt_stipulates_move': False, 'quoted_source_text': False, 'archaic_register': False}

## Samples rejected

Nothing was dropped in this run.
