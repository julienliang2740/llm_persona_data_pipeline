#!/usr/bin/env python
"""Validate a persona spec: the target schema, plus the persona sections, plus the gate.

    python persona_generalizer/check_persona.py <persona_id>
    python persona_generalizer/check_persona.py --all

`main.py check` already validates everything the pipeline needs to run. It knows nothing about
the persona sections, so a persona spec can pass it while carrying a `refuse` verdict, a conflict
that resolves to nothing, or an attribution policy that never reaches the manifest. This runs
that check first and then the persona-only rules on top.

Every problem is reported at once, following the same idiom as `main.py check`: one run of the
checker should fix one round of edits. Errors block; warnings are things a reviewer should look
at and may knowingly accept.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.target import SpecError, TargetSpec, load_target  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scope as scope_rules  # noqa: E402

PERSONAS_DIR = REPO_ROOT / "persona_generalizer" / "personas"

REQUIRED_SECTIONS = (
    "subject",
    "context",
    "formation",
    "voice",
    "epistemic_horizon",
    "sufficiency",
    "attribution_policy",
)

# The gate's criteria. `decisions_with_reasoning` is the binding one: a subject can leave a
# great deal of prose behind and still leave almost no decisions where both the act and the
# reason survive, and that is the material a persona is actually built from.
SUFFICIENCY_CRITERIA = (
    "first_person_volume",
    "decisions_with_reasoning",
    "domain_breadth",
    "contestedness",
)
# The gate answers two different questions and used to collapse them into one word. `refuse`
# meant both "the material does not exist" and "I could not find the material", and only the
# second is a bug in the acquisition pass rather than a fact about the subject. They are split
# so that a refusal states which it is, and so a retry is aimed at the one that is retryable.
#
#   admit                  every criterion met
#   admit_with_caveats     one criterion thin; say which
#   admit_reconstructed    buildable, but part of the corpus is inference rather than
#                          attestation. Requires evidence_basis on every passage, holds the
#                          reconstruction share under RECONSTRUCTED_SHARE_CEILING, and travels
#                          into the export manifest so a downstream consumer can see it
#   refuse_acquisition     could not retrieve the material. RETRYABLE: record what was tried
#                          in sufficiency.acquisition_attempts and run the gate again
#   refuse_evidence        the material does not exist. Not retryable
#   refuse_scope           out of scope whatever the evidence shows. A different axis from the
#                          gate's criteria: see persona_generalizer/scope.py
#   refuse                 deprecated alias for refuse_evidence; warns
VERDICTS = (
    "admit",
    "admit_with_caveats",
    "admit_reconstructed",
    "refuse_acquisition",
    "refuse_evidence",
    "refuse_scope",
    "refuse",
)
BLOCKING_VERDICTS = (
    "refuse", "refuse_acquisition", "refuse_evidence", "refuse_scope",
)

# A persona built more than half out of inference is a portrait of the researcher. The ceiling
# is a share of passages rather than of words so that a few long reconstructed essays cannot
# outweigh many short attested ones.
RECONSTRUCTED_SHARE_CEILING = 0.4
CONFLICT_RESOLUTIONS = ("conduct", "statement", "reconciled")
HORIZON_POLICIES = (
    "translate_to_analogue",
    "acknowledge_unfamiliarity",
    "answer_at_principle",
    "refuse",
)
SUBJECT_KINDS = ("historical", "fictional")

# The conditions that produced the person. These are required, and required in this shape,
# because the failure they guard against is a real one: it is easy to write sixteen vivid
# passages of what someone said and did and leave their world as four lines of unsourced prose.
# A persona built that way is fluent, characterful and weightless. Where the sources genuinely do
# not record something, say so in `what` — "unknown; no record survives" is itself informative.
REQUIRED_CONTEXT_FIELDS = (
    "period",
    "material_conditions",
    "standing_and_constraint",
    "institutions",
    "what_was_ordinary_then",
    "what_was_possible_for_someone_like_her",
)
# `period` is scene-setting; the rest have to say what the condition did to the person.
CONTEXT_FIELDS_NEEDING_EFFECT = tuple(f for f in REQUIRED_CONTEXT_FIELDS if f != "period")
# Below this the context is a summary, not the material the persona rests on.
CONTEXT_PROSE_FLOOR_WORDS = 400

# The spec is the seed for a dataset, not the dataset: configs/full.yaml expands one spec into
# about 240 scenario families and roughly 500 training rows. The four reviewed value-system
# targets carry 49-128 passages and 5,100-8,300 words, so a persona wanting comparable output
# needs comparable input. The ceiling is real too: key_passages.md goes into every generation
# prompt, so its size is a per-call token budget rather than storage.
PASSAGE_FLOOR = 60
PASSAGE_WORDS_FLOOR = 6000
PASSAGE_WORDS_CEILING = 8000

# Phrases the value-system targets use to place a tradition inside modern norms. A persona spec
# that grows one has had its purpose reversed, so the absence is asserted rather than reviewed.
MODERN_CONSTRAINT_MARKERS = (
    "modern constraints:",
    "operates inside them",
    "operates inside these",
)


class Report:
    """Errors block; warnings are for a human to accept or act on."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def _missing(container: Any, key: str) -> bool:
    return not (isinstance(container, dict) and container.get(key))


def check_sufficiency(raw: dict[str, Any], report: Report) -> str:
    """The admissibility gate. A `refuse` verdict is a real answer and must stop the build."""
    sufficiency = raw.get("sufficiency")
    if not isinstance(sufficiency, dict):
        report.error("sufficiency: missing. Run the gate before writing the rest of the spec.")
        return ""

    verdict = str(sufficiency.get("verdict") or "").strip()
    if verdict not in VERDICTS:
        report.error(
            f"sufficiency.verdict is {verdict!r}; expected one of {', '.join(VERDICTS)}."
        )
    elif verdict == "refuse":
        report.error(
            "sufficiency.verdict is 'refuse', so this subject is not admissible and the spec "
            "must not be built out. A spec written past a refusal is the researcher's "
            "imagination wearing a real name. Record the refusal and stop."
        )
        report.warn(
            "sufficiency.verdict 'refuse' is deprecated because it does not say which refusal "
            "this is. Use 'refuse_evidence' when the material does not survive, or "
            "'refuse_acquisition' when it could not be retrieved and a further pass might "
            "reach it."
        )
    elif verdict == "refuse_evidence":
        report.error(
            "sufficiency.verdict is 'refuse_evidence': the material a persona needs does not "
            "survive for this subject, so the spec must not be built out. This is a finding "
            "about the sources, not about the search; a further acquisition pass will not "
            "change it."
        )
    elif verdict == "refuse_acquisition":
        report.error(
            "sufficiency.verdict is 'refuse_acquisition': the material was not retrieved, which "
            "is a fact about the search rather than about the subject. Do not build the spec "
            "out on what was reached. Escalate the acquisition pass and run the gate again; if "
            "the material genuinely does not survive, record 'refuse_evidence' instead."
        )
        if _missing(sufficiency, "acquisition_attempts"):
            report.error(
                "sufficiency.acquisition_attempts: missing, and 'refuse_acquisition' claims the "
                "search fell short. Record what was tried — tiers, languages, sites declined — "
                "so the next pass escalates instead of repeating."
            )

    elif verdict == "refuse_scope":
        report.error(
            "sufficiency.verdict is 'refuse_scope': this subject is out of scope for a persona "
            "target whatever the evidence shows, so the spec must not be built out. Record the "
            "refusal in personas/_refused/ and stop."
        )

    for criterion in SUFFICIENCY_CRITERIA:
        if _missing(sufficiency, criterion):
            report.error(f"sufficiency.{criterion}: missing; the gate needs every criterion answered.")

    # Scope is a separate axis from the five criteria, and the reason it is a required field
    # rather than an automatic check is that no list can make the judgement. Requiring it means
    # the question is asked once, in writing, by a person, on every spec that gets built.
    if verdict.startswith("admit") and _missing(sufficiency, "scope_check"):
        report.error(
            "sufficiency.scope_check: missing. Every admitted spec must record that scope was "
            "considered and what was concluded — a persona spec is fidelity-maximising and "
            "carries no modern-constraint clause, so whether it should exist is not answered by "
            "the evidentiary criteria. See persona_generalizer/scope.py."
        )

    if verdict == "admit_reconstructed" and _missing(sufficiency, "caveats"):
        report.error(
            "sufficiency.verdict is 'admit_reconstructed' but no caveats are recorded. Say which "
            "criterion forced it and what the reconstructed passages rest on."
        )
    if verdict == "admit_with_caveats" and _missing(sufficiency, "caveats"):
        report.error(
            "sufficiency.verdict is 'admit_with_caveats' but no caveats are recorded. Say which "
            "criterion is thin, and reflect it in the domain weights."
        )
    if verdict == "admit" and sufficiency.get("caveats"):
        report.warn(
            "sufficiency.verdict is 'admit' but caveats are recorded; consider "
            "'admit_with_caveats' so the thin area is visible downstream."
        )
    return verdict


def check_subject(raw: dict[str, Any], report: Report) -> None:
    subject = raw.get("subject")
    if not isinstance(subject, dict):
        report.error("subject: missing.")
        return

    kind = str(subject.get("kind") or "").strip()
    if kind not in SUBJECT_KINDS:
        report.error(f"subject.kind is {kind!r}; expected 'historical' or 'fictional'.")

    boundary = subject.get("canon_boundary")
    if not isinstance(boundary, dict):
        report.error(
            "subject.canon_boundary: missing. Without it the persona becomes the legend that "
            "accreted around the person."
        )
        return
    if _missing(boundary, "attributed"):
        report.error("subject.canon_boundary.attributed: missing; say what is genuinely theirs.")
    if _missing(boundary, "disputed") and _missing(boundary, "excluded"):
        report.warn(
            "subject.canon_boundary records nothing as disputed or excluded. Almost every subject "
            "has apocrypha; finding none usually means it has not been looked for."
        )


def check_conflicts(raw: dict[str, Any], spec: TargetSpec, report: Report) -> dict[str, int]:
    """Where the record and the rhetoric pull apart. This is conduct-over-words made checkable."""
    known_ids = {passage.id for passage in spec.key_passages}
    tally: dict[str, int] = {resolution: 0 for resolution in CONFLICT_RESOLUTIONS}

    # Absent and empty mean different things. An absent key means the question was never asked,
    # which blocks; an empty list is a researcher saying they looked and found none, which is
    # unusual enough to flag but is theirs to assert.
    if "conflicts" not in raw:
        report.error(
            "conflicts: missing. The section is where conduct-over-words is adjudicated; write "
            "an empty list if the sources genuinely show no gap between word and deed."
        )
        return tally
    conflicts = raw.get("conflicts")
    if not isinstance(conflicts, list):
        report.error("conflicts: must be a list.")
        return tally
    if not conflicts:
        report.warn(
            "conflicts: none recorded. A subject whose words and conduct never diverge is rare; "
            "more often the deeds have not been researched as hard as the writings."
        )
        return tally

    for index, conflict in enumerate(conflicts):
        where = f"conflicts[{index}] ({conflict.get('id', 'no id')})"
        if _missing(conflict, "id"):
            report.error(f"{where}: has no 'id'.")

        for field in ("said", "did"):
            value = conflict.get(field)
            if not value:
                report.error(f"{where}: has no '{field}'.")
            elif value not in known_ids:
                report.error(
                    f"{where}: '{field}' cites passage id {value!r}, which is not in "
                    f"key_passages.md. Passage ids are parsed only from that file."
                )

        resolution = str(conflict.get("resolution") or "").strip()
        if resolution not in CONFLICT_RESOLUTIONS:
            report.error(
                f"{where}: resolution is {resolution!r}; expected one of "
                f"{', '.join(CONFLICT_RESOLUTIONS)}."
            )
        else:
            tally[resolution] += 1

        if _missing(conflict, "reconciliation_attempted"):
            report.error(
                f"{where}: resolves without recording an attempt to reconcile the gap. The rule "
                f"is to explain the conflict first — danger, coercion, a view that moved — and "
                f"fall back to conduct only when no reading holds."
            )
        if _missing(conflict, "consequence_for_the_persona"):
            report.error(
                f"{where}: states no consequence_for_the_persona, so the finding never reaches "
                f"the data. Write it as behaviour, not as a verdict."
            )
    return tally


def _check_sources(value: Any, known_ids: set[str], where: str, report: Report) -> None:
    sources = value.get("sources") if isinstance(value, dict) else None
    if not sources:
        report.error(f"{where}: cites no sources; this material is grounded like any other.")
        return
    missing = [s for s in sources if s not in known_ids]
    if missing:
        report.error(f"{where}: cites passage ids not in key_passages.md: {missing}.")


def _prose_words(value: Any) -> int:
    """Total words across the prose fields of a nested block, for the thinness check."""
    if isinstance(value, str):
        return len(value.split())
    if isinstance(value, dict):
        return sum(_prose_words(v) for k, v in value.items() if k != "sources")
    if isinstance(value, list):
        return sum(_prose_words(v) for v in value)
    return 0


def check_context(raw: dict[str, Any], spec: TargetSpec, report: Report) -> None:
    """The socio-economic and psychological conditions that produced the person."""
    context = raw.get("context")
    if not isinstance(context, dict):
        report.error("context: missing.")
        return

    known_ids = {passage.id for passage in spec.key_passages}
    for field in REQUIRED_CONTEXT_FIELDS:
        value = context.get(field)
        if not value:
            report.error(f"context.{field}: missing.")
            continue
        if not isinstance(value, dict) or _missing(value, "what"):
            report.error(
                f"context.{field}: expected a block with 'what' and 'sources'. A bare paragraph "
                f"is what this schema exists to prevent."
            )
            continue
        _check_sources(value, known_ids, f"context.{field}", report)
        if field in CONTEXT_FIELDS_NEEDING_EFFECT and _missing(value, "psychological_effect"):
            report.warn(
                f"context.{field}: no psychological_effect. The condition is recorded but not "
                f"what it did to the person, which is the half that reaches the persona."
            )


def check_formation(raw: dict[str, Any], spec: TargetSpec, report: Report) -> None:
    formation = raw.get("formation")
    if not isinstance(formation, list) or not formation:
        report.error("formation: missing or empty; a persona needs the events that shaped it.")
        return
    known_ids = {passage.id for passage in spec.key_passages}
    for index, phase in enumerate(formation):
        where = f"formation[{index}] ({phase.get('phase', 'unnamed')})"
        for field in ("phase", "what_happened", "what_it_left_them_with"):
            if _missing(phase, field):
                report.error(f"{where}: has no '{field}'.")
        _check_sources(phase, known_ids, where, report)


def check_context_is_not_thin(raw: dict[str, Any], report: Report) -> None:
    """Guard the specific regression: rich words-and-deeds, threadbare world."""
    words = _prose_words(raw.get("context")) + _prose_words(raw.get("formation"))
    if words < CONTEXT_PROSE_FLOOR_WORDS:
        report.warn(
            f"context and formation come to {words} words, under the {CONTEXT_PROSE_FLOOR_WORDS} "
            f"expected. The period someone grew up in, their circumstances and what happened to "
            f"them are the forces that produced the persona, not background for it; give them "
            f"the weight the words and deeds get."
        )


def check_voice(raw: dict[str, Any], report: Report) -> None:
    voice = raw.get("voice")
    if not isinstance(voice, dict):
        report.error("voice: missing; the tagged in-voice slice has nothing to render.")
        return
    if _missing(voice, "register"):
        report.error("voice.register: missing.")
    if _missing(voice, "do_not_imitate"):
        report.warn(
            "voice.do_not_imitate: missing. Period diction from the source documents is "
            "furniture, not voice, and the generator will copy it unless told not to."
        )
    if _missing(voice, "never_says"):
        report.warn("voice.never_says: empty; the negative space is what makes a voice checkable.")


def check_epistemic_horizon(raw: dict[str, Any], report: Report) -> None:
    horizon = raw.get("epistemic_horizon")
    if not isinstance(horizon, dict):
        report.error(
            "epistemic_horizon: missing. Generated scenarios are contemporary, so the spec has "
            "to say what the subject cannot know and what they do about it."
        )
        return
    policy = str(horizon.get("policy") or "").strip()
    if policy not in HORIZON_POLICIES:
        report.error(
            f"epistemic_horizon.policy is {policy!r}; expected one of {', '.join(HORIZON_POLICIES)}."
        )
    if _missing(horizon, "cannot_know"):
        report.error("epistemic_horizon.cannot_know: missing; name the limits concretely.")


def check_attribution(raw: dict[str, Any], report: Report) -> None:
    policy = raw.get("attribution_policy")
    if not isinstance(policy, dict):
        report.error(
            "attribution_policy: missing. Every generated row is a construction in a real "
            "person's voice; the dataset has to say so."
        )
        return
    if _missing(policy, "statement"):
        report.error("attribution_policy.statement: missing.")
    if policy.get("declare_in_manifest") is not True:
        report.error(
            "attribution_policy.declare_in_manifest must be true, so the constraint travels with "
            "the export the way source licences already do."
        )
    if str(policy.get("subject_status") or "").strip() == "living_private_individual":
        report.error(
            "attribution_policy.subject_status is 'living_private_individual', which is out of "
            "scope. Public figures, historical subjects and fictional characters are in scope."
        )


def check_no_modern_constraint_clause(spec: TargetSpec, report: Report) -> None:
    """Persona specs place the subject inside nothing. Fidelity governs the content."""
    summary = (spec.summary or "").lower()
    for marker in MODERN_CONSTRAINT_MARKERS:
        if marker in summary:
            report.error(
                f"summary contains {marker!r}, the modern-constraint clause the value-system "
                f"targets use. Persona specs must not carry it: conflicts with contemporary "
                f"norms are declared in redistribution_note and the manifest, not applied to "
                f"the content."
            )
            return


def check_corpus_volume(spec: TargetSpec, persona_id: str, report: Report) -> None:
    """Is there enough grounding material to expand into a dataset, and not so much it overflows?

    Skipped for template ids (a leading underscore), which are deliberately small examples that
    exist to be copied and deleted rather than generated from.
    """
    if persona_id.startswith("_"):
        return
    count = len(spec.key_passages)
    words = sum(len(passage.text.split()) for passage in spec.key_passages)
    if count < PASSAGE_FLOOR:
        report.warn(
            f"{count} passages, under the {PASSAGE_FLOOR} expected. The reviewed targets carry "
            f"49-128, and one spec has to expand into roughly 500 training rows; a thin corpus "
            f"produces repetitive scenarios rather than fewer of them."
        )
    if words < PASSAGE_WORDS_FLOOR:
        report.warn(
            f"key_passages.md holds {words} words, under the {PASSAGE_WORDS_FLOOR} expected "
            f"(the reviewed targets run 5,100-8,300)."
        )
    elif words > PASSAGE_WORDS_CEILING:
        report.warn(
            f"key_passages.md holds {words} words, over the {PASSAGE_WORDS_CEILING} ceiling. It "
            f"is placed into every generation prompt, so this is a per-call token budget: curate "
            f"down and record in research_notes.md what was left out."
        )


def check_scope(raw: dict[str, Any], verdict: str, report: Report) -> None:
    """The cheap stop, applied to the spec's own name.

    A tripwire, not a filter — see persona_generalizer/scope.py. It exists so that an obvious
    case fails at the checker rather than after a dataset has been generated from it.
    """
    name = str(raw.get("name") or "")
    hit = scope_rules.tripwire_match(name)
    if hit and verdict != scope_rules.SCOPE_VERDICT:
        needle, why = hit
        report.error(
            f"name {name!r} matches the scope tripwire ({needle}: {why}), but the verdict is "
            f"{verdict!r}. Out-of-scope subjects are refused whatever the evidence shows; set "
            f"sufficiency.verdict to '{scope_rules.SCOPE_VERDICT}' and do not build the spec out."
        )


def check_evidence_basis(
    spec: TargetSpec, raw: dict[str, Any], verdict: str, report: Report
) -> dict[str, int]:
    """How much of the corpus is inference, and is the inference in a place it can do harm?

    Reconstruction is allowed — the sources for most people are incomplete and a persona that
    refused every gap would be unbuildable. What is not allowed is reconstruction that cannot be
    seen: an inferred passage reads exactly like an attested one once it is in a prompt, and a
    row generated from it is indistinguishable from evidence in the exported dataset.
    """
    tally = {"attested": 0, "reconstructed": 0}
    known_bases = {"attested", "reconstructed"}

    for passage in spec.key_passages:
        basis = passage.evidence_basis
        if basis not in known_bases:
            report.error(
                f"key_passages.md [{passage.id}]: evidence_basis is {basis!r}; expected "
                f"'attested' or 'reconstructed'."
            )
            continue
        tally[basis] += 1

    total = sum(tally.values())
    reconstructed = tally["reconstructed"]

    if verdict == "admit_reconstructed":
        undeclared = [p.id for p in spec.key_passages if not p.evidence_basis_declared]
        if undeclared:
            report.error(
                f"sufficiency.verdict is 'admit_reconstructed', so every passage must declare an "
                f"'evidence_basis:' line rather than relying on the default. "
                f"{len(undeclared)} do not: {', '.join(undeclared[:8])}"
                + (" ..." if len(undeclared) > 8 else "")
            )
        if reconstructed == 0:
            report.warn(
                "sufficiency.verdict is 'admit_reconstructed' but no passage is marked "
                "reconstructed. If the corpus is wholly attested, 'admit' or "
                "'admit_with_caveats' describes it better."
            )
    elif reconstructed and verdict.startswith("admit"):
        report.error(
            f"{reconstructed} passage(s) are marked evidence_basis: reconstructed, but the "
            f"gate verdict is {verdict!r}. A spec carrying reconstruction must say so at the "
            f"gate, so the share travels into the export manifest: use 'admit_reconstructed'."
        )

    if total:
        share = reconstructed / total
        if share > RECONSTRUCTED_SHARE_CEILING:
            report.error(
                f"{reconstructed} of {total} passages ({share:.0%}) are reconstructed, over the "
                f"{RECONSTRUCTED_SHARE_CEILING:.0%} ceiling. Past this the persona is mostly the "
                f"researcher. Acquire more, or record a refusal."
            )
        elif share > RECONSTRUCTED_SHARE_CEILING / 2:
            report.warn(
                f"{reconstructed} of {total} passages ({share:.0%}) are reconstructed. Under the "
                f"ceiling, but a reviewer should confirm the attested half carries the persona."
            )

    # The conduct-over-words rule is the one thing that cannot run on inference. A conflict
    # weighs what someone said against what they did; if either side is reconstructed, the gap
    # being adjudicated may be one the researcher created.
    reconstructed_ids = {p.id for p in spec.key_passages if p.evidence_basis == "reconstructed"}
    for index, conflict in enumerate(raw.get("conflicts") or []):
        if not isinstance(conflict, dict):
            continue
        where = f"conflicts[{index}] ({conflict.get('id', 'no id')})"
        for field_name in ("said", "did"):
            cited = conflict.get(field_name)
            if cited in reconstructed_ids:
                report.error(
                    f"{where}: '{field_name}' cites {cited!r}, which is marked "
                    f"evidence_basis: reconstructed. A conflict adjudicates what a person said "
                    f"against what they did, so both sides must be attested — otherwise the gap "
                    f"may be one the reconstruction invented."
                )
    return tally


def check_general(spec: TargetSpec, raw: dict[str, Any], report: Report) -> None:
    if len(spec.principles) < 8:
        report.warn(
            f"{len(spec.principles)} principles; the schema asks for 8-16. Fewer than 8 usually "
            f"means the persona is a sketch."
        )
    weights = [float(d.get("weight", 0) or 0) for d in spec.domains]
    total = sum(weights)
    if weights and abs(total - 1.0) > 0.01:
        report.warn(f"domain weights sum to {total:.2f}, not 1.00.")
    if not raw.get("redistribution_note"):
        report.warn(
            "redistribution_note: missing. A faithful persona export can carry positions "
            "unacceptable in a contemporary product; say so here."
        )


def check_persona(persona_id: str, personas_dir: Path = PERSONAS_DIR) -> int:
    """Return 0 when the spec is usable, 2 otherwise. Prints every problem at once."""
    try:
        spec = load_target(personas_dir, persona_id, strict=True)
    except SpecError as error:
        print(f"{persona_id}: NOT OK (target schema)\n{error}", file=sys.stderr)
        return 2

    raw = spec.raw
    report = Report()

    for section in REQUIRED_SECTIONS:
        if not raw.get(section):
            report.error(f"{section}: missing; required by the persona schema.")

    verdict = check_sufficiency(raw, report)
    check_subject(raw, report)
    check_scope(raw, verdict, report)
    check_context(raw, spec, report)
    tally = check_conflicts(raw, spec, report)
    check_formation(raw, spec, report)
    check_context_is_not_thin(raw, report)
    check_voice(raw, report)
    check_epistemic_horizon(raw, report)
    check_attribution(raw, report)
    check_no_modern_constraint_clause(spec, report)
    check_corpus_volume(spec, persona_id, report)
    basis_tally = check_evidence_basis(spec, raw, verdict, report)
    check_general(spec, raw, report)

    subject = raw.get("subject") or {}
    passages = [p.id for p in spec.key_passages]

    if report.errors:
        print(f"{persona_id}: NOT OK — {len(report.errors)} problem(s)", file=sys.stderr)
        for problem in report.errors:
            print(f"  ERROR   {problem}", file=sys.stderr)
        for problem in report.warnings:
            print(f"  warning {problem}", file=sys.stderr)
        return 2

    resolutions = ", ".join(f"{count} {name}" for name, count in tally.items() if count) or "none"
    print(
        "\n".join(
            [
                f"{persona_id}: OK (persona, strict)",
                f"  {spec.name} v{spec.version}"
                + (f"  [{subject.get('kind')}, {subject.get('lived')}]" if subject else ""),
                f"  sufficiency: {verdict}",
                f"  principles: {len(spec.principles)}   tradeoffs: {len(spec.tradeoffs)}"
                f"   divergence hypotheses: {len(spec.divergence_hypotheses)}",
                f"  passages: {len(passages)} ({sum(len(p.text.split()) for p in spec.key_passages)} words)"
                f"   formation phases: {len(raw.get('formation') or [])}"
                f"   context+formation: {_prose_words(raw.get('context')) + _prose_words(raw.get('formation'))} words",
                f"  conflicts: {len(raw.get('conflicts') or [])} ({resolutions})",
                *(
                    [
                        f"  evidence basis: {basis_tally['attested']} attested, "
                        f"{basis_tally['reconstructed']} reconstructed "
                        f"({basis_tally['reconstructed'] / max(1, sum(basis_tally.values())):.0%})"
                    ]
                    if basis_tally["reconstructed"]
                    else []
                ),
                f"  epistemic horizon: {(raw.get('epistemic_horizon') or {}).get('policy')}",
                f"  attribution declared in manifest: "
                f"{(raw.get('attribution_policy') or {}).get('declare_in_manifest')}",
            ]
        )
    )
    for problem in report.warnings:
        print(f"  warning {problem}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_persona.py",
        description="Validate a persona spec and run the admissibility gate.",
    )
    parser.add_argument("persona_id", nargs="?", help="directory name under personas/")
    parser.add_argument("--all", action="store_true", help="check every persona")
    parser.add_argument(
        "--personas-dir", default=None, help="override persona_generalizer/personas"
    )
    args = parser.parse_args(argv)

    personas_dir = Path(args.personas_dir) if args.personas_dir else PERSONAS_DIR
    if args.all:
        ids = sorted(p.name for p in personas_dir.iterdir() if (p / "spec.yaml").exists())
        if not ids:
            print(f"no personas found under {personas_dir}", file=sys.stderr)
            return 2
        return max(check_persona(persona_id, personas_dir) for persona_id in ids)
    if not args.persona_id:
        parser.error("give a persona id, or --all")
    return check_persona(args.persona_id, personas_dir)


if __name__ == "__main__":
    raise SystemExit(main())
