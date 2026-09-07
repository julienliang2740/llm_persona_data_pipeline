"""Validation stage: reviewer critique, cue check, near-duplicates, leakage, divergence.

Every response ends with a Decision recording keep/drop and every reason, so a
researcher can see why anything was dropped without re-running a model.
"""

from __future__ import annotations

import json
import logging
import math
import random
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from pipeline import records
from pipeline.config import RunConfig
from pipeline.model import ModelClient, ModelError, gather_bounded
from pipeline.records import (
    BaselineAnswer,
    Decision,
    DivergenceVerdict,
    Family,
    Prompt,
    Response,
    Review,
    short_id,
)
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
    DIVERGENCE_JUDGE_PROMPT,
    FIDELITY_REVIEW_PROMPT,
    REVIEWER_SYSTEM_PROMPT,
    SIGNATURE_MOVES_NOTE,
    SOFT_TERMS_NOTE,
)

logger = logging.getLogger("pipeline.validate")

WORD = re.compile(r"[a-z0-9']+")


# -- pure checks (no network; unit-tested directly) --------------------------


def find_cue_hits(text: str, forbidden_terms: Sequence[str]) -> list[str]:
    """Return the forbidden terms that appear in `text`, case-insensitive, on word boundaries.

    Multi-word terms are matched as phrases. Substrings inside longer words never match,
    so "lion" does not fire on "million".
    """
    hits: list[str] = []
    for term in forbidden_terms:
        term = str(term).strip()
        if not term:
            continue
        pattern = r"\b" + r"\s+".join(re.escape(part) for part in term.split()) + r"\b"
        if re.search(pattern, text, re.IGNORECASE):
            hits.append(term)
    return hits


def tokenize(text: str) -> set[str]:
    return set(WORD.findall(text.lower()))


def jaccard(left: str, right: str) -> float:
    """Lexical similarity, used when embeddings are unavailable."""
    left_tokens, right_tokens = tokenize(left), tokenize(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def cosine(left: Sequence[float], right: Sequence[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


@dataclass
class DuplicateCluster:
    representative_id: str
    member_ids: list[str]
    similarity: float


def find_near_duplicates(
    item_ids: Sequence[str],
    similarity: Callable[[int, int], float],
    threshold: float,
    group_ids: Sequence[str] | None = None,
    within_group_threshold: float | None = None,
    never_compare_ids: Sequence[str | None] | None = None,
) -> tuple[dict[str, str], list[DuplicateCluster]]:
    """Greedy clustering: the first item seen is kept, later close ones point at it.

    Items in the same group (a scenario family) are compared against a separate, much
    higher threshold. Several prompts per family and reframing variants of an eval prompt
    are deliberately near-identical in situation; only a near-verbatim repeat there is a
    defect. Across families, any close pair is redundant data.

    Pairs sharing a `never_compare_ids` value are skipped entirely. That carries the
    counterfactual groups: two members of a contrastive pair are near-identical on purpose,
    and collapsing them destroys exactly the contrast they were written to draw.

    Returns (duplicate_of by item id, clusters). Deterministic in input order.
    """
    duplicate_of: dict[str, str] = {}
    representatives: list[int] = []
    clusters: dict[int, DuplicateCluster] = {}
    for index, item_id in enumerate(item_ids):
        best_index, best_score, best_threshold = None, 0.0, threshold
        for rep_index in representatives:
            if (
                never_compare_ids is not None
                and never_compare_ids[index] is not None
                and never_compare_ids[index] == never_compare_ids[rep_index]
            ):
                continue
            same_group = (
                group_ids is not None and group_ids[index] == group_ids[rep_index]
            )
            if same_group and within_group_threshold is None:
                continue
            applicable = within_group_threshold if same_group else threshold
            score = similarity(index, rep_index)
            if score >= applicable and score > best_score:
                best_index, best_score, best_threshold = rep_index, score, applicable
        if best_index is not None and best_score >= best_threshold:
            rep_id = item_ids[best_index]
            duplicate_of[item_id] = rep_id
            cluster = clusters.setdefault(
                best_index, DuplicateCluster(rep_id, [rep_id], best_score)
            )
            cluster.member_ids.append(item_id)
            cluster.similarity = max(cluster.similarity, best_score)
        else:
            representatives.append(index)
    return duplicate_of, list(clusters.values())


def max_leakage(
    eval_indices: Sequence[int],
    train_indices: Sequence[int],
    similarity: Callable[[int, int], float],
) -> dict[int, tuple[float, int | None]]:
    """For each eval item, the highest similarity to any train item and which one."""
    out: dict[int, tuple[float, int | None]] = {}
    for eval_index in eval_indices:
        best_score, best_train = 0.0, None
        for train_index in train_indices:
            score = similarity(eval_index, train_index)
            if score > best_score:
                best_score, best_train = score, train_index
        out[eval_index] = (best_score, best_train)
    return out


# -- stage -------------------------------------------------------------------


def _comparison_text(prompt: Prompt, family: Family | None) -> str:
    """What similarity is measured on: the situation, never the answer.

    Generated answers share register and structure, which washes out the scenario signal.
    Measured on round-1 data, one Catholic pair scored 0.784 on prompts alone and 0.412 once
    the answers were included, so a fixed 0.92 threshold could never fire.
    """
    seed = family.seed_situation if family else ""
    return f"{prompt.text}\n\n{seed}".strip()


def calibrated_threshold(
    scores: Sequence[float],
    sigmas: float = 3.0,
    floor: float = 0.0,
    ceiling: float = 0.98,
) -> tuple[float, float, float]:
    """Threshold at median + `sigmas` robust deviations of the pair distribution.

    An absolute cut cannot work across embedding models and traditions: the round-1 cross
    split maxima of 0.42 to 0.59 cosine were simply the embedding floor for English prose,
    nowhere near the configured 0.85.

    Median and MAD rather than mean and sd, because the duplicates are exactly the values
    that sit in the tail and they poison a mean-based cut. On eight pairs holding two
    near-duplicates at 0.81 and 0.83, mean plus three sd came to 0.98 and flagged neither;
    the robust cut lands at 0.21 and flags both. MAD is scaled by 1.4826 so that on a
    normal distribution it estimates the same quantity as the standard deviation.

    The one case it cannot resolve is a set where duplicates are not a minority: if half
    the pairs are near-identical the median sits between the two clusters and nothing is
    flagged. That is why the report always prints the closest pairs with their scores,
    whether or not any crossed the cut.

    Returns (threshold, centre, spread).
    """
    values = sorted(float(score) for score in scores)
    if len(values) < 2:
        return (min(ceiling, max(floor, 1.0)), values[0] if values else 0.0, 0.0)
    centre = _median(values)
    spread = 1.4826 * _median([abs(value - centre) for value in values])
    if spread <= 0:
        # Every pair identical to the median: fall back to the smallest gap that exists.
        gaps = [b - a for a, b in zip(values, values[1:]) if b > a]
        spread = min(gaps) if gaps else 0.0
    threshold = min(ceiling, max(floor, centre + sigmas * spread))
    return (threshold, centre, spread)


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    count = len(ordered)
    if not count:
        return 0.0
    middle = count // 2
    if count % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def all_pair_scores(
    count: int, similarity: Callable[[int, int], float]
) -> list[tuple[float, int, int]]:
    """Every distinct pair's score, for calibration and for the report's top-N table."""
    return [
        (similarity(left, right), left, right)
        for left in range(count)
        for right in range(left + 1, count)
    ]


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


def _review_from_payload(payload: dict[str, Any], response: Response, reviewer_model: str) -> Review:
    scores = payload.get("scores") or {}
    quote = str(payload.get("judgment_evidence_quote", "")).strip()
    judgment = _as_int(scores.get("judgment_not_terminology"))
    if not quote:
        # The rubric says an unevidenced judgment score is capped; enforce it here too so
        # a reviewer that ignores the instruction cannot inflate the score anyway.
        judgment = min(judgment, 3)
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
        issues=[str(issue) for issue in (payload.get("issues") or [])],
        verdict=str(payload.get("verdict", "revise")).lower().strip(),
        rationale=str(payload.get("rationale", "")).strip(),
        judgment_evidence_quote=quote,
        judgment_move=str(payload.get("judgment_move", "")).strip(),
        signature_moves_present=[str(m) for m in (payload.get("signature_moves_present") or [])],
        notes=[str(note) for note in (payload.get("notes") or [])],
    )


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


async def _judge_divergence(
    client: ModelClient,
    config: RunConfig,
    spec: TargetSpec,
    prompts_by_id: dict[str, Prompt],
    families_by_id: dict[str, Family],
    responses_by_prompt: dict[str, Response],
    baselines: list[BaselineAnswer],
    strong_generics: list[BaselineAnswer],
    existing: list[DivergenceVerdict],
) -> list[DivergenceVerdict]:
    """Three-way judging: the candidate, the 7B base, and a strong answer with no spec."""
    judge = config.role("judge") if "judge" in config.roles else config.role("reviewer")
    judged = {verdict.prompt_id for verdict in existing}
    base_by_prompt = {answer.prompt_id: answer for answer in baselines}
    generic_by_prompt = {answer.prompt_id: answer for answer in strong_generics}
    hypothesis_text = {
        str(h.get("id")): " ".join(str(h.get("description", "")).split())
        for h in spec.divergence_hypotheses
        if h.get("id")
    }

    todo = [
        prompt_id
        for prompt_id in base_by_prompt
        if prompt_id not in judged
        and prompt_id in responses_by_prompt
        and prompts_by_id.get(prompt_id)
        and prompts_by_id[prompt_id].case_type == "divergence"
    ]
    if not todo:
        return existing

    verdicts = list(existing)
    comparable: list[str] = []
    for prompt_id in todo:
        base = base_by_prompt[prompt_id]
        generic = generic_by_prompt.get(prompt_id)
        reasons = []
        if base.truncated:
            reasons.append(f"base answer cut off ({base.finish_reason or 'no terminal punctuation'})")
        if generic is None:
            reasons.append("no strong generic answer; run the baseline stage")
        elif generic.truncated:
            reasons.append("strong generic answer cut off")
        if reasons:
            # Round 1 judged 18 truncated baselines as if they had reached a
            # recommendation. An unusable comparison is unverified, never divergent.
            verdicts.append(
                DivergenceVerdict(
                    prompt_id=prompt_id,
                    judge_model=judge.model,
                    diverges=False,
                    kind="none",
                    explanation="not judged",
                    divergence_source="none",
                    unverified_reason="; ".join(reasons),
                )
            )
            continue
        comparable.append(prompt_id)

    async def judge_one(prompt_id: str) -> DivergenceVerdict | None:
        prompt = prompts_by_id[prompt_id]
        family = families_by_id.get(prompt.family_id)
        candidate = responses_by_prompt[prompt_id]
        base = base_by_prompt[prompt_id]
        generic = generic_by_prompt[prompt_id]
        hypothesis_id = (family.divergence_hypothesis_id if family else "") or ""
        # Seeded on the prompt id: random across items, reproducible for one item.
        candidate_first = random.Random(prompt_id).random() < 0.5
        reply_a = candidate.answer
        reply_b, reply_c = (base.text, generic.text) if candidate_first else (generic.text, base.text)
        payload, _ = await client.complete_json(
            judge,
            [
                {
                    "role": "user",
                    "content": render(
                        DIVERGENCE_JUDGE_PROMPT,
                        user_prompt=prompt.text,
                        hypothesis=hypothesis_text.get(hypothesis_id)
                        or "(no specific hypothesis recorded for this family)",
                        reply_a=reply_a,
                        reply_b=reply_b,
                        reply_c=reply_c,
                    ),
                }
            ],
            stage="validate.divergence",
            record_id=prompt_id,
        )
        actions = payload.get("actions") or {}
        pairwise = payload.get("pairwise") or {}
        base_key, generic_key = ("b", "c") if candidate_first else ("c", "b")
        # The judge answers about labels A/B/C; map them back to base and generic.
        vs_base = bool(pairwise.get(f"a_vs_{base_key}"))
        vs_generic = bool(pairwise.get(f"a_vs_{generic_key}"))
        value_named = str(payload.get("value_named", "")).strip()
        source = str(payload.get("divergence_source", "none")).strip().lower()
        # Both gates, not one: an unquoted value claim is not a value difference.
        diverges = bool(value_named) and source == "value"
        return DivergenceVerdict(
            prompt_id=prompt_id,
            judge_model=judge.model,
            diverges=diverges,
            kind=str(payload.get("kind", "none")),
            explanation=str(payload.get("explanation", "")).strip(),
            presented_first="base" if candidate_first else "strong_generic",
            candidate_action=str(actions.get("a", "")).strip(),
            base_action=str(actions.get(base_key, "")).strip(),
            generic_action=str(actions.get(generic_key, "")).strip(),
            closer_to=str(payload.get("closer_to", "")).strip().lower(),
            value_named=value_named,
            divergence_source=source if source in ("value", "capability", "stipulated", "none") else "none",
            hypothesis_id=str(payload.get("hypothesis_id", "")).strip(),
            diverges_vs_base=vs_base,
            diverges_vs_generic=vs_generic,
            generic_differs_from_base=bool(pairwise.get("b_vs_c")),
        )

    results = await gather_bounded([judge_one(prompt_id) for prompt_id in comparable])
    for result in results:
        if isinstance(result, Exception):
            logger.error("divergence judging failed: %s", result)
            continue
        if result is not None:
            verdicts.append(result)
    return verdicts


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


async def _similarity_matrix(
    client: ModelClient, texts: list[str], config: RunConfig
) -> tuple[Callable[[int, int], float], str]:
    """Return a similarity function over text indices and the method actually used."""
    use_embeddings = bool(config.validation.get("use_embeddings", True))
    role = config.roles.get("embeddings")
    if use_embeddings and role is not None and role.enabled and texts:
        try:
            vectors = await client.embed(texts, role, stage="validate.embed")
            return (lambda i, j: cosine(vectors[i], vectors[j])), "embeddings"
        except (ModelError, KeyError) as error:
            logger.warning("embeddings unavailable (%s); falling back to lexical Jaccard", error)
    return (lambda i, j: jaccard(texts[i], texts[j])), "jaccard"


async def run_stage(config: RunConfig, spec: TargetSpec, run_dir: Path) -> dict[str, Any]:
    """Entry point for `main.py validate`."""
    settings = config.validation
    families = records.read_jsonl(run_dir / records.FAMILIES_FILE, Family)
    prompts = records.read_jsonl(run_dir / records.PROMPTS_FILE, Prompt)
    responses = records.read_jsonl(run_dir / records.RESPONSES_FILE, Response)
    baselines = records.read_jsonl(run_dir / records.BASELINE_FILE, BaselineAnswer)
    strong_generics = records.read_jsonl(run_dir / records.STRONG_BASELINE_FILE, BaselineAnswer)
    if not responses:
        raise RuntimeError(
            f"No responses in {run_dir / records.RESPONSES_FILE}. Run the generate stage first."
        )

    from pipeline.plan import selected_layers

    layer_ids = selected_layers(spec, config)
    families_by_id = {family.family_id: family for family in families}
    prompts_by_id = {prompt.prompt_id: prompt for prompt in prompts}
    responses_by_prompt = {response.prompt_id: response for response in responses}

    existing_reviews = records.read_jsonl(run_dir / records.REVIEWS_FILE, Review)
    existing_verdicts = records.read_jsonl(run_dir / records.DIVERGENCE_FILE, DivergenceVerdict)

    async with ModelClient.from_config(config, run_dir / records.USAGE_FILE, "validate") as client:
        reviews = await _review_responses(
            client,
            config,
            spec,
            prompts_by_id,
            families_by_id,
            responses,
            existing_reviews,
            layer_ids,
        )
        responses, reviews, revised_count = await _revise_flagged_responses(
            client, config, spec, prompts_by_id, families_by_id, responses, reviews, layer_ids
        )
        if revised_count:
            records.write_jsonl(run_dir / records.RESPONSES_FILE, responses)
            responses_by_prompt = {response.prompt_id: response for response in responses}
        records.write_jsonl(run_dir / records.REVIEWS_FILE, reviews)

        second_role = config.validation.get("second_reviewer_role")
        if second_role:
            second = await _review_responses(
                client,
                config,
                spec,
                prompts_by_id,
                families_by_id,
                responses,
                records.read_jsonl(run_dir / records.REVIEWS_SECOND_FILE, Review),
                layer_ids,
                reviewer_role_name=str(second_role),
            )
            records.write_jsonl(run_dir / records.REVIEWS_SECOND_FILE, second)

        verdicts = await _judge_divergence(
            client,
            config,
            spec,
            prompts_by_id,
            families_by_id,
            responses_by_prompt,
            baselines,
            strong_generics,
            existing_verdicts,
        )
        records.write_jsonl(run_dir / records.DIVERGENCE_FILE, verdicts)

        ordered = [r for r in responses if r.prompt_id in prompts_by_id]
        texts = [
            _comparison_text(
                prompts_by_id[r.prompt_id],
                families_by_id.get(prompts_by_id[r.prompt_id].family_id),
            )
            for r in ordered
        ]
        similarity, method = await _similarity_matrix(client, texts, config)

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


async def _similarity_matrix(
    client: ModelClient, texts: list[str], config: RunConfig
) -> tuple[Callable[[int, int], float], str]:
    """Return a similarity function over text indices and the method actually used."""
    use_embeddings = bool(config.validation.get("use_embeddings", True))
    role = config.roles.get("embeddings")
    if use_embeddings and role is not None and role.enabled and texts:
        try:
            vectors = await client.embed(texts, role, stage="validate.embed")
            return (lambda i, j: cosine(vectors[i], vectors[j])), "embeddings"
        except (ModelError, KeyError) as error:
            logger.warning("embeddings unavailable (%s); falling back to lexical Jaccard", error)
    return (lambda i, j: jaccard(texts[i], texts[j])), "jaccard"


async def run_stage(config: RunConfig, spec: TargetSpec, run_dir: Path) -> dict[str, Any]:
    """Entry point for `main.py validate`."""
    settings = config.validation
    families = records.read_jsonl(run_dir / records.FAMILIES_FILE, Family)
    prompts = records.read_jsonl(run_dir / records.PROMPTS_FILE, Prompt)
    responses = records.read_jsonl(run_dir / records.RESPONSES_FILE, Response)
    baselines = records.read_jsonl(run_dir / records.BASELINE_FILE, BaselineAnswer)
    strong_generics = records.read_jsonl(run_dir / records.STRONG_BASELINE_FILE, BaselineAnswer)
    if not responses:
        raise RuntimeError(
            f"No responses in {run_dir / records.RESPONSES_FILE}. Run the generate stage first."
        )

    from pipeline.plan import selected_layers

    layer_ids = selected_layers(spec, config)
    families_by_id = {family.family_id: family for family in families}
    prompts_by_id = {prompt.prompt_id: prompt for prompt in prompts}
    responses_by_prompt = {response.prompt_id: response for response in responses}

    existing_reviews = records.read_jsonl(run_dir / records.REVIEWS_FILE, Review)
    existing_verdicts = records.read_jsonl(run_dir / records.DIVERGENCE_FILE, DivergenceVerdict)

    async with ModelClient.from_config(config, run_dir / records.USAGE_FILE, "validate") as client:
        reviews = await _review_responses(
            client,
            config,
            spec,
            prompts_by_id,
            families_by_id,
            responses,
            existing_reviews,
            layer_ids,
        )
        responses, reviews, revised_count = await _revise_flagged_responses(
            client, config, spec, prompts_by_id, families_by_id, responses, reviews, layer_ids
        )
        if revised_count:
            records.write_jsonl(run_dir / records.RESPONSES_FILE, responses)
            responses_by_prompt = {response.prompt_id: response for response in responses}
        records.write_jsonl(run_dir / records.REVIEWS_FILE, reviews)

        second_role = config.validation.get("second_reviewer_role")
        if second_role:
            second = await _review_responses(
                client,
                config,
                spec,
                prompts_by_id,
                families_by_id,
                responses,
                records.read_jsonl(run_dir / records.REVIEWS_SECOND_FILE, Review),
                layer_ids,
                reviewer_role_name=str(second_role),
            )
            records.write_jsonl(run_dir / records.REVIEWS_SECOND_FILE, second)

        verdicts = await _judge_divergence(
            client,
            config,
            spec,
            prompts_by_id,
            families_by_id,
            responses_by_prompt,
            baselines,
            strong_generics,
            existing_verdicts,
        )
        records.write_jsonl(run_dir / records.DIVERGENCE_FILE, verdicts)

        ordered = [r for r in responses if r.prompt_id in prompts_by_id]
        texts = [_training_text(prompts_by_id[r.prompt_id], r) for r in ordered]
        similarity, method = await _similarity_matrix(client, texts, config)

    review_by_response = {review.response_id: review for review in reviews}
    verdict_by_prompt = {verdict.prompt_id: verdict for verdict in verdicts}

    # Calibrate against this run's own pair distribution rather than a fixed cut.
    pair_scores = all_pair_scores(len(ordered), similarity)
    sigmas = float(settings.get("duplicate_sigmas", 3.0))
    floor_key = (
        "duplicate_floor_embeddings" if method == "embeddings" else "duplicate_floor_jaccard"
    )
    floor = float(settings.get(floor_key, 0.55 if method == "embeddings" else 0.35))
    duplicate_threshold, pair_centre, pair_spread = calibrated_threshold(
        [score for score, _left, _right in pair_scores], sigmas, floor
    )
    within_family_threshold = (
        float(settings.get("within_family_duplicate_embeddings", 0.985))
        if method == "embeddings"
        else float(settings.get("within_family_duplicate_jaccard", 0.9))
    )
    logger.info(
        "similarity (%s): %d pairs, median %.3f, robust sd %.3f, threshold median+%.1fsd = %.3f",
        method,
        len(pair_scores),
        pair_centre,
        pair_spread,
        sigmas,
        duplicate_threshold,
    )
    duplicate_of, clusters = find_near_duplicates(
        [r.response_id for r in ordered],
        similarity,
        duplicate_threshold,
        group_ids=[prompts_by_id[r.prompt_id].family_id for r in ordered],
        within_group_threshold=within_family_threshold,
        never_compare_ids=[
            (
                families_by_id[prompts_by_id[r.prompt_id].family_id].counterfactual_group_id
                if prompts_by_id[r.prompt_id].family_id in families_by_id
                else None
            )
            for r in ordered
        ],
    )

    def split_of(response: Response) -> str:
        family = families_by_id.get(prompts_by_id[response.prompt_id].family_id)
        return family.split if family else ""

    eval_indices = [i for i, r in enumerate(ordered) if split_of(r) == "eval"]
    train_indices = [i for i, r in enumerate(ordered) if split_of(r) == "train"]
    leakage = max_leakage(eval_indices, train_indices, similarity)
    cross_scores = [
        similarity(eval_index, train_index)
        for eval_index in eval_indices
        for train_index in train_indices
    ]
    leakage_threshold, leak_centre, leak_spread = calibrated_threshold(
        cross_scores, sigmas, floor
    )
    _write_similarity_pairs(
        run_dir,
        ordered,
        prompts_by_id,
        families_by_id,
        pair_scores,
        cross_scores,
        duplicate_threshold,
        leakage_threshold,
        method,
        _calibration(pair_centre, pair_spread, sigmas),
        _calibration(leak_centre, leak_spread, sigmas),
        eval_indices,
        train_indices,
        similarity,
    )

    min_fidelity = int(settings.get("min_fidelity", 4))
    min_judgment = int(settings.get("min_judgment_not_terminology", 3))
    min_scenario = int(settings.get("min_scenario_quality", 3))
    reject_on_quoted_source = bool(settings.get("reject_on_quoted_source", False))

    decisions: list[Decision] = []
    cue_hit_details: list[dict[str, Any]] = []
    for index, response in enumerate(ordered):
        prompt = prompts_by_id[response.prompt_id]
        family = families_by_id.get(prompt.family_id)
        reasons: list[str] = []
        keep = True

        final_case_type_hint = prompt.case_type
        review = review_by_response.get(response.response_id)
        if review is None:
            keep = False
            reasons.append("no reviewer verdict")
        else:
            if review.verdict == "reject":
                keep = False
                reasons.append(f"reviewer rejected: {review.rationale[:160]}")
            elif review.verdict == "revise":
                # The revise round already ran. A response still asking for revision has
                # had its rewrite and did not pass, so it is dropped rather than annotated.
                keep = False
                reasons.append(
                    f"reviewer still asks for revision after a rewrite: {review.rationale[:160]}"
                )
            if review.scores.get("formulaic_shape"):
                keep = False
                reasons.append("reviewer: fixed template shape rather than a shape this case needed")
            if review.scores.get("prompt_stipulates_move"):
                # The user's own message stated the move, so any assistant would make it.
                if final_case_type_hint == "divergence":
                    reasons.append(
                        "note: prompt stipulates the target's move; relabelled ordinary"
                    )
            if not _scores_pass(review, min_fidelity, min_judgment, min_scenario):
                keep = False
                reasons.append(
                    f"scores below thresholds: fidelity={review.scores.get('fidelity')} "
                    f"judgment={review.scores.get('judgment_not_terminology')} "
                    f"scenario={review.scores.get('scenario_quality')}"
                )
            if review.scores.get("confident_on_unresolved"):
                keep = False
                reasons.append("reviewer: confident resolution of an unresolved tradeoff")

        response_text = f"{response.deliberation}\n{response.answer}"
        soft_hits = sorted(
            set(find_cue_hits(prompt.text, spec.soft_terms))
            | set(find_cue_hits(response_text, spec.soft_terms))
        )
        if soft_hits:
            # Reported, never a reason to drop: these words have ordinary senses too.
            reasons.append(f"note: soft cue terms present: {soft_hits}")
        if prompt.mode == "explicit":
            # The explicit slice is allowed to name the tradition; that is its purpose.
            reasons.append("note: explicit-mode record, cue check skipped")
            prompt_hits, response_hits = [], []
        else:
            prompt_hits = find_cue_hits(prompt.text, spec.forbidden_terms)
            response_hits = find_cue_hits(response_text, spec.forbidden_terms)
            if prompt_hits or response_hits:
                keep = False
                reasons.append(
                    f"cue terms found (prompt: {prompt_hits or 'none'}, "
                    f"response: {response_hits or 'none'})"
                )
                cue_hit_details.append(
                    {
                        "response_id": response.response_id,
                        "prompt_hits": prompt_hits,
                        "response_hits": response_hits,
                    }
                )
            elif review is not None and review.scores.get("cue_leakage"):
                keep = False
                reasons.append("reviewer flagged cue leakage the term list did not catch")
            elif review is not None and review.scores.get("archaic_register"):
                keep = False
                reasons.append(
                    "reviewer flagged archaic or translated-sounding register, which signals "
                    "the source as surely as naming it"
                )
        if review is not None and review.scores.get("quoted_source_text"):
            note = "quoted or closely echoed source-text wording"
            if reject_on_quoted_source:
                keep = False
                reasons.append(note)
            else:
                reasons.append(f"note: {note}")

        duplicate = duplicate_of.get(response.response_id)
        if duplicate:
            keep = False
            reasons.append(f"near-duplicate of {duplicate} ({method})")

        leak_score = None
        if index in leakage:
            leak_score, _ = leakage[index]
            if leak_score >= leakage_threshold:
                keep = False
                reasons.append(
                    f"eval item too close to training data ({method} {leak_score:.3f} "
                    f">= {leakage_threshold})"
                )

        final_case_type = prompt.case_type
        if review is not None and review.scores.get("prompt_stipulates_move"):
            final_case_type = "ordinary"
        divergence_status = "not_applicable"
        divergence_kind = ""
        divergence_source = ""
        if prompt.case_type == "divergence" and final_case_type == "divergence":
            verdict = verdict_by_prompt.get(prompt.prompt_id)
            if verdict is None:
                divergence_status = "unverified"
                reasons.append(
                    "note: intended divergence not checked, no baseline answer for this prompt"
                )
            elif verdict.unverified_reason:
                divergence_status = "unverified"
                reasons.append(f"note: divergence unverified: {verdict.unverified_reason}")
            elif verdict.diverges:
                # A difference in reasons alone counts as divergence, not only a
                # difference in the recommended action.
                divergence_status = "confirmed"
                divergence_kind = verdict.kind
                divergence_source = verdict.divergence_source
            else:
                # Never silently dropped: relabelled and counted.
                divergence_status = "not_confirmed"
                divergence_kind = verdict.kind
                divergence_source = verdict.divergence_source
                final_case_type = "ordinary"
                reasons.append(
                    f"note: intended divergence did not hold against the baseline "
                    f"({verdict.explanation[:120]}); relabelled ordinary"
                )

        if not response.answer.strip():
            keep = False
            reasons.append("empty answer")

        decisions.append(
            Decision(
                response_id=response.response_id,
                keep=keep,
                reasons=reasons,
                final_case_type=final_case_type,
                duplicate_of=duplicate,
                max_leakage=round(leak_score, 4) if leak_score is not None else None,
                divergence_status=divergence_status,
                divergence_kind=divergence_kind,
                divergence_source=divergence_source,
                soft_cue_hits=soft_hits,
            )
        )
        if family is None:
            decisions[-1].keep = False
            decisions[-1].reasons.append("orphan response: its family is missing")

    records.write_jsonl(run_dir / records.DECISIONS_FILE, decisions)

    kept = sum(1 for decision in decisions if decision.keep)
    summary = {
        "responses": len(decisions),
        "kept": kept,
        "dropped": len(decisions) - kept,
        "similarity_method": method,
        "similarity_calibration": _calibration(pair_centre, pair_spread, sigmas),
        "leakage_calibration": _calibration(leak_centre, leak_spread, sigmas),
        "duplicate_threshold": round(duplicate_threshold, 4),
        "leakage_threshold": round(leakage_threshold, 4),
        "duplicate_clusters": len(clusters),
        "duplicates": len(duplicate_of),
        "cue_hits": len(cue_hit_details),
        "eval_items_checked_for_leakage": len(eval_indices),
        "max_leakage_seen": round(max((s for s, _ in leakage.values()), default=0.0), 4),
        "divergence_confirmed": sum(1 for d in decisions if d.divergence_status == "confirmed"),
        "divergence_not_confirmed": sum(
            1 for d in decisions if d.divergence_status == "not_confirmed"
        ),
        "divergence_unverified": sum(1 for d in decisions if d.divergence_status == "unverified"),
        "divergence_action": sum(
            1 for d in decisions if d.divergence_status == "confirmed" and d.divergence_kind in ("action", "both")
        ),
        "divergence_reasons": sum(
            1 for d in decisions if d.divergence_status == "confirmed" and d.divergence_kind in ("reasons", "both")
        ),
        **_family_divergence_rates(decisions, ordered, prompts_by_id, verdicts),
        "soft_cue_flags": sum(1 for d in decisions if d.soft_cue_hits),
        "explicit_mode_records": sum(
            1 for r in ordered if prompts_by_id[r.prompt_id].mode == "explicit"
        ),
        "quoted_source_flags": sum(
            1 for r in reviews if r.scores.get("quoted_source_text")
        ),
        "archaic_register_flags": sum(1 for r in reviews if r.scores.get("archaic_register")),
    }
    logger.info("validate: %s", summary)
    return summary


def _calibration(centre: float, spread: float, sigmas: float) -> dict[str, Any]:
    """Self-describing calibration record, so a report can print how the cut was reached."""
    return {
        "statistic": f"median + {sigmas:g} x robust_sd",
        "centre": round(centre, 4),
        "spread": round(spread, 4),
        "sigmas": sigmas,
    }


def _write_similarity_pairs(
    run_dir: Path,
    ordered: list[Response],
    prompts_by_id: dict[str, Prompt],
    families_by_id: dict[str, Family],
    pair_scores: list[tuple[float, int, int]],
    cross_scores: list[float],
    duplicate_threshold: float,
    leakage_threshold: float,
    method: str,
    dedupe_calibration: dict[str, float],
    leakage_calibration: dict[str, float],
    eval_indices: list[int],
    train_indices: list[int],
    similarity: Callable[[int, int], float],
    top_n: int = 50,
) -> None:
    """Write the closest pairs so the report can show them even when nothing is flagged.

    A dedupe stage that flags nothing is indistinguishable from one that is broken unless
    the distribution it saw is on record.
    """
    def describe(index: int) -> dict[str, Any]:
        response = ordered[index]
        prompt = prompts_by_id[response.prompt_id]
        family = families_by_id.get(prompt.family_id)
        return {
            "id": prompt.prompt_id,
            "family": prompt.family_id,
            "split": family.split if family else "",
        }

    rows: list[dict[str, Any]] = []
    for score, left, right in sorted(pair_scores, reverse=True)[:top_n]:
        a, b = describe(left), describe(right)
        rows.append(
            {
                "kind": "dedupe",
                "a_id": a["id"],
                "b_id": b["id"],
                "a_family": a["family"],
                "b_family": b["family"],
                "a_split": a["split"],
                "b_split": b["split"],
                "score": round(float(score), 4),
                "method": method,
                "flagged": float(score) >= duplicate_threshold,
                "threshold": round(duplicate_threshold, 4),
                "calibration": dedupe_calibration,
            }
        )
    cross_pairs = sorted(
        (
            (similarity(eval_index, train_index), eval_index, train_index)
            for eval_index in eval_indices
            for train_index in train_indices
        ),
        reverse=True,
    )[:top_n]
    for score, eval_index, train_index in cross_pairs:
        a, b = describe(eval_index), describe(train_index)
        rows.append(
            {
                "kind": "leakage",
                "a_id": a["id"],
                "b_id": b["id"],
                "a_family": a["family"],
                "b_family": b["family"],
                "a_split": a["split"],
                "b_split": b["split"],
                "score": round(float(score), 4),
                "method": method,
                "flagged": float(score) >= leakage_threshold,
                "threshold": round(leakage_threshold, 4),
                "calibration": leakage_calibration,
            }
        )
    records.write_jsonl(run_dir / records.SIMILARITY_FILE, rows)


def _family_divergence_rates(
    decisions: list[Decision],
    ordered: list[Response],
    prompts_by_id: dict[str, Prompt],
    verdicts: list[DivergenceVerdict],
) -> dict[str, Any]:
    """Divergence rates per family, not per prompt.

    Several prompts on one family ask about the same situation, so counting per prompt
    inflates the rate by however many prompts a family happens to carry.
    """
    family_of = {
        response.response_id: prompts_by_id[response.prompt_id].family_id
        for response in ordered
        if response.prompt_id in prompts_by_id
    }
    verdict_by_prompt = {v.prompt_id: v for v in verdicts}
    intended: set[str] = set()
    value_families: set[str] = set()
    closer: Counter[str] = Counter()
    for decision in decisions:
        family_id = family_of.get(decision.response_id)
        if family_id is None or decision.divergence_status == "not_applicable":
            continue
        intended.add(family_id)
        if decision.divergence_source == "value":
            value_families.add(family_id)
    for verdict in verdict_by_prompt.values():
        if verdict.closer_to:
            closer[verdict.closer_to] += 1
    pairwise_counts = {
        "candidate_vs_base": sum(1 for v in verdicts if v.diverges_vs_base),
        "candidate_vs_strong_generic": sum(1 for v in verdicts if v.diverges_vs_generic),
        "strong_generic_vs_base": sum(1 for v in verdicts if v.generic_differs_from_base),
        "judged": len([v for v in verdicts if not v.unverified_reason]),
    }
    return {
        "divergence_pairwise": pairwise_counts,
        "divergence_families_intended": len(intended),
        "divergence_families_value": len(value_families),
        "divergence_value_rate_by_family": (
            round(len(value_families) / len(intended), 3) if intended else 0.0
        ),
        "divergence_closer_to": dict(closer),
        "divergence_by_source": dict(
            Counter(d.divergence_source for d in decisions if d.divergence_source)
        ),
    }


def _scores_pass(review: Review, min_fidelity: int, min_judgment: int, min_scenario: int) -> bool:
    return (
        _as_int(review.scores.get("fidelity")) >= min_fidelity
        and _as_int(review.scores.get("judgment_not_terminology")) >= min_judgment
        and _as_int(review.scores.get("scenario_quality")) >= min_scenario
    )
