"""Reviewer critique and the revise round.

The reviewer scores a response against the target, and a `revise` verdict costs an actual
rewrite followed by a fresh review rather than an annotation on a kept record.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from typing import Any

from pipeline.config import RunConfig
from pipeline.model import ModelClient, gather_bounded
from pipeline.records import Family, Prompt, Response, Review, short_id
from pipeline.similarity import _comparison_text  # noqa: F401  (re-exported for callers)
from pipeline.target import (
    TargetSpec,
    render_for_reviewer,
    render_key_passages,
    render_open_questions,
    render_signature_moves,
)
from prompts import render
from prompts.review import (
    ALLOWED_TERMS_NOTE,
    FIDELITY_REVIEW_PROMPT,
    REVIEWER_SYSTEM_PROMPT,
    SIGNATURE_MOVES_NOTE,
    SOFT_TERMS_NOTE,
)

logger = logging.getLogger("pipeline.review")


async def _review_responses(
    client: ModelClient,
    config: RunConfig,
    spec: TargetSpec,
    prompts_by_id: dict[str, Prompt],
    families_by_id: dict[str, Family],
    responses: list[Response],
    existing: list[Review],
    layer_ids: list[str] | None = None,
    reviewer_role_name: str = "reviewer",
) -> list[Review]:
    reviewer = config.role(reviewer_role_name)
    reviewed = {review.response_id for review in existing}
    todo = [r for r in responses if r.response_id not in reviewed]
    if not todo:
        return existing
    spec_text = render_for_reviewer(spec, layer_ids)
    forbidden = ", ".join(spec.forbidden_terms) or "(none)"
    soft_terms_note = (
        render(SOFT_TERMS_NOTE, soft_terms=", ".join(spec.soft_terms)) if spec.soft_terms else ""
    )
    allowed_terms_note = (
        render(ALLOWED_TERMS_NOTE, allowed_terms=", ".join(spec.allowed_terms))
        if spec.allowed_terms
        else ""
    )
    moves_text = render_signature_moves(spec)
    signature_moves = render(SIGNATURE_MOVES_NOTE, moves=moves_text) if moves_text else ""
    open_questions = render_open_questions(spec)

    async def review_one(response: Response) -> Review | None:
        prompt = prompts_by_id.get(response.prompt_id)
        if prompt is None:
            return None
        family = families_by_id.get(prompt.family_id)
        tradeoff_ids = family.tradeoff_ids if family else []
        tradeoff_summary = "; ".join(
            f"{tid}"
            + (" (UNRESOLVED: a confident resolution is a defect)"
               if (spec.tradeoff(tid) or {}).get("unresolved") else "")
            for tid in tradeoff_ids
        ) or "(none recorded)"
        messages = [
            {"role": "system", "content": REVIEWER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": render(
                        FIDELITY_REVIEW_PROMPT,
                        target_spec=spec_text,
                        key_passages=render_key_passages(
                            spec, response.hidden.get("source_passages") or None, max_chars=4000
                        ),
                        user_prompt=prompt.text,
                        deliberation=response.deliberation,
                        answer=response.answer,
                        principles_claimed=", ".join(response.hidden.get("principles_applied") or []),
                        passages_claimed=", ".join(response.hidden.get("source_passages") or []),
                        tradeoff_summary=tradeoff_summary,
                        why_it_is_hard=(family.why_it_is_hard if family else "(not recorded)"),
                        open_questions=open_questions,
                        forbidden_terms=forbidden,
                        allowed_terms_note=allowed_terms_note,
                        soft_terms_note=soft_terms_note,
                    signature_moves=signature_moves,
                ),
            },
        ]
        payload, _ = await client.complete_json(
            reviewer, messages, stage="validate.review", record_id=response.response_id
        )
        missing = missing_score_keys(payload)
        if missing:
            # A missing boolean reads as false, which silently clears a defect flag.
            logger.warning(
                "review of %s omitted score keys %s; asking once more",
                response.response_id,
                missing,
            )
            payload, _ = await client.complete_json(
                reviewer,
                messages
                + [
                    {"role": "assistant", "content": json.dumps(payload)[:3000]},
                    {
                        "role": "user",
                        "content": (
                            "That reply omitted these required keys inside `scores`: "
                            + ", ".join(missing)
                            + ". Reply again with the complete JSON object, every score key "
                            "present, and nothing else."
                        ),
                    },
                ],
                stage="validate.review.repair",
                record_id=response.response_id,
            )
        return _review_from_payload(payload, response, reviewer.model)

    results = await gather_bounded([review_one(response) for response in todo])
    reviews = list(existing)
    for result in results:
        if isinstance(result, Exception):
            logger.error("review failed: %s", result)
            continue
        if result is not None:
            reviews.append(result)
    return reviews


REQUIRED_SCORE_KEYS = (
    "fidelity",
    "judgment_not_terminology",
    "scenario_quality",
    "cue_leakage",
    "confident_on_unresolved",
    "formulaic_shape",
    "prompt_stipulates_move",
    "quoted_source_text",
    "archaic_register",
)


def missing_score_keys(payload: Any) -> list[str]:
    """Score keys the reviewer left out. A missing boolean silently reads as false."""
    scores = (payload or {}).get("scores") or {}
    return [key for key in REQUIRED_SCORE_KEYS if key not in scores]


#: Flags that cap `judgment_not_terminology`, and the reason each one does.
JUDGMENT_CAP = 3
CAPPING_FLAGS = {
    "formulaic_shape": "a fixed paragraph template is a shape, not judgment about this case",
    "archaic_register": "translated-sounding register signals the source rather than reasoning",
}


def _review_from_payload(payload: dict[str, Any], response: Response, reviewer_model: str) -> Review:
    scores = payload.get("scores") or {}
    quote = str(payload.get("judgment_evidence_quote", "")).strip()
    judgment = _as_int(scores.get("judgment_not_terminology"))
    # The rubric states these caps in prose, and a real reviewer ignored them: a smoke
    # call returned 5 for judgment_not_terminology while setting formulaic_shape true on
    # the same response. Enforcing them here makes the rubric's words binding.
    capped_by: list[str] = []
    if not quote:
        capped_by.append("no judgment_evidence_quote")
    for flag, reason in CAPPING_FLAGS.items():
        if scores.get(flag):
            capped_by.append(f"{flag}: {reason}")
    if capped_by and judgment > JUDGMENT_CAP:
        logger.info(
            "review of %s: judgment_not_terminology %d capped to %d (%s)",
            response.response_id,
            judgment,
            JUDGMENT_CAP,
            "; ".join(capped_by),
        )
    if capped_by:
        judgment = min(judgment, JUDGMENT_CAP)
    return Review(
        review_id=short_id("rev", response.response_id, reviewer_model),
        response_id=response.response_id,
        reviewer_model=reviewer_model,
        scores={
            "fidelity": _as_int(scores.get("fidelity")),
            "judgment_not_terminology": judgment,
            "scenario_quality": _as_int(scores.get("scenario_quality")),
            "cue_leakage": bool(scores.get("cue_leakage")),
            "confident_on_unresolved": bool(scores.get("confident_on_unresolved")),
            "formulaic_shape": bool(scores.get("formulaic_shape")),
            "prompt_stipulates_move": bool(scores.get("prompt_stipulates_move")),
            "quoted_source_text": bool(scores.get("quoted_source_text")),
            "archaic_register": bool(scores.get("archaic_register")),
        },
        issues=[str(issue) for issue in (payload.get("issues") or [])]
        + [f"score capped: {reason}" for reason in capped_by],
        verdict=str(payload.get("verdict", "revise")).lower().strip(),
        rationale=str(payload.get("rationale", "")).strip(),
        judgment_evidence_quote=quote,
        judgment_move=str(payload.get("judgment_move", "")).strip(),
        signature_moves_present=[str(m) for m in (payload.get("signature_moves_present") or [])],
        notes=[str(note) for note in (payload.get("notes") or [])],
    )


#: Boolean score keys that mark a defect. A 5 alongside any of these is a contradiction.
DEFECT_FLAGS = (
    "cue_leakage",
    "confident_on_unresolved",
    "formulaic_shape",
    "prompt_stipulates_move",
    "quoted_source_text",
    "archaic_register",
)
NUMERIC_SCORES = ("fidelity", "judgment_not_terminology", "scenario_quality")


def flag_score_conflicts(reviews: list[Review]) -> dict[str, Any]:
    """Count reviews that award a 5 while also raising a defect flag.

    A reviewer that does both is not applying the rubric: a reply cannot be an exemplar of
    the target's judgment and also carry a template shape or name its own source. Two of
    the flags now cap the judgment score in code, so a surviving conflict means the
    reviewer put the 5 on a dimension the cap does not cover.
    """
    conflicts: Counter[str] = Counter()
    conflicted_reviews = 0
    for review in reviews:
        raised = [flag for flag in DEFECT_FLAGS if review.scores.get(flag)]
        fives = [name for name in NUMERIC_SCORES if _as_int(review.scores.get(name)) >= 5]
        if raised and fives:
            conflicted_reviews += 1
            for flag in raised:
                for name in fives:
                    conflicts[f"{flag}+{name}=5"] += 1
    return {
        "reviews_with_flag_and_five": conflicted_reviews,
        "reviews_total": len(reviews),
        "flag_five_pairs": dict(conflicts.most_common()),
    }


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


async def _revise_flagged_responses(
    client: ModelClient,
    config: RunConfig,
    spec: TargetSpec,
    prompts_by_id: dict[str, Prompt],
    families_by_id: dict[str, Family],
    responses: list[Response],
    reviews: list[Review],
    layer_ids: list[str] | None,
) -> tuple[list[Response], list[Review], int]:
    """Rewrite the responses the reviewer asked to revise, then review them again.

    Round 1 recorded "reviewer asked for revision but all scores pass thresholds" on six
    records and shipped the named defect unfixed. A revise verdict now costs a rewrite,
    and a response that still fails is dropped rather than annotated.
    """
    from pipeline.generate import mode_instructions
    from prompts.generation import GENERATOR_SYSTEM_PROMPT, RESPONSE_REVISION_PROMPT
    from pipeline.target import render_for_generator

    rounds = int(config.validation.get("revise_rounds", 1))
    if rounds <= 0:
        return responses, reviews, 0

    review_by_response = {review.response_id: review for review in reviews}
    to_revise = [
        response
        for response in responses
        if (review_by_response.get(response.response_id) or Review("", "", "", {}, [], "accept", "")).verdict
        == "revise"
    ]
    if not to_revise:
        return responses, reviews, 0

    generator = config.role("generator")
    forbidden = ", ".join(spec.forbidden_terms) or "(none)"
    logger.info("revise: rewriting %d responses the reviewer flagged", len(to_revise))

    async def revise_one(response: Response) -> Response | None:
        prompt = prompts_by_id.get(response.prompt_id)
        family = families_by_id.get(prompt.family_id) if prompt else None
        if prompt is None or family is None:
            return None
        review = review_by_response[response.response_id]
        payload, _ = await client.complete_json(
            generator,
            [
                {"role": "system", "content": GENERATOR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": render(
                        RESPONSE_REVISION_PROMPT,
                        target_spec=render_for_generator(
                            spec,
                            principle_ids=family.principle_ids or None,
                            tradeoff_ids=family.tradeoff_ids or None,
                            layer_ids=layer_ids,
                            stage="responses",
                        ),
                        key_passages=render_key_passages(
                            spec, family.source_passage_ids or None, max_chars=8000
                        ),
                        user_prompt=prompt.text,
                        deliberation=response.deliberation,
                        answer=response.answer,
                        verdict=review.verdict,
                        issues="\n".join(f"- {issue}" for issue in review.issues),
                        rationale=review.rationale,
                        mode_instructions=mode_instructions(prompt.mode, forbidden, spec.name),
                    ),
                },
            ],
            stage="validate.revise",
            record_id=response.response_id,
        )
        answer = str(payload.get("answer", "")).strip()
        if not answer:
            return None
        response.deliberation = str(payload.get("deliberation", "")).strip()
        response.answer = answer
        response.revise_rounds += 1
        return response

    results = await gather_bounded([revise_one(response) for response in to_revise])
    revised: list[Response] = []
    for result in results:
        if isinstance(result, Exception):
            logger.error("revision failed: %s", result)
            continue
        if result is not None:
            revised.append(result)
    if not revised:
        return responses, reviews, 0

    # Re-review only the rewritten ones, replacing their earlier review.
    kept_reviews = [r for r in reviews if r.response_id not in {x.response_id for x in revised}]
    fresh = await _review_responses(
        client, config, spec, prompts_by_id, families_by_id, revised, [], layer_ids
    )
    return responses, kept_reviews + fresh, len(revised)


def _scores_pass(review: Review, min_fidelity: int, min_judgment: int, min_scenario: int) -> bool:
    return (
        _as_int(review.scores.get("fidelity")) >= min_fidelity
        and _as_int(review.scores.get("judgment_not_terminology")) >= min_judgment
        and _as_int(review.scores.get("scenario_quality")) >= min_scenario
    )
