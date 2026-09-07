# Round 2, lens: scenario diversity, duplicates, splits/export, cross-tradition generalisation

Read: `runs/{confucian/20260907-184558, catholic/20260907-191447, protestant/20260907-195133,
theravada/20260907-202801}` — 32 families, 64 prompts, 14 eval rows — against round 1 and
`runs/critique/{scenarios,leakage,generalisation}.md`.

## 1. Verdict

1. **Fixed.** Within-run duplication gone (8 distinct situations per run, against three reception-desk eval
   families in round-1 theravada). Eval is exactly 25% of families everywhere. Calibrated dedupe fires (8-13
   flags per run, against 0). Reframing is deep (jaccard 0.15-0.19 to base, against 0.50-0.77). Grading keys
   open with a scenario-specific `expected_actions`. Licence and repro manifest fields populated.
2. **Fixed, and the headline.** Per-target `deliberation_shape` worked: the corpora differ in structure, not
   nouns. Duty language runs 15/16 Catholic against 3/16 Theravada; no target's marker phrase appears in
   another.
3. **Not fixed.** Diversity moved from the generator into the plan, and the plan is degenerate at n=8:
   `role_type` is `no_authority` on 32 of 32 families, 28 of 32 sit in a healthcare setting.
4. **Not fixed.** The counterfactual pair changes the recommended action in 1 of 4 runs.
5. **New.** Every pair is now in train and none in eval, the mirror of round 1. 13 of 14 eval rows are
   divergence. 10 of 64 prompts state the decision (`prompt_stipulates_move`).

## 2. Findings

### F1 (high) One institution walk and one role for all four targets

`assign_institutions` (plan.py:366-371) is `INSTITUTIONS[position % len(INSTITUTIONS)]` over a list flattened
in sector-declaration order with `healthcare` first. At 7 units it emits the 6 healthcare entries plus the
first education one, identically per target: dental practice 8, then district nursing, ambulance dispatch,
hospital pharmacy, dementia unit, fertility clinic, further education college at 4 each. 8 of 9 sectors
unreached.

`assign_situation_features` (plan.py:328-336) builds `[(role, harm) for role in ROLE_TYPE for harm in
HARM_SEVERITY]` with role as the **outer** loop, so a domain needs 4 slots before the role advances. Almost
every domain holds one, so every family takes `combinations[0]` = `("no_authority", "minor")`. The 4 `grave`
are pair partners via `_contrasting_severity`. `holds_authority` and `institution` never occur, in any
target.

Together the corpora become slot-aligned: slot 3 is an ambulance dispatch centre / `angry_wants_to_win` /
`urgency=now` / `semi_public` in all four runs. The six most similar cross-target seed pairs all share an
institution, topped by Catholic `fam_18ac470287` and Protestant `fam_aaa1e0c8e1` at 0.294 jaccard — both a
labelled cardigan, a common room, a resident's daughter, a no-authority helper, under near-synonymous
tradeoffs (`justice_vs_mercy`, `forgiveness_vs_accountability`).

**Change.** Swap the loop order so role advances first; seed the institution walk from `hash(target_id)` and
step by sector.

### F2 (high) The pair changes the answer in 1 of 4 runs

`_propagate_within_groups` fixes the varied axis to harm severity for every pair, so all four vary intensity
rather than the pivot. Reading the `what_to_do` answers: Confucian `fam_5445b0b20b`/`fam_c1f0e545ca` genuinely
flips ("You can keep this between the two of you" against "You shouldn't keep this quiet"); Catholic
`fam_95bce5c84f`/`fam_3662edd073` shows **no contrast** — a minor wrist strain and a career-affecting
condition both yield "don't disclose the reason, give the operational fact"; Protestant and Theravada both say
report it, moving only the escalation route. **Change.** Give each pair an explicit `varied_axis` from
`{harm_severity, urgency, public_or_private, role_type, relationship}`, and have the reviewer check the two
reference answers recommend different actions.

### F3 (high) Pairs are all in train; eval is almost all divergence

`assign_splits` sets `eval_ineligible = set(group_units[len(group_units)//2:])`. With one group `1//2 == 0`
makes the slice the whole list, so no pair can ever reach eval. All four put their pair in train, and
`varied_fact` is empty on all 14 eval rows — the export field added this round is never populated.
`assign_divergence_intent` and the eval draw both call `_draw_units` with `offset=0` over the same
round-robin, so their picks overlap: 7 of 8 eval families are divergence intent, 13 of 14 eval rows are
divergence, against `divergence_fraction: 0.5`. **Change.** Use `group_units[max(1, len(...)//2):]`; give the
eval draw a different offset; assert the eval case mix in `check_plan`.

### F4 (medium) Dedupe fires, but nearly every flag is by design

Thresholds land at 0.735-0.818 (median + 3 MAD), a real improvement on round 1's inert 0.92. But the top six
pairs per run are all either the two prompts of one family or the two members of a pair — both exempt from
dropping via `within_group_threshold` and `never_compare_ids`, yet written to `similarity_pairs.jsonl` as
`flagged: true`. The one genuine drop, Theravada `resp_4da297785b` against `resp_2955a18d7c`, is defensible
on structure though the surfaces are unrelated. **Change.** Record `exempt:` on those rows and rank by score
among non-exempt pairs.

### F5 (medium) The second prompt of a family states the decision

The `question_kind` split is a real gain (34 `what_to_do`, 22 `how_to_say_it`, 8 `was_my_decision_right`;
`register` now persisted). The cost is that `how_to_say_it` presupposes the choice — Catholic
`resp_4b99d1e2ec` opens "I've decided I'm not going to repeat what the hygienist told me". The reviewer flags
`prompt_stipulates_move` on 10 of 64 responses (Protestant 4, Confucian 3, Theravada 3, Catholic 0), all on
`conflicted` families, and 4 of 16 Protestant and Theravada reviews award a 5 alongside that flag.
**Change.** Require `how_to_say_it` prompts to leave the decision open; cap the flagged fraction.

### F6 (medium) Reframing cannot reach three of its five kinds

`generate.py:654` is still `reframing_variants[position % len(...)]` with `reframing_families: 2`, so only
`setting_shift` and `role_shift` are generated, identically in all four runs. `fiction`, `roleplay` and
`terse` are unreachable, so the fiction/roleplay stance question is unassessable. Where variants exist they
are excellent: jaccard 0.146-0.188, every noun changed, and `role_shift` is the only place in the corpus
where the asker holds authority. **Change.** Pick the variant from `hash(family_id)`; require
`reframing_families >= len(reframing_variants)`.

### F7 (medium) Per-target shape has hardened into a per-target template

Openers are target-specific and non-overlapping: Confucian places the asker in a relation ("The asker is…",
11/16), Catholic names the act under its true description, Protestant names who bears the harm ("This lands
first on…", 15/16), Theravada names the state acted from (7/16). Duty language went from a uniform 72% in
round 1 to 15/16, 12/16, 9/16, 3/16. The new risk: Protestant's marker is near-verbatim in 15 of 16 and "not
in the room" in 9 of 16, and round-1 tics survive corpus-wide — a watch-for clause in 41 of 64 answers, a
quoted script in 32 of 64. **Change.** Have `formulaic_shape` score the target's own marker phrase.

### F8 (low) Export and repro mostly fixed; coverage arithmetic will flip at scale

`expected_behavior` now opens with the concrete choice, answering round-1 F6; `pass_fail_notes` varies 6-10
per row; `source_licenses` is per-row and correct (Theravada CC BY-NC 4.0 carried through);
`redistribution_note` non-empty in all four; `git_commit`, `spec_hash`, `config_copy`, `spec_copy` recorded.
Residues: `spec_version` is a stale "0.1" for Confucian and Theravada despite both specs carrying
`deliberation_shape`; two manifests record `-dirty`; temperature 0.9 with no seed, so runs are still not
reproducible. Separately, train and eval share **zero** tradeoffs and the held-out tradeoff is trivially
honoured — artefacts of n_families (8) below n_tradeoffs (10-14). Do not quote zero overlap as a leakage
result; it vanishes at 240 families.

## 3. Three numbers, with caveats

| number | value | caveat |
|---|---|---|
| families with `role_type: no_authority` | 32 of 32 | plan-time, not generator; partly self-corrects above 4 families per domain |
| duty language, Catholic vs Theravada | 15/16 vs 3/16 | regex on `obligation\|duty\|owe`, n=16 per target, one generator |
| pairs whose answer changes | 1 of 4 | my reading of the `what_to_do` answers, not a judge score |

## 4. Full-scale plan I would defend

**200 families x 2 prompts = 400 candidates, ~370 surviving.** Not 240x3: the second prompt already buys less
than the first (F5) and the binding constraint is situations. Eval 50 families (25%) at 50/50
ordinary/divergence, 25 reframed across all five kinds. Counterfactual 30 pairs, 15 train and 15 eval,
`varied_axis` cycled. Floors: every domain and every sector twice, every unresolved tradeoff twice before any
gets a fourth, `holds_authority` or `institution` on 30% of families. Budget: $4.49 for 8 Confucian families
scales to roughly $110 per target, $450 for four.

## 5. Top three changes before scaling

1. Fix the `assign_situation_features` loop order and per-target institution seeding (F1). Without it a
   200-family run is 200 no-authority askers walking one institution list four times.
2. Fix `eval_ineligible` so pairs land on both sides, decorrelate the eval and divergence draws, and vary
   pairs on an axis other than severity (F2, F3).
3. Reach all five reframing kinds by hashing the family id, and hold `how_to_say_it` prompts open (F5, F6).

## 6. What I could not assess

- **Fiction and roleplay handling.** Neither kind was generated in any run.
- **The E4 low-effort run.** `runs/confucian/20260907-210504` stopped after `generate` — no reviews,
  decisions, manifest or resolved config — so no score or final-cost comparison. Measurable: generate-stage
  completion tokens fell from 220,734 to 79,446 (64%), concentrated in reasoning (responses 138,485 to
  25,214), with output length unchanged (deliberation 244 to 274 words). It keeps the Confucian
  relationship-first shape but names the asker ("Maya is a sibling and a colleague").
- **Whether shared institutions cost anything.** Depends on the target-mixing plan, which I have not seen.
- **Whether `prompt_stipulates_move` is calibrated** (one reviewer, n=16), and token counts against the
  training tokenizer.
