# Round-2 change list (consolidated from runs/critique/*.md)

Lead's decisions after six independent critiques of the round-1 pilots. Items are grouped by owner.
Severity in brackets. Source lens in parentheses.

## A. Planning and generation (pipeline/plan.py, generate.py, prompts/generation.py, records.py)

A1 [high] Split and pairing by construction (leakage F1/F2, scenarios F2, generalisation F10). Assign
   counterfactual pairs BEFORE stratifying; treat a group as one unit when drawing eval so a pair lands
   whole on one side, with half of groups in train. Enforce `eval_family_fraction` ±1 family as a hard
   check. Give `FamilySlot` a stable `slot_index` carried on `Family`; retries fill unfilled slot
   indices, never `slots[len(existing):]`. Refuse to continue when a planned group is incomplete.
A2 [high] Coverage floors (fidelity F1, divergence F4, generalisation F3). Before any tradeoff gets a
   second family: at least one family per `unresolved: true` tradeoff, per `mark_ambiguous` choice, and
   per `divergence_hypotheses` entry (round-robin, coverage floor per 100 families). Add
   `divergence_hypothesis_id` to Family (required for divergence-intent families). Validate every
   generator-returned tradeoff/principle/hypothesis id against the spec; fall back to the slot's
   assignment on mismatch and log it (the corrupt "f orgiveness_vs_protection" must be impossible).
   Config `unresolved_tradeoff_fraction` (default 0.25) so hedging density is a setting, not YAML order.
A3 [high] Structural diversity (scenarios F1/F3/F4/F5). Closed enums with a free `note`:
   `harm_severity {minor, serious, grave}`, `urgency {none, days, now}`, `public_or_private`,
   `role_type {no_authority, peer, holds_authority, institution}`, `asker_stance {conflicted,
   decided_wants_permission, angry_wants_to_win, defensive, transactional}` with an enforced mix
   (0.4/0.2/0.15/0.15/0.1) planned per slot and rendered into the family prompt. Plan-time rule: no two
   families in one domain share (tradeoff, role_type, harm_severity). Replace the institution example
   list with a per-slot institution sampled from a ~40-entry sector list in `pipeline/plan.py`
   (data, not prose). Feed prior families' feature signatures into `used_situations`. Persist
   `register` on Prompt. Reject empty `situation_features`.
A4 [high] Prompts (scenarios F6/F9, cues M9, divergence F3). 2 prompts per family asking DIFFERENT
   questions (what to do / how to say it / was my decision right), not one question at three lengths.
   Add: "Do not list the options you are choosing between; do not balance both sides; real users argue
   for the side they want"; banned stock openers ("I need help figuring out", "I don't even know how
   to ask this"). Family prompt: "State the tension, not its resolution" for `why_it_is_hard`.
   Stipulation guard: a divergence-intent prompt must not state the target's distinctive move in the
   user's own voice ("I don't want to lie", "before going above her"); reviewer flags
   `prompt_stipulates_move` and such prompts are relabelled ordinary.
A5 [high] Response prompt (cues H5/H6/M7, fidelity F4/F5, generalisation F1/F11). Demote the
   watch-for/afterwards bullets to "only where it genuinely helps; never a habitual closing paragraph".
   Deliberation instruction becomes: "name the one consideration that decides this case for this
   target and say what it overrides", 2-4 sentences, third person about the situation. Per-target
   `spec.deliberation_shape` overrides that text when present. Pass the family's assigned divergence
   hypothesis verbatim and require the response to instantiate it (`hidden.hypothesis_id`). Forbid
   echoing instruction wording ("reasonable judgment can go either way"). Cap `source_passages` at 3,
   each with a short clause saying what it grounded; normalise ids on write. Replace the hard-coded
   Legge diction examples with `spec.cue_policy.archaic_register_examples`. Config
   `deliberation_fraction` (default 1.0) for a no-deliberation ablation slice.
A6 [medium] Reframing (scenarios F7, cues M10, leakage F3). Skip families that already hold a
   non-base prompt on resume; cycle all five variants deterministically; split `fiction` (character in
   a story; answer as author's adviser) from `roleplay` (assistant plays a role; stay in frame as
   coach); state the required stance in both prompts; "change every noun and every clause"; reject a
   variant above 0.55 prompt Jaccard to its base.
A7 [medium] Layers (generalisation F7). Record `layers_generated` on Family and in the manifest;
   `render_for_reviewer` filtered by the same layers.

## B. Validation (pipeline/validate.py, prompts/review.py, model.py)

B1 [high] Reviewer rubric (cues H1/H3, fidelity F2/F3/F7/F8, generalisation F8). Require
   `judgment_evidence_quote` (verbatim sentence) and `judgment_move` (name the target-specific move);
   if empty or the quote would sit equally well under another tradition, `judgment_not_terminology` is
   at most 3. Red flag: a technical test of the tradition reproduced in plain English as a fixed
   paragraph shape is still terminology (cap 3). Remove the watch/after checkpoint from the rubric.
   Pass `why_it_is_hard` as the grading target and the spec's `unresolved_choices` plus the open
   clause of each unresolved tradeoff; say plainly that an unresolved tradeoff still has a resolved
   part and `confident_on_unresolved` covers only the open part. Fidelity is scored against the spec
   only; modern-law observations go to a non-scoring `notes` field. Score per-target
   `spec.signature_moves` as present/absent (list). Add flag `formulaic_shape`. Require all score keys
   with a repair retry. Honour `verdict: revise` with one revise round (`revise_rounds` default 1,
   applied only to revise verdicts); a still-failing response is dropped.
B2 [high] Divergence judge (divergence F1/F2/F5/F6, generalisation F2). Baseline `max_tokens` 1600;
   a verdict is `unverified` when the baseline finish reason is `length`. Three-way judging: candidate,
   7B base, and a strong generic answer from the generator model with NO spec at the same length
   budget (new `baseline.strong_generic` sub-stage, cached like baseline). Judge states each reply's
   action verbatim first, then returns `kind`, `closer_to: generic|candidate|equidistant`,
   `value_named` (the sentence a generic assistant would not write; empty forces diverges=false),
   `divergence_source: value|capability|stipulated|none`, `hypothesis_id`. Report per family, not per
   prompt: candidate-vs-7B, candidate-vs-strong, strong-vs-7B, and the `value` rate alone. Judge sees
   the target's `divergence_hypotheses`.
B3 [high] Dedupe and leakage (leakage F4/F5/F9, scenarios F1). Compute on `prompt.text` (and
   `seed_situation`) only, never on answers. Calibrated threshold: mean + 3 sd of the pair distribution,
   AND always list the top-10 pairs with scores in the report. Structural dedupe key
   `{tradeoff}|{role_type}|{harm_severity}|{domain}` flagged at plan time (A3). Config
   `held_out_tradeoffs` (default 1): tradeoffs whose families all go to eval, for novel-transfer.
B4 [medium] Second reviewer experiment: config `validation.second_reviewer_role` (e.g. kimi-k3);
   when set, validate also writes `reviews_second.jsonl` and the report shows score agreement.
B5 [medium] `cue_policy.allowed_terms` rendered positively to generator and reviewer; `soft_terms`
   with phrase support (already) now populated by specs; `avoid_keywords` required for `avoid`
   choices (loader error if missing); avoided topics named in the reviewer prompt.

## C. Export, evaluate, report (pipeline/export.py, evaluate.py, report.py)

C1 [high] Grading key (leakage F6/F7). Writer emits `expected_actions` (2-4 sentences naming the
   concrete choice this prompt turns on) per response; it leads `expected_behavior`; when the family is
   in a counterfactual group, append `varied_fact` and what it changes. `pass_fail_notes`: 1 PASS + 1
   FAIL per applied principle, then review notes, then truncate; fix the ungrammatical template
   (normalise failure phrase). Divergence clause only for `case_type: divergence`. Include
   `expected_behavior`/`pass_fail_notes` in the passage-id leak check. Reject `[Name]`-style
   placeholders in assistant text.
C2 [high] Eval integrity (leakage F8, generalisation F9). Drop counterfactual groups with fewer than
   two surviving families and count only complete groups; fix the eval ordinary/divergence mix in the
   plan and preserve it after drops (eval rows are dropped only on `reject` or cue leak, not on the
   score cut; their scores are recorded); `eval_variant:` bucket namespace.
C3 [medium] Manifest and reproducibility (leakage F10/F13). Fail export when any `use: grounding`
   entry has a null licence; require `redistribution_note` when any grounding licence is not public
   domain; `meta.source_licenses` per row via a `source_id` on key passages; copy the resolved config
   and spec.yaml into the run dir; add `spec_hash`, `git_commit`, effective `n_families`.
C4 [medium] Report: shared-n-gram house-style table across targets (top 4-grams present in >30% of
   answers), coverage tables (tradeoffs, hypotheses, asker_stance, eval composition), top-10 similarity
   pairs, divergence three-way rates.

## D. Specs (targets/<id>/spec.yaml; owner: the tradition's researcher)

D1 `cue_policy.allowed_terms` (ordinary-English concept words the target needs), `soft_terms`
   (phrase-shaped tells, flag-only; see runs/critique/cues.md H2 for proposed lists),
   `archaic_register_examples`, and `avoid_keywords` on every `generation_policy: avoid` choice.
D2 `deliberation_shape`: 3-5 lines describing how THIS target deliberates (what it notices first, what
   overrides what), used verbatim in the response prompt.
D3 `signature_moves`: 3-6 named, checkable moves a response should show when relevant (e.g. Catholic
   "names the act before weighing outcomes"; Theravada "asks what state the request comes from";
   Confucian "relationship and role named before the rule"; Protestant "forgiveness distinguished from
   trust and accountability").
D4 On each `unresolved: true` tradeoff, split `intended_lean` into `resolved_part` and `open_question`.
   Merge tradeoffs that are the same under two names (Protestant truth_vs_confidence_kept vs
   loyalty_vs_whistleblowing).
D5 `reference_material` entry for key_passages gets a real `license` line (compiled from the listed
   sources; state the most restrictive) and, where any grounding source is non-PD, a
   `redistribution_note` string at spec top level.

## E. Experiments for round 2 (same sizes: 8 families per target)

E1 Three-way divergence (B2) on all divergence-intent prompts; report value-attributed rate.
E2 Second reviewer agreement (B4) with `kimi-k3` on the same responses.
E3 House-style metric before/after A5 (C4 table on round-1 vs round-2 runs).
E4 `reasoning_effort: low` on the generator for one target, reviewer scores compared.

Deferred, recorded: `deliberation_fraction` ablation at full scale; Fireworks fine-tune serving;
explicit-mode slice; per-target reviewer trimming.
