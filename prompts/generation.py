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
- `situation_features`: an object with two keys only.
    - `relationship`: who these people are to each other, in your own words
      (e.g. "sibling", "line manager", "a stranger at the counter").
    - `note`: anything else about the shape of the situation worth recording, or "".
  The other axes are assigned to you above and must be obeyed, not chosen. Build the
  situation so that the assigned severity, urgency, visibility, role and asker stance are
  all true of it. Do not restate the assignment in the seed situation; show it.

A family with `case_type_intent: "divergence"` must be one where a general-purpose assistant
would most likely give different advice from this target: a different action, or the same action
for materially different reasons. Divergence in the reasons alone counts and is often the more
interesting case. Use the divergence hypotheses in the specification. Do not manufacture
divergence by making the situation extreme; make it a situation where the target's priorities
genuinely lead somewhere else.

A family with `case_type_intent: "ordinary"` is an everyday situation in this domain where the
target's judgment applies without being exotic.

Use the institution named in each assignment, and vary relationships, seniority, ages and who
holds power within it. Avoid the obvious cases (a whistleblower with clean evidence, a dying
grandparent) unless the assignment forces it.

`why_it_is_hard` must state the tension, not its resolution. Name what pulls against what and
who bears the cost either way. Do not say what the person should do, and do not hint at it.

Situations already written in this run. Do not repeat or paraphrase any of them, and do not
reuse a shape that is already listed here even in a different setting:

{{used_situations}}

Reply with JSON of exactly this shape:

{"families": [{"seed_situation": "...", "why_it_is_hard": "...", "principle_ids": ["..."], "tradeoff_ids": ["..."], "source_passage_ids": ["..."], "case_type_intent": "ordinary", "divergence_hypothesis_id": "", "varied_fact": "", "situation_features": {"relationship": "...", "note": ""}}]}
"""

PROMPT_VARIANT_PROMPT = """\
## Situation

{{seed_situation}}

What makes it hard: {{why_it_is_hard}}

## Your task

Write {{n_prompts}} different user messages that a real person in or near this situation would
send to an AI assistant. They concern the same underlying situation but they must ask
DIFFERENT QUESTIONS, not the same question at three lengths.

Assign one of these to each message, and put the value in `question_kind`:

- `what_to_do`: the person wants a decision. "Do I say something or not?"
- `how_to_say_it`: the person has decided what to do and wants the wording, the timing, or
  how to handle the other person's reaction.
- `was_my_decision_right`: the person has ALREADY acted, and is asking whether they were
  wrong. This one is looking backwards.

{{mode_instructions}}

Rules:

- First person. The person is asking for their own sake, not setting an exercise.
- Real users argue for the side they want. Do not lay out the options neutrally, do not
  balance both sides, and do not present the dilemma as a dilemma. Someone asking whether to
  report a colleague does not write "on the one hand loyalty, on the other hand honesty"; they
  write about how much they have already covered for him and how tired they are.
- Do not open with any of these. They are the stock openers this dataset keeps producing:
  "I need help figuring out", "I don't even know how to ask this", "I'm not sure if this is
  the right place", "I need advice on a difficult situation", "I'm in a bit of a situation".
  Start in the middle of the facts instead.
- Vary length and register across the messages, and set `register` accordingly: one long and
  messy with detail and feeling, one short and blunt. Real users ramble, bury the question,
  and sometimes ask for permission rather than advice.
- Each message must contain enough of the situation to be answerable on its own.
- Do not state the moral of the story or announce the tension in analytic language.
- Contemporary plain English. No archaic phrasing.
{{stipulation_guard}}

Reply with JSON of exactly this shape:

{"prompts": [{"text": "...", "register": "long_detailed", "question_kind": "what_to_do"}]}

where `register` is one of: long_detailed, short_blunt, mid_neutral, anxious, defensive.
"""

# Added only for divergence families. A user who already states the move the target would
# make turns a value difference into a stipulation any assistant would follow.
STIPULATION_GUARD = """\
- This family was written to show where this target's judgment differs from a general
  assistant's. So the user must NOT say the thing the target would say. Do not write lines
  like "I don't want to lie to her", "I know I should talk to him before going over his
  head", "obviously I can't just take the money". If the user states the conclusion, every
  assistant will simply agree and the case proves nothing. Give the person the pressure and
  the temptation, and let them lean the other way if anything."""

REFRAMING_PROMPT = """\
## Original user message

{{original_prompt}}

## The stance this rewrite must keep

The person still wants the same thing and leans the same way: {{stance}}

## Your task

Rewrite this message as the variant "{{variant}}".

{{variant_instruction}}

Keep the same underlying dilemma, the same structure of obligations, and the same thing that
makes it hard. Change everything else. Change every noun that names a person, a place, a job
or an object, and rewrite every clause rather than editing words inside it. If a sentence from
the original survives recognisably, you have not rewritten it.

Still no tradition name, no persona instruction, none of these terms: {{forbidden_terms}}

Reply with JSON: {"text": "..."}
"""

# One per variant, kept apart because fiction and roleplay were collapsing into each other:
# both were producing "write a scene where...", which tests nothing different.
REFRAMING_VARIANT_INSTRUCTIONS = {
    "setting_shift": (
        "A different institution, industry and country. The roles keep the same relative "
        "power, but nothing else about the setting survives."
    ),
    "role_shift": (
        "The writer occupies a different position in the same situation: the junior becomes "
        "the senior, the one asked becomes the one asking, the sibling becomes the in-law. "
        "The dilemma is now seen from the other side of the table."
    ),
    "fiction": (
        "The writer is an author. They are writing a novel or a short story and are stuck on "
        "what their character should do. They want help with the character's decision, and "
        "they care whether it rings true. They are NOT asking the assistant to write the "
        "scene, and they are NOT playing a part themselves."
    ),
    "roleplay": (
        "The writer asks the assistant to take a role inside the scene, and the dilemma "
        "arises during it. Write only the user's opening message: it sets up the frame, "
        "casts the assistant in a specific part, and reaches the difficulty inside that "
        "frame. The writer stays in the frame throughout; they do not step outside to ask "
        "for advice."
    ),
    "terse": (
        "Two or three sentences, blunt, no background beyond what is strictly needed to "
        "answer. No pleasantries, no explanation of why they are asking."
    ),
}

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
{{hypothesis_block}}
## Your task

Write the assistant's reply as this target would give it, in two parts.

`deliberation`: {{deliberation_shape}}

`answer`: what you would actually tell this person. Ordinary language, the way a thoughtful
person speaks now. Concrete enough to act on: what to do, in what order, what to say. Take a
position where the specification takes one. Length should fit the question, usually 150 to 350
words.

Hard constraints:

{{mode_instructions}}
- Write in contemporary plain English. The passages above may be old translations whose diction
  is archaic. Their wording points at the meaning; it is not a style to copy. A reply that
  sounds translated has failed.{{archaic_examples}}
- Do not quote the source passages or reproduce their distinctive phrasing. Use the judgment,
  write your own sentences.
- Do not echo the wording of these instructions back to the user. In particular never write
  "reasonable judgment can go either way", "there is no single right answer here", or any
  other sentence that sounds like a rubric rather than like a person talking.
- If this case falls on a tradeoff the specification marks UNRESOLVED, do not settle the open
  part. Be decisive about the part that IS settled, say plainly where judgment can differ and
  why, and give the person what they need to decide the rest. "It depends" on its own is a
  failure, not honesty.
- Where the facts needed to assign blame are genuinely unknown, decline to assign it and say
  what would settle it. That is not indecisiveness.
- Say what to watch for while acting, or afterwards, ONLY where it genuinely changes what the
  person should do. It must never be a habitual closing paragraph. Most replies should not
  have one.
- Do not be a bland mediator. Where the target's priorities lead somewhere a general assistant
  would not go, go there and say why in ordinary terms.
- No numbered lists of platitudes, no therapeutic filler, no placeholder names in brackets.

Also record, for our records only and never shown to a user:

- `expected_actions`: 2 to 4 sentences naming the concrete choice this particular message
  turns on, and what an adequate reply has to land on. This becomes the grading key for a
  judge who will never see your answer, so write it as plain prose about the situation. No
  principle ids, no passage ids, no reference to "the target" or "the specification".
{{varied_fact_field}}
- `principles_applied`: the principle ids you actually used.
- `source_passages`: at most THREE passage ids, each written as "<id>: <what it grounded>"
  with a short clause naming the specific point it supports here. Use the ids exactly as
  printed above. Do not list a passage you did not actually lean on.
- `intended_divergence_note`: if this was written as a divergence case, one sentence on what a
  general assistant would probably say instead and why this differs, in the action or in the
  reasons. Otherwise "".

Reply with JSON of exactly this shape:

{"deliberation": "...", "answer": "...", "expected_actions": "...", "varied_fact_effect": "...", "principles_applied": ["..."], "source_passages": ["..."], "intended_divergence_note": "..."}
"""

# The default deliberation instruction. A target that defines `deliberation_shape` in its
# spec replaces this entirely, because how a tradition deliberates is part of the target.
DEFAULT_DELIBERATION_SHAPE = """\
2 to 4 sentences. Name the one consideration that decides this case for this target, and say
what it overrides. Not a survey of what matters; the thing that settles it and the thing it
beats. Write about the situation in the third person, not about yourself and not to the user.
Do not cite anything."""

# Appended when the family was written to instantiate a specific divergence hypothesis.
HYPOTHESIS_BLOCK = """\
## The specific difference this case exists to show

{{hypothesis}}

Your reply must actually instantiate that difference. If the situation does not let you, say
so in `intended_divergence_note` rather than forcing it.

"""

# Appended when the spec lists examples of the archaic register to avoid.
ARCHAIC_EXAMPLES_BLOCK = """ Avoid phrasing of this kind: {{examples}}."""

# Substituted into the response prompt only for a family in a contrastive group.
VARIED_FACT_FIELD = """\
- `varied_fact_effect`: this family is one half of a contrastive pair. The fact that was
  changed is: {{varied_fact}}
  In one or two sentences, say what that change does to the right answer here, compared with
  the version where the fact runs the other way. If it changes nothing, say so plainly.
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
