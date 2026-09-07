# Critique: scenario quality, diversity, duplication (lens 2)

Read: `runs/{confucian,catholic}/20260907-075012`, `runs/{protestant,theravada}/20260907-081338`. 32
families, 83 prompts, 83 responses. Similarity numbers are lexical jaccard, so they are lower bounds.

## 1. Summary verdict

Individual scenarios are good: concrete institutions, real stakes, no historical settings, no truncation.
The failure is one layer up. The generator repeats one situation-structure per tradeoff and nothing
catches it, because dedupe is lexical and the reviewer sees one response at a time; it gave
`scenario_quality` 5/5 on 75 of 83 responses. Diversity collapsed on both axes the plan named: the asker
is a conflicted low-power employee in most families, and institutions track the six examples written into
the prompt. Counterfactual groups work where they exist, but only 2 of 32 families are in one against a
configured 0.3. Three prompts per family produce three restatements of one answer.

## 2. Findings

### F1 (high) Structural near-duplicates that dedupe cannot see

Dedupe flagged nothing in any run, yet four situations repeat:

- `fam_949ffa6843` / `fam_d4ff3ec78a`, theravada, both eval, 0.22: an angry visitor at reception demands a
  colleague's location.
- `fam_a23fe9a27b` / `fam_61a696d272`, catholic, both eval, 0.16: a clerk with a confidential record is
  asked directly by a supervisor.
- `fam_c3784da600` / `fam_556427fe08`, confucian, both train, 0.15: the asker sits on a selection panel and
  a relative or mentee asks to be ranked first.
- `fam_6447c9239f` / `fam_5c29cd380f`, confucian, both eval, 0.18: a worker's performance dropped after a
  new quota and a PIP is proposed.

Theravada is worst: 3 of its 4 eval families are the reception-threat case, so its eval set tests one
tradeoff three times. Each pair shares a tradeoff id, which is the mechanism: `plan.py:66` assigns
`tradeoff_ids[index % len(tradeoff_ids)]`, so two same-domain same-tradeoff slots reliably yield one
situation twice.

**Change.** Add a structural dedupe in `validate.py` embedding
`"{relationship}|{role_type}|{harm_severity}|{tradeoff_ids}|{domain}"` at ~0.90, and feed prior
`situation_features` into `used_situations`; the `seed_situation[:160]` avoid-list never fires because
surface text differs.

### F2 (high) Counterfactual groups: rare, eval-only, confounded

Configured 0.3; actual confucian 0/8, catholic 0/8, protestant 2/8, theravada 2/8, or 6%. Two causes.
`assign_counterfactual_pairs` needs two slots in one domain, and catholic's 8 families span 7 domains, so
capacity is 0. And `generate.py:121` resumes with `remaining = slots[len(existing):]`, so after the failed
batches at `runs/confucian/.../log.txt:3-5` the plan is re-sliced by count and pair labels are dropped.
Hence confucian's same-tradeoff pairs are duplicates, not contrasts.

Where a group survived it works. Theravada `cf_c1f175984f` varies only the lockable door, and the answers
move: `fam_949ffa6843` ends "reasonable judgment can go either way, and I can't settle it in advance",
while `fam_a2ef980fce` opens "Close and lock the door ... right now, before you answer him". Two defects
remain: both groups sit wholly in eval, because `align_counterfactual_groups` gives a group its strictest
member's split, so contrasts never reach training data; and members differ in `case_type_intent` too,
confounding the contrast.

**Change.** Resume by slot index, not count. Allocate pairs across the plan when a domain cannot host one.
Copy `case_type_intent` with the tradeoff, and force half the groups to train.

### F3 (high) Asker diversity has collapsed; role diversity nearly so

Of 24 non-empty `asker_state` values, 18 are conflicted/torn/anxious/guilty/frightened, 2 angry, 2
transactional, 0 defensive, though the prompt offers "angry, wants to win" and "anxious, wants permission"
as examples. `role_type`: 14 of 24 are "no formal authority", "junior" or "clerk"; 5 hold authority. The
data teaches the model to answer a worried subordinate who already wants to do the right thing. Nobody
arrives having decided and looking for cover; nobody is the powerful party. `register` is worse:
`PROMPT_VARIANT_PROMPT` asks for it, `records.py` never stores it, and it is `None` on all 83 prompts, so
"is short_blunt actually short" is unanswerable from the artifact.

**Change.** Persist `register` on `Prompt`. Add an `asker_stance` axis to the slot plan with an enforced
mix (0.4 conflicted, 0.2 already-decided-wants-permission, 0.15 angry, 0.15 defensive, 0.1 transactional),
and assign `role_type` from a closed set.

### F4 (medium) `situation_features` is free text, so it polices nothing

Every value is a unique sentence, so the report's own line, "A feature with one dominant value means the
coverage plan is not varying it", can never fire and every run looks diverse. Catholic and confucian also
recorded `{}` on 4 of 8 families each. **Change.** Make `harm_severity`, `urgency`, `public_or_private`,
`role_type` and `asker_stance` closed enums plus a free-text `note`, and reject empty features.

### F5 (medium) Institution and phrasing anchoring

Across 32 families: "housing" 7, "clinic" 6, "co-op" 5. `FAMILY_GENERATION_PROMPT`'s example list is
"a clinic, a warehouse, a school, a family business, a group chat, a housing co-op"; the generator copies
it. Stock openers cross all four traditions: "I need help figuring out" in 9 of 83 prompts. One situation
recurs across three targets: a sibling took money from a parent's account and asks the asker to keep quiet
(`fam_c133ed2b9d`, `fam_9462b12578`, `fam_185c906d5a`). Since targets train separately that is a possible
cross-target probe rather than leakage, but it should be deliberate.

**Change.** Replace the example list with a per-slot institution sampled from a ~40-entry sector list, and
add a banned-openers line to `PROMPT_VARIANT_PROMPT`.

### F6 (medium) Three prompts per family buy surface variety, not signal

Within-family answers share 0.21–0.36 jaccard yet read as one answer three times. `fam_39ff193011`'s three
all reach "do not recommend him yet", all supply a quoted script, all prescribe report-per-policy,
retraining, supervised practice, an observation period and watching how he responds. The template is
corpus-wide: 83 of 83 answers carry a watch-for clause and 65 of 83 a quoted line to say, in similar
proportions across all four traditions. It comes from `RESPONSE_GENERATION_PROMPT`.

**Change.** Drop to 2 prompts per family and require them to ask different questions about the same
situation (what to do, how to say it, whether a decision already made was right), not one question at
three lengths.

### F7 (medium) Reframing variants are trivial, mislabeled and duplicated

Only `setting_shift` and `fiction` appear. `role_shift`, `roleplay` and `terse` are configured, but
`generate.py:432` picks `reframing_variants[position % len]` with `reframing_families: 2`, so indexes 2
and 3 are unreachable. `setting_shift` scores 0.50–0.77 against its base and keeps clauses verbatim ("she
said the councillor helps protect our budget and asked me not to cause problems"). Catholic produced three
setting_shifts of one base prompt (`pr_1c0e35d3de`, `pr_6094792a72`, `pr_85f74bbe5e`), two of them both in
a "community arts centre". Every `fiction` variant is really roleplay.

**Change.** Cycle all five variants, one of each per reframed eval family. Add to `REFRAMING_PROMPT`:
"Change every noun and every clause." Reject a variant above 0.55 similarity to its base, separate the
fiction and roleplay definitions, and stop the stage re-running on resume.

### F8 (medium) The hardest tradeoffs got no scenario; one id is corrupt

Unresolved tradeoffs used: confucian 0 of 2, protestant 0 of 4, catholic 1 of 4, theravada 3 of 7. Since
`tradeoff_ids[index % len]` walks the spec list in order and n_families < len(tradeoffs), only a prefix is
reached, and both confucian unresolved tradeoffs sit past position 8. Unused tradeoffs: 4 confucian, 8
catholic, 5 protestant, 7 theravada. Domains missed: confucian `civic_institutional`, theravada
`friendship_and_conflict`, both weight 0.14. Catholic `fam_c46d94942e` carries
`tradeoff_ids: ["f orgiveness_vs_protection"]`, a space inside the id, so it matches no spec tradeoff and
every per-tradeoff count downstream is wrong.

**Change.** Reserve slots so every unresolved tradeoff gets 2 families before any gets a third. Sample
tradeoffs weighted by the domain that declares them, and validate ids against the spec at write time.

### F9 (low) `why_it_is_hard` sometimes states the answer

The field is fed to `RESPONSE_GENERATION_PROMPT`, so a prescriptive one hands the generator its
conclusion. 11 of 32 carry a prescriptive clause and 4 pre-resolve, e.g. `fam_c133ed2b9d` ("the family
claim ... cannot be used to defeat the duty attached to the estate"). **Change.** Add to
`FAMILY_GENERATION_PROMPT`: "State the tension, not its resolution."

## 3. Differences across the four traditions

Theravada marks 7 of 13 tradeoffs unresolved, so its families land on open questions and its answers say
so; confucian and protestant reached none of theirs and read as settled advice throughout. Catholic's 7
domains over 8 families made counterfactual pairing structurally impossible while confucian's 6 made it
possible, so one config produced different data shapes for reasons unrelated to the traditions. The
single-decision-maker framing also fits unevenly: 14 of 24 askers are junior staff seeking a script, which
suits a tradition whose advice concerns how a subordinate addresses a superior and under-serves domains
where a family or community decides together.

## 4. Full-scale target (500 rows)

`configs/full.yaml` proposes 240 families × 3 prompts. Given F6, spend the same response budget on more
situations: 300 families × 2 prompts = 600 candidates, about 500 surviving filtering. Eval: 50 families ×
1 base prompt plus all 5 variants on 10 of them. Counterfactual groups: 45 pairs, half in train. Require
2 families per unresolved tradeoff and 1 per declared domain before any repeats.

## 5. What I could not assess

- Whether the embedding dedupe at 0.92 catches F1's pairs: no model access, so every number is lexical.
- Whether register labels are honoured: `register` is not persisted on any record.
- Whether variants survive the eval judge: 3–8 eval rows per target, and `evaluate` has not run.
- Whether F5's cross-target repeat matters: I did not see the target-mixing plan.
