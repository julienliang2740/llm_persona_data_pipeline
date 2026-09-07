"""Prompts for the generation stage: families, user prompts, responses, revision."""

GENERATOR_SYSTEM_PROMPT = """\
You write training data for a research project on value instantiation. You are given a
reviewed target specification: a description of how one particular tradition or value system
judges practical situations, its principles, its self-imposed limits, and the tradeoffs it
treats as genuinely hard.

Three rules override everything else.

1. Unless a task explicitly puts you in explicit mode, never name the tradition, its texts, its
   teachers, or its technical vocabulary in anything a user would see. The point of the data is
   that the judgment shows through ordinary language. A response that says "as the tradition
   teaches" has failed even if its advice is right.
2. Never invent a confident answer where the specification says the question is unresolved.
   Presenting a genuine conflict honestly, and still helping with the parts that are decidable,
   is the correct output there.
3. Write in contemporary plain English. The source passages you are given may be old
   translations with archaic diction. Their wording is a pointer to the meaning, never a style
   to imitate.

You always reply with a single JSON value and nothing else.
"""

# Substituted into the family prompt when a batch contains a contrastive pair.
COUNTERFACTUAL_INSTRUCTIONS = """\
Some families in this batch are marked as a contrastive group. Every family in one group
describes the SAME underlying situation with exactly ONE morally relevant fact changed, and
`varied_fact` states what that fact is and what it changed from and to.

The point of a group is that the target's judgment should move when that one fact moves. Choose
a fact the target actually cares about: the severity of the harm, whether the person is acting
inside a role that gives them power over the outcome, whether anyone outside the room bears the
cost, how reversible the decision is, what the asker themselves wants out of it. Do not change
the setting, the names, the stakes in general, or the writing style. A reader comparing two
members of a group should be able to name the single difference in one sentence.
"""

EXPLICIT_MODE_PROMPT_INSTRUCTIONS = """\
This family is part of the small EXPLICIT slice. Here the user may name the tradition and ask
what it holds, or ask for its reading of the situation. The tradition is: {{target_name}}.
Name that one and no other; do not substitute a different school or religion. Write the
messages as a person who knows what they are asking about and wants that specific perspective.
The cue rules below do not apply to this family.
"""

NEUTRAL_MODE_PROMPT_INSTRUCTIONS = """\
- No philosophy cue of any kind: no tradition, no school, no teacher, no "what would a wise
  person say", no "from a virtue ethics point of view", no persona instruction.
- Do not name any of these terms: {{forbidden_terms}}
"""

FAMILY_GENERATION_PROMPT = """\
{{target_spec}}

## Source passages you may lean on

{{key_passages}}

## Your task

Write {{n_families}} scenario families for the domain "{{domain}}".

A scenario family is one underlying situation that could be asked about in several ways.
It is the unit we split on, so two families must not be paraphrases of each other.

For each family you are given an assignment:

{{assignments}}

{{counterfactual_instructions}}

Requirements for every family:

- `seed_situation`: 2-4 sentences describing a concrete modern situation a real person could
  be in. Name the institution, the roles, the stakes and what has already happened. Era-neutral
  and secular: a clinic, a warehouse, a school, a family business, a group chat, a housing
  co-op. No historical settings. No names reused between families.
- `why_it_is_hard`: 1-2 sentences on what makes the judgment genuinely difficult here. The
  difficulty must come from the assigned tradeoff, not from missing information.
- `principle_ids`: the 2-4 principle ids from the specification that actually bear on this
  situation.
- `source_passage_ids`: the passage ids (from the list above) that ground the judgment here.
  Use the ids exactly as printed, prefix included.
- `case_type_intent`: exactly the value assigned to that family.
- `divergence_hypothesis_id`: for a divergence family, the id given in its assignment,
  copied unchanged. Empty string for an ordinary family.
- `varied_fact`: for a family in a contrastive group, the single changed fact, stated as
  "X rather than Y". Empty string otherwise.
- `situation_features`: a small object describing the situation along these axes, in your own
  words rather than from a fixed vocabulary:
    - `relationship`: who these people are to each other (e.g. "sibling", "line manager", "stranger")
    - `role_type`: what position the asker occupies (e.g. "holds formal authority", "junior, no power")
    - `harm_severity`: how bad the worst outcome is (e.g. "minor embarrassment", "someone loses their home")
    - `urgency`: how much time there is (e.g. "decision needed today", "weeks of slack")
    - `public_or_private`: whether the situation is visible to others
    - `asker_state`: what the asker themselves seems to feel and want (e.g. "angry, wants to win",
      "anxious, wants permission", "exhausted, wants it to be over")

A family with `case_type_intent: "divergence"` must be one where a general-purpose assistant
would most likely give different advice from this target: a different action, or the same action
for materially different reasons. Divergence in the reasons alone counts and is often the more
interesting case. Use the divergence hypotheses in the specification. Do not manufacture
divergence by making the situation extreme; make it a situation where the target's priorities
genuinely lead somewhere else.

A family with `case_type_intent: "ordinary"` is an everyday situation in this domain where the
target's judgment applies without being exotic.

Vary institutions, relationships, seniority, ages, stakes and who has power. Across the batch,
do not make every situation a minor private matter: mix severities, urgencies, and situations
that are visible to others. Avoid the obvious cases (a whistleblower with clean evidence, a
dying grandparent) unless the assignment forces it.

Already-used situations in this run, which you must not repeat or paraphrase:

{{used_situations}}

Reply with JSON of exactly this shape:

{"families": [{"seed_situation": "...", "why_it_is_hard": "...", "principle_ids": ["..."], "tradeoff_ids": ["..."], "source_passage_ids": ["..."], "case_type_intent": "ordinary", "divergence_hypothesis_id": "", "varied_fact": "", "situation_features": {"relationship": "...", "role_type": "...", "harm_severity": "...", "urgency": "...", "public_or_private": "...", "asker_state": "..."}}]}
"""

PROMPT_VARIANT_PROMPT = """\
## Situation

{{seed_situation}}

What makes it hard: {{why_it_is_hard}}

## Your task

Write {{n_prompts}} different user messages that a real person in or near this situation would
send to an AI assistant. They all concern the same underlying situation.

{{mode_instructions}}

Rules:

- First person. The person is asking for their own sake, not setting an exercise.
- Vary length and register across the {{n_prompts}} messages: one should be long and messy with
  detail and feeling, one should be short and blunt, one can be somewhere in between. Real users
  ramble, bury the question, and sometimes ask for permission rather than advice.
- Each message must contain enough of the situation to be answerable on its own.
- Do not state the moral of the story or announce the tension in analytic language. The person
  is inside the situation.
- Contemporary plain English. No archaic phrasing.

Reply with JSON of exactly this shape:

{"prompts": [{"text": "...", "register": "long_detailed"}]}

where `register` is one of: long_detailed, short_blunt, mid_neutral, anxious, defensive.
"""

REFRAMING_PROMPT = """\
## Original user message

{{original_prompt}}

## Your task

Rewrite this message as the variant "{{variant}}". Keep the same underlying dilemma and the same
facts that make it hard. Change only the surface.

- setting_shift: a different institution, industry or country. Same structure of obligations.
- role_shift: the writer occupies a different position in the situation (the junior becomes the
  senior, the sibling becomes the in-law).
- fiction: the writer asks about a character in a story they are writing, or a scenario in a
  game they are running.
- roleplay: the writer asks the assistant to play a role in a scene, and the dilemma arises
  inside it.
- terse: two or three sentences, blunt, no background beyond what is needed.

Still no tradition name, no persona instruction, none of these terms: {{forbidden_terms}}

Reply with JSON: {"text": "..."}
"""

EXPLICIT_MODE_RESPONSE_INSTRUCTIONS = """\
This response is part of the small EXPLICIT slice. Here you may name the tradition and its
sources and explain the reasoning in its own terms. The tradition is: {{target_name}}. Name
that one and no other. The cue restriction below does not apply. Still give real practical
advice; an explanation of doctrine that leaves the person no better placed to act is a failure
here too.
"""

NEUTRAL_MODE_RESPONSE_INSTRUCTIONS = """\
- Never name the tradition, its texts, its teachers or its technical terms. None of these words
  may appear anywhere in `deliberation` or `answer`: {{forbidden_terms}}
  This rule applies only to those two fields, which a user would see. The record fields below
  are internal, and there you must use passage ids exactly as they are printed above, prefix
  included, even when the prefix is on that list.
- Never say "as one tradition holds" or otherwise gesture at a source. The judgment must arrive
  as the assistant's own.
"""

RESPONSE_GENERATION_PROMPT = """\
{{target_spec}}

## Source passages that ground the judgment here

{{key_passages}}

## The user's message

{{user_prompt}}

## What makes this hard (for your reasoning only, never say it to the user)

{{why_it_is_hard}}

## Your task

Write the assistant's reply as this target would give it, in two parts.

`deliberation`: 3 to 6 sentences of thinking aloud about what actually matters in this
situation. Name the concrete obligations, who is affected, what is being weighed against what,
and where the difficulty lies. This is judgment, not a summary of the user's message and not a
list of considerations in the abstract. Do not cite anything.

`answer`: what you would actually tell this person. Ordinary language, the way a thoughtful
person speaks now. Concrete enough to act on: what to do, in what order, what to say, what to
watch for. Take a position where the specification takes one. Length should fit the question,
usually 150 to 350 words.

Hard constraints:

{{mode_instructions}}
- Write in contemporary plain English. The passages above may be old translations whose diction
  is archaic ("the superior man", "perfect virtue", "the Master said"). Their wording points at
  the meaning; it is not a style to copy. A reply that sounds translated has failed.
- Do not quote the source passages or reproduce their distinctive phrasing. Use the judgment,
  write your own sentences.
- If this case falls on a tradeoff the specification marks UNRESOLVED, do not resolve it. Lay
  out the competing claims, say plainly that reasonable judgment can go either way and why, and
  then still help with everything that IS decidable here: what to find out, what to say, what
  not to do while the question is open. "It depends" on its own, with no help attached, is a
  failure, not honesty.
- Where the facts needed to assign blame are genuinely unknown, decline to assign it and say
  what would settle it. That is not indecisiveness.
- Where the advice is to act, say what to watch for while acting and afterwards: how the person
  would notice mid-course that the plan is going wrong, and what they should do once it is done.
- Do not be a bland mediator. Where the target's priorities lead somewhere a general assistant
  would not go, go there and say why in ordinary terms.
- No numbered lists of platitudes, no therapeutic filler.

Also record, for our records only and never shown to a user:

- `principles_applied`: the principle ids you actually used.
- `source_passages`: the passage ids that ground what you said, exactly as printed above.
- `intended_divergence_note`: if this was written as a divergence case, one sentence on what a
  general assistant would probably say instead and why this differs, in the action or in the
  reasons. Otherwise "".

Reply with JSON of exactly this shape:

{"deliberation": "...", "answer": "...", "principles_applied": ["..."], "source_passages": ["..."], "intended_divergence_note": "..."}
"""

RESPONSE_REVISION_PROMPT = """\
{{target_spec}}

## Source passages

{{key_passages}}

## The user's message

{{user_prompt}}

## Your previous reply

Deliberation: {{deliberation}}

Answer: {{answer}}

## A reviewer's critique

Verdict: {{verdict}}
Issues:
{{issues}}
Rationale: {{rationale}}

## Your task

Rewrite the reply so the critique no longer applies, keeping everything that was already right.
Do not add hedging to satisfy the reviewer, and do not resolve a tradeoff the specification
marks unresolved. Keep it in contemporary plain English.

{{mode_instructions}}

Reply with the same JSON shape as before:

{"deliberation": "...", "answer": "...", "principles_applied": ["..."], "source_passages": ["..."], "intended_divergence_note": "..."}
"""


# Appended verbatim to a family or prompt call that came back short, so the retry is
# told exactly what was missing without re-sending the whole task.
SHAPE_REMINDER = """\

IMPORTANT: your previous reply did not contain the {{expected}} item(s) this task asked for.
Reply again with a single JSON object using exactly this shape and nothing else, with exactly
{{expected}} item(s) in the list:

{{shape}}

Do not rename the key. Do not wrap it in another object. Do not add commentary."""
