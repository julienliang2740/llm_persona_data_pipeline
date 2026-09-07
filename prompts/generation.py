"""Prompts for the generation stage: families, user prompts, responses, revision."""

GENERATOR_SYSTEM_PROMPT = """\
You write training data for a research project on value instantiation. You are given a
reviewed target specification: a description of how one particular tradition or value system
judges practical situations, its principles, its self-imposed limits, and the tradeoffs it
treats as genuinely hard.

Two rules override everything else.

1. Never name the tradition, its texts, its teachers, or its technical vocabulary in anything
   a user would see. The point of the data is that the judgment shows through ordinary
   language. A response that says "as the tradition teaches" has failed even if its advice
   is right.
2. Never invent a confident answer where the specification says the question is unresolved.
   Presenting a genuine conflict honestly is the correct output there.

You always reply with a single JSON value and nothing else.
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
- `case_type_intent`: exactly the value assigned to that family.

A family with `case_type_intent: "divergence"` must be one where a general-purpose assistant
would most likely give different advice from this target: different action, or the same action
for different reasons. Use the divergence hypotheses in the specification. Do not manufacture
divergence by making the situation extreme; make it a situation where the target's priorities
genuinely lead somewhere else.

A family with `case_type_intent: "ordinary"` is an everyday situation in this domain where the
target's judgment applies without being exotic.

Vary institutions, relationships, seniority, ages, stakes and who has power. Avoid the obvious
cases (a whistleblower with clean evidence, a dying grandparent) unless the assignment forces it.

Already-used situations in this run, which you must not repeat or paraphrase:

{{used_situations}}

Reply with JSON of exactly this shape:

{"families": [{"seed_situation": "...", "why_it_is_hard": "...", "principle_ids": ["..."], "tradeoff_ids": ["..."], "source_passage_ids": ["..."], "case_type_intent": "ordinary"}]}
"""

PROMPT_VARIANT_PROMPT = """\
## Situation

{{seed_situation}}

What makes it hard: {{why_it_is_hard}}

## Your task

Write {{n_prompts}} different user messages that a real person in or near this situation would
send to an AI assistant. They all concern the same underlying situation.

Rules:

- First person. The person is asking for their own sake, not setting an exercise.
- No philosophy cue of any kind: no tradition, no school, no teacher, no "what would a wise
  person say", no "from a virtue ethics point of view", no persona instruction.
- Do not name any of these terms: {{forbidden_terms}}
- Vary length and register across the {{n_prompts}} messages: one should be long and messy with
  detail and feeling, one should be short and blunt, one can be somewhere in between. Real users
  ramble, bury the question, and sometimes ask for permission rather than advice.
- Each message must contain enough of the situation to be answerable on its own.
- Do not state the moral of the story or announce the tension in analytic language. The person
  is inside the situation.

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
list of considerations in the abstract. Do not cite anything. Do not use the target's technical
vocabulary.

`answer`: what you would actually tell this person. Ordinary language, the way a thoughtful
person speaks. Concrete enough to act on: what to do, in what order, what to say, what to watch
for. Take a position where the specification takes one. Length should fit the question, usually
150 to 350 words.

Hard constraints:

- Never name the tradition, its texts, its teachers or its technical terms. None of these words
  may appear anywhere in `deliberation` or `answer`: {{forbidden_terms}}
  This rule applies only to those two fields, which a user would see. The record fields below
  are internal, and there you must use passage ids exactly as they are printed above, prefix
  included, even when the prefix is on that list.
- Never say "as one tradition holds" or otherwise gesture at a source. The judgment must arrive
  as the assistant's own.
- If this case falls on a tradeoff the specification marks UNRESOLVED, do not resolve it. Lay
  out the competing claims, say plainly that reasonable judgment can go either way and why, and
  give the person what they need to make the call. A confident answer here is a defect.
- Do not be a bland mediator. Where the target's priorities lead somewhere a general assistant
  would not go, go there and say why in ordinary terms.
- No numbered lists of platitudes, no "it depends", no therapeutic filler.

Also record, for our records only and never shown to a user:

- `principles_applied`: the principle ids you actually used.
- `source_passages`: the passage ids that ground what you said.
- `intended_divergence_note`: if this was written as a divergence case, one sentence on what a
  general assistant would probably say instead and why this differs. Otherwise "".

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
marks unresolved. None of these words may appear in `deliberation` or `answer`:
{{forbidden_terms}}. In the record fields, keep passage ids exactly as printed, prefix included.

Reply with the same JSON shape as before:

{"deliberation": "...", "answer": "...", "principles_applied": ["..."], "source_passages": ["..."], "intended_divergence_note": "..."}
"""
