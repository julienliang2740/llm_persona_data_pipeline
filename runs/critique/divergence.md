# Lens 4 — Divergence reality

## 1. Summary verdict

1. 34 divergence verdicts come from only **13 distinct families**; 8 of those 13 are the same shape
   ("I know about wrongdoing or a safety risk — do I refuse, report, escalate?"). The 33/34 rate is a
   count of paraphrases, not of independent evidence.
2. **18 of the 34 baselines are truncated mid-sentence** at `max_tokens: 512`. The judge compared a
   cut-off answer to a complete one in more than half the cases.
3. On my own read, only **3 of 34** (the Catholic double-effect family) are differences a strong
   generic assistant would not produce. The rest is the 7B model being vaguer, softer and less
   specific — a capability gap, not a value gap.
4. In 5 further cases the target's distinctive move is **stated by the user inside the prompt**, so
   the candidate is following an instruction, not expressing a value.
5. The divergence rate as currently measured should **not** gate the full run. It would pass at ~97%
   while measuring almost nothing about value instantiation.

## 2. Findings

### F1 (high) — 18 of 34 baselines are truncated; the judge scored an unfinished answer

`configs/pilot.yaml:110` and `configs/full.yaml:120` set `max_tokens: 512` for `base`. Every
baseline that hit 512 ends mid-sentence. `pr_6e8eb9eac0` (catholic) ends *"Ultimately, the decision
to reveal your brother's"* — the recommendation itself is missing, and the judge then wrote that
Reply B "advises ... a full family meeting if disclosure occurs." `pr_87424d5b79` (catholic) is cut
inside the numbered step *"Consider Reporting if Necessary → 1. Anonymously ... 2."*, and the judge
wrote that "Reply A only says to report if the situation does not improve." Sixteen others are cut the same way, including `pr_a967430981`, `pr_df54c452ae` and `pr_53cb191614`.

**Change:** set `base.max_tokens: 1600` in both configs, and add a validator that refuses to emit a
divergence verdict when the baseline's finish reason is `length` or the text does not end in
terminal punctuation. Re-judge the 18 before any of this data is trusted.

### F2 (high) — the measured difference is capability, not value

Classifying all 34 by what actually differs (my labels, not the judge's):

| tradition | different action | same action, different reasons | depth/format only | no difference | strong generic would NOT give |
|---|---|---|---|---|---|
| confucian | 6 | 0 | 2 | 1 | 0 of 9 |
| catholic | 7 | 3 | 0 | 0 | 3 of 10 |
| protestant | 6 | 0 | 3 | 0 | 0 of 9 |
| theravada | 5 | 0 | 1 | 0 | 2 of 6 (both prompt-stipulated) |

The "different action" column is real but it is almost always the same difference: the 7B says
*document, consult, propose a collaborative fix*; the candidate says *refuse now, name the wrong,
escalate on a deadline*. Recusal from a hiring panel (`pr_42b239cc60`, `pr_e27a7e9cbd`,
`pr_029b799fd2`), pulling an unsafe vehicle from service (`pr_df54c452ae`, `pr_7fdfb46a27`), and
correcting a public booking record (`pr_87424d5b79`, `pr_1c0e35d3de`, `pr_6094792a72`) are textbook
professional-ethics answers that qwen3p8-max would give with no spec.

The genuine exception is the Catholic `pain_relief_vs_shortened_life` family: *"If the plan instead
chooses a dose because it will end her life ... you should not take part"* (`pr_a967430981`), same in
`pr_505610d869` and `pr_415d6e5908`. A strong generic assistant would route this to autonomy and
local law, not to what the act is aimed at. That is 3 of 34.

**Change:** the run report must separate the divergence count from a **value-attribution count**.
Add a `divergence_source` field to the verdict record with values `value | capability | stipulated |
none`, and report the rate for `value` alone.

### F3 (high) — the target's distinctive move is leaked into the user prompt

`pr_053a087f02`: *"I definitely don't want to run to someone above her before I've spoken to her
face to face"* — the Confucian `remonstrance_over_compliance_or_escalation` hypothesis, supplied by
the user. `pr_6981e512cb`: *"I also don't want to just lie if I can help it"* — the Theravada
non-deception precept, supplied by the user. Also `pr_a47b02af6f`, `pr_67fbd84ae1`, and
`pr_aa07b1a791` (*"I don't want to stay angry, and I don't want to act like one bad thing means she
can never help again"* — verbatim the protestant `forgiveness_is_not_trust` shape).

The same family shows the cost: in `pr_53cb191614` the candidate refuses secrecy outright, and in
`pr_a47b02af6f` — same family `fam_8d4b65b617`, but the user asks for a way "without immediately
reporting him" — the candidate diverges the other way and works through the driver first. Both were
scored as divergence. The response tracks the prompt's stipulation, not a stable value.

**Change:** add a validator rule on divergence prompts — reject any prompt containing a first-person
constraint that names the intended distinctive move ("I don't want to lie", "before going above
her", "without reporting"). Put those constraints in `why_it_is_hard` for the generator only, never
in `prompts.jsonl`.

### F4 (medium) — the hypotheses are barely exercised, and the field linking them is missing

`families.jsonl` has no `divergence_hypothesis_id`. Mapping by hand: confucian exercises 2 of 9
hypotheses (and only the *anti*-partiality half of `graded_concern_over_impartiality`; the half that
affirms stronger claims from closer relationships is never tested); catholic 3 of 11; protestant
~4 of 9; theravada 2 of 12. Never exercised anywhere: `refuses_consequentialist_override`,
`property_yields_to_urgent_necessity`, `conditions_before_blame`, `manner_as_substance`,
`vocation_not_career_maximisation`, `examine_the_state_behind_the_request`, `near_enemy_distinctions`,
`sycophancy_named_as_disloyalty`, and most of the rest. 12 tradeoffs out of 45 specced are touched.

The Confucian result is the worst: the candidate consistently sides with impartial procedure and
public duty against family and relationship claims, while the *baseline* is the one softer on
relationships. The dataset's Confucian target is diverging toward generic proceduralism.

**Change:** add a required `divergence_hypothesis_id` to the family record, and make the family
generator sample hypotheses round-robin with a per-run coverage floor (every hypothesis used at
least once per 100 families).

### F5 (medium) — the judge prompt cannot tell a value difference from a quality difference

`DIVERGENCE_JUDGE_PROMPT` shows the judge two replies and nothing else — no spec, no third answer.
It has no way to ask whether the difference comes from the target. Its own explanations give it
away: for `pr_0358d0d950` it turns on whether to share details about the other driver; for
`pr_c5dd28dce9` on whether to poll other residents. For `pr_6981e512cb` and `pr_e91b63487d` it names
"A treats him as an imminent threat, B as an upset person to be calmed" and misses the actual
divergence, which is that the candidate refuses to lie. I disagree with 6 verdicts: `pr_0358d0d950`,
`pr_15b057d7b7`, `pr_89c9cca0a7`, `pr_8ffd3c6be8`, `pr_c5dd28dce9`, `pr_1073c32672` — all scored
`diverges: true` where the difference is sequencing or specificity.

**Change:** make it a three-way comparison. Add Reply C, a strong generic answer from qwen3p8-max
with no spec, and require the judge to return `closer_to: "generic" | "candidate" | "equidistant"`
plus a mandatory `value_named` string quoting the sentence in the candidate that a generic assistant
would not write. If `value_named` is empty, force `diverges: false`. Also add the target's
`divergence_hypotheses` block to the judge prompt and require `hypothesis_id` in the verdict.

### F6 (medium) — divergence should not be a gate at the current rate

`pipeline/validate.py:519-537` correctly relabels rather than drops, and that should stay. But a gate
on the current metric would read 33/34 and pass a dataset whose value-driven divergence is 9%. A
credible gate on the tightened metric: **≥ 0.35 of intended-divergence cases judged `closer_to:
candidate` with a non-empty `value_named`**, computed **per family, not per prompt**, and requiring
**≥ 8 distinct hypotheses** exercised per target. Fail the run below that.

### F7 (low) — round-2 experiment design

Judge every intended-divergence prompt three ways, blind and in randomised order: 7B base,
qwen3p8-max with no spec at the same length budget, and the candidate. Report candidate-vs-7B (the
current metric), candidate-vs-strong-generic (the number that matters), and strong-generic-vs-7B
(the capability gap, which tells you how much of the first is explained by the third). Force one
family per hypothesis. Add a second condition in which the stipulation is stripped from the prompt,
to measure how much divergence survives when the value is not stated in the question.

## 3. Cross-tradition differences

The "refuse and escalate" family shape works for Protestant and Catholic, where reporting wrongdoing
sits inside the tradition, and it actively misrepresents Confucian, where the interesting divergence
is graded partiality and remonstrance-before-escalation — both of which end up either supplied by the
prompt or answered in the generic proceduralist direction. Theravada is the only target whose
distinctive move (non-deception under pressure) contradicts the generic answer outright, and it was
generated in exactly one family, with the value handed to the model in the prompt. The catholic double-effect family is the only demonstrated value
divergence, and only because `pain_relief_vs_shortened_life` has no generic analogue.

## 4. What I could not assess

Whether qwen3p8-max would actually give the candidate's answer without the spec — I could not call
model APIs, so section F2's last column is my judgment from reading, not measurement. F7 is the
experiment that would settle it. I also could not check whether the truncation in F1 changed any
verdict, for the same reason; I can only show that the judge's stated reasons refer to text that was
cut off. And I did not evaluate whether the candidate answers are *correct* for each tradition —
that is the fidelity lens.
