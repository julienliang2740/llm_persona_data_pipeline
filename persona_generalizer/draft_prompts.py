"""Model-facing text for the script arm of the drafter.

Kept apart from the code, as ALL_CAPS constants with {{placeholders}}, following the convention
in `prompts/`. Every prompt here is written for a model working from its own memory: it has no
sources in front of it and cannot check anything, so each pass is asked to mark its own
confidence and to name what a human must verify. See draft_persona.py for why that matters.
"""

SYSTEM_PROMPT = """\
You are researching one person so that a dataset can be built which fine-tunes a language model
to judge as that person judged. You are working from memory alone: you have no sources in front
of you and you cannot look anything up.

That constraint governs everything you produce. Three rules follow from it.

1. Mark your confidence on every claim, and never present a recollection as a citation. If you
   are reconstructing the substance of something rather than recalling its wording, say so.
2. Never produce a verbatim quotation. Paraphrase what the person is understood to have written
   or said, and label it a paraphrase. A fabricated quotation attributed to a real person is the
   single worst output you can produce here.
3. Conduct outranks statements. Where what the person said conflicts with what they did, try to
   explain the gap first — danger, coercion, a view that changed over time — and if no
   explanation holds, what they did governs.

Do not sanitise the subject. Their objectionable views, their failures and their hypocrisies are
part of the persona and must be recorded as plainly as anything admirable. A subject corrected
into a better person is a different person.

You always reply with a single JSON value and nothing else.
"""

SUFFICIENCY_PROMPT = """\
Subject: {{subject}}

Decide whether enough survives about this person to build a persona dataset from.

Judge these, and be honest about how much you actually know rather than how famous they are:

- first_person_volume: roughly how much survives in their own words
- decisions_with_reasoning: how many documented decisions survive where BOTH the act and their
  stated reason are known. This is the binding criterion and most subjects fail it
- domain_breadth: how many areas of life the material covers
- contestedness: how much of the record is legend, hagiography or hostile invention
- testimonial_variety: whether independent observers with differing interests survive

Scope is a SEPARATE question from evidence and you answer it first: not "is there enough
material?" but "should a faithful persona of this subject exist?". A persona spec is
fidelity-maximising — it carries no modern-constraint clause, and the export is training data.
Out of scope regardless of how much survives: living private individuals, and subjects whose
distinctive value content is the direction or advocacy of mass atrocity, where the faithful
rendering and the harmful artefact are the same object. An unattractive record is NOT a reason to
refuse: a stolen election, self-dealing or a shameful voting record is the material, not a defect.

Return JSON:
{"verdict": "admit" | "admit_with_caveats" | "admit_reconstructed"
           | "refuse_acquisition" | "refuse_evidence" | "refuse_scope",
 "first_person_volume": "...", "decisions_with_reasoning": "...", "domain_breadth": "...",
 "contestedness": "...", "testimonial_variety": "...", "caveats": "...",
 "scope_check": "whether this subject is in scope and why; required on any admit verdict",
 "kind": "historical" | "fictional",
 "living_private_individual": true | false,
 "reasoning": "why this verdict"}

The verdicts, and the distinctions that matter:
- refuse_evidence: the material does not survive. Not retryable.
- refuse_acquisition: the material was not RETRIEVED. A fact about the search, not the subject.
  Use this when slots came back empty and the acquisition passes were not exhausted.
- refuse_scope: out of scope whatever the evidence shows. Set living_private_individual, or say
  in scope_check why the subject's value content puts them outside.
- admit_reconstructed: sources thin but real, and part of the corpus will be inference. Say so.
A refusal is a useful answer; say so plainly rather than admitting a subject you cannot ground.
"""

EVIDENCE_PROMPT = """\
Subject: {{subject}}

Assemble the evidence a persona spec is built from. Produce {{target_count}} items{{kind_clause}}.

The full corpus is weighted roughly: a third circumstance, a third deeds, a fifth words, the rest
testimony. All four kinds are described below because you need to know what the others are for
even when this call asks for only one of them.

- circumstance: the socio-economic and psychological conditions that produced them. What money
  meant, what ruin would have meant, their class and legal standing, whose permission they
  needed, the institutions they answered to, what was ordinary to endure in their time and place,
  what education and travel were available to them. THIS IS THE KIND MOST OFTEN SKIPPED AND IT IS
  WHAT GIVES THE PERSONA A WORLD. A persona built from words and deeds alone reads as fluent,
  characterful and weightless.
- deed: something they are documented to have DONE, with the circumstances. Prefer acts recorded
  in registers, minutes, court records and official returns over acts known only from their own
  account. This is the material the conduct-over-words rule stands on.
- words: something they wrote or were recorded saying. PARAPHRASE — never a verbatim quotation.
- testimony: what a contemporary said about them, with that person's interest noted.

Each item:
{"id": "short stable id, e.g. C1 / D3 / W2 / T1",
 "kind": "circumstance" | "deed" | "words" | "testimony",
 "title": "a few words",
 "period": "date or range if known, else empty",
 "body": "2-6 sentences. State in the prose what kind of record this is. For a deed, what they
          did and in what circumstances. For circumstance, the condition AND what it did to them.",
 "bears_on": "what this grounds in the persona",
 "confidence": "high" | "medium" | "low",
 "evidence_basis": "attested" | "reconstructed",
 "verify": "what a human must check against a source"}

evidence_basis is the difference between something a source says and something you inferred from
the surrounding evidence. Mark it "reconstructed" whenever the item is your inference — a
psychological effect nobody recorded, a motive the sources do not state, a circumstance argued
from what was normal at the time. Reconstruction is allowed and expected where sources are thin;
what is not allowed is reconstruction that cannot be seen, because once a passage is in a prompt
an inference reads exactly like a record. Under-marking is the serious error, so when in doubt
mark it reconstructed.

Two consequences you should know: reconstructed passages may not exceed 40% of the corpus, and a
conflict's said/did passages must both be attested, because conduct-over-words cannot adjudicate
a gap that the reconstruction may itself have created.

{{id_clause}}

Return JSON and nothing else: {"evidence": [ ... ]}. No preamble, no planning, no commentary
before or after the object. If you find yourself writing a sentence that is not inside a JSON
string, stop and emit the object.
"""

CONFLICTS_PROMPT = """\
Subject: {{subject}}

Here is the evidence assembled so far:

{{evidence}}

Find where what this person SAID conflicts with what they DID. Look hard; almost everyone has at
least one, and finding none usually means the deeds were researched less than the writings.

For each conflict, attempt a reconciliation BEFORE falling back on conduct. Test: was their life
or livelihood at risk? Were they coerced, or without an alternative? Did their view move over
time, and does the chronology actually support that? Is the statement narrower than it looks, so
the conduct sits inside a carve-out it already made?

Write out what you tested and why each reading does or does not hold. Only when none holds does
conduct govern.

Each conflict:
{"id": "snake_case",
 "said": "the id of the words item",
 "did": "the id of the deed item",
 "reconciliation_attempted": "the readings you tested and why each does or does not hold",
 "resolution": "conduct" | "statement" | "reconciled",
 "consequence_for_the_persona": "what this means the persona actually DOES. Behaviour, not a
   verdict. Do not resolve this by deciding the person was better than the record shows.",
 "confidence": "high" | "medium" | "low"}

Return JSON: {"conflicts": [ ... ]}
"""

SPEC_PROMPT = """\
Subject: {{subject}}

Evidence:

{{evidence}}

Conflicts already adjudicated:

{{conflicts}}

Write the persona specification. Cite evidence ids in every `sources` list; cite only ids that
appear above.

Two rules govern this:

1. The persona is NEVER placed inside modern constraints. Do not write that they operate inside
   anti-discrimination, safeguarding or consent norms. Their views stand as they were.
2. The conflicts above are the authority on what the persona does. Where one resolved to
   `conduct`, the persona does what the person DID, not what they said.

Return JSON with these keys:

{"name": "display name",
 "summary": "2 paragraphs on HOW they judge: what they notice first, what overrides what, what
   they refuse. Carry the unattractive parts as plainly as the attractive ones.",
 "subject": {"kind": "...", "lived": "...", "place": "...", "one_line": "...",
   "canon_boundary": {"attributed": "...", "disputed": "...", "excluded": "..."}},
 "context": {"period": {...}, "material_conditions": {...}, "standing_and_constraint": {...},
   "institutions": {...}, "what_was_ordinary_then": {...},
   "what_was_possible_for_someone_like_her": {...}},
   -- each context block is {"what": "...", "psychological_effect": "what the condition DID to
      them", "sources": ["ids"]}; `period` needs no psychological_effect. Write these fully:
      together with formation they should run well past 400 words.
 "formation": [{"phase": "name (dates)", "what_happened": "...",
   "what_it_left_them_with": "...", "sources": ["ids"]}],
 "principles": [{"id": "P01", "name": "...", "description": "...",
   "positive_indicators": ["..."], "failure_modes": ["..."], "sources": ["ids"]}],
   -- 8 to 12, citing deeds where deeds exist
 "boundaries": [{"principle": "P01", "limit": "...", "sources": ["ids"]}],
 "tradeoffs": [{"id": "...", "description": "...", "considerations": ["..."],
   "intended_lean": "...", "sources": ["ids"]}],
   -- or "unresolved": true with "resolved_part" and "open_question" instead of intended_lean
 "misinterpretations": [{"claim": "the popular version", "correction": "..."}],
 "voice": {"register": "...", "habits": ["..."], "vocabulary": ["..."],
   "never_says": ["..."], "do_not_imitate": "period diction not to copy"},
 "epistemic_horizon": {"cannot_know": "...",
   "policy": "translate_to_analogue" | "acknowledge_unfamiliarity" | "answer_at_principle",
   "policy_notes": "..."},
 "deliberation_shape": "3-5 lines on their ORDER OF ATTENTION. No phrasing, or every response
   opens with the same sentence.",
 "signature_moves": [{"id": "...", "description": "..."}],
 "divergence_hypotheses": [{"id": "...", "description": "where a generic assistant answers
   differently", "example_prompt_shape": "..."}],
 "domains": [{"id": "...", "weight": 0.0, "notes": "..."}],
   -- weights sum to 1; weight toward where the sources are thick
 "cue_policy": {"forbidden_terms": ["the person, their works, their setting"],
   "allowed_terms": ["ordinary words the persona needs"], "soft_terms": ["phrase-shaped tells"],
   "archaic_register_examples": ["diction not to imitate"]},
 "redistribution_note": "distribution limits, including any arising from the persona's own views"}
"""


SOURCED_PREAMBLE = """\
You have been given excerpts from pages retrieved from the web for this subject, grouped by the
coverage slot each search was aimed at. They are raw and uneven: some are useful, some are
irrelevant, some are popular summaries repeating one underlying source.

Use them as follows.

- Prefer what the retrieved material supports over what you remember. Where they disagree, say so
  in `verify` and trust the material less than a primary source you can name.
- Trace a claim to its earliest source. Twenty pages repeating one biography are one source, not
  twenty; do not let repetition raise your confidence.
- Anything attested only in popular treatment — a novel, a film, a listicle — is not evidence.
  Mark it low confidence and say it belongs in the disputed or excluded part of canon_boundary.
- Where the retrieved material does not cover a slot, say so rather than filling the gap from
  memory. A recorded gap is a result.
- Set `source_url` on any item that a retrieved page actually supports, and leave it empty
  otherwise. Do not attach a URL to a claim the page does not make.

RETRIEVED MATERIAL

{{sources}}

END OF RETRIEVED MATERIAL
"""
