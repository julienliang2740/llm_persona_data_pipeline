"""Validation stage: reviewer critique, cue check, near-duplicates, leakage, divergence.

Every response ends with a Decision recording keep/drop and every reason, so a
researcher can see why anything was dropped without re-running a model.
"""

from __future__ import annotations

import logging
import math
import random
import re
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
from pipeline.target import TargetSpec, render_for_reviewer, render_key_passages
from prompts import render
from prompts.review import (
    DIVERGENCE_JUDGE_PROMPT,
    FIDELITY_REVIEW_PROMPT,
    REVIEWER_SYSTEM_PROMPT,
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


def _training_text(prompt: Prompt, response: Response) -> str:
    return f"{prompt.text}\n\n{response.deliberation}\n\n{response.answer}"


async def _review_responses(
    client: ModelClient,
    config: RunConfig,
    spec: TargetSpec,
    prompts_by_id: dict[str, Prompt],
    families_by_id: dict[str, Family],
    responses: list[Response],
    existing: list[Review],
) -> list[Review]:
    reviewer = config.role("reviewer")
    reviewed = {review.response_id for review in existing}
    todo = [r for r in responses if r.response_id not in reviewed]
    if not todo:
        return existing
    spec_text = render_for_reviewer(spec)
    forbidden = ", ".join(spec.forbidden_terms) or "(none)"
    soft_terms_note = (
        render(SOFT_TERMS_NOTE, soft_terms=", ".join(spec.soft_terms)) if spec.soft_terms else ""
    )

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
        payload, _ = await client.complete_json(
            reviewer,
            [
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
                        forbidden_terms=forbidden,
                        soft_terms_note=soft_terms_note,
                    ),
                },
            ],
            stage="validate.review",
            record_id=response.response_id,
        )
        scores = payload.get("scores") or {}
        return Review(
            review_id=short_id("rev", response.response_id, reviewer.model),
            response_id=response.response_id,
            reviewer_model=reviewer.model,
            scores={
                "fidelity": _as_int(scores.get("fidelity")),
                "judgment_not_terminology": _as_int(scores.get("judgment_not_terminology")),
                "scenario_quality": _as_int(scores.get("scenario_quality")),
                "cue_leakage": bool(scores.get("cue_leakage")),
                "confident_on_unresolved": bool(scores.get("confident_on_unresolved")),
                "quoted_source_text": bool(scores.get("quoted_source_text")),
                "archaic_register": bool(scores.get("archaic_register")),
            },
            issues=[str(issue) for issue in (payload.get("issues") or [])],
            verdict=str(payload.get("verdict", "revise")).lower().strip(),
            rationale=str(payload.get("rationale", "")).strip(),
        )

    results = await gather_bounded([review_one(response) for response in todo])
    reviews = list(existing)
    for result in results:
        if isinstance(result, Exception):
            logger.error("review failed: %s", result)
            continue
        if result is not None:
            reviews.append(result)
    return reviews


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


async def _judge_divergence(
    client: ModelClient,
    config: RunConfig,
    prompts_by_id: dict[str, Prompt],
    responses_by_prompt: dict[str, Response],
    baselines: list[BaselineAnswer],
    existing: list[DivergenceVerdict],
) -> list[DivergenceVerdict]:
    judge = config.role("judge") if "judge" in config.roles else config.role("reviewer")
    judged = {verdict.prompt_id for verdict in existing}
    todo = [
        baseline
        for baseline in baselines
        if baseline.prompt_id not in judged
        and baseline.prompt_id in responses_by_prompt
        and prompts_by_id.get(baseline.prompt_id, Prompt("", "", "", "", "")).case_type == "divergence"
    ]
    if not todo:
        return existing

    async def judge_one(baseline: BaselineAnswer) -> DivergenceVerdict | None:
        prompt = prompts_by_id[baseline.prompt_id]
        candidate = responses_by_prompt[baseline.prompt_id]
        # Seeded on the prompt id so the ordering is random across items but reproducible.
        candidate_first = random.Random(baseline.prompt_id).random() < 0.5
        reply_a = candidate.answer if candidate_first else baseline.text
        reply_b = baseline.text if candidate_first else candidate.answer
        payload, _ = await client.complete_json(
            judge,
            [
                {
                    "role": "user",
                    "content": render(
                        DIVERGENCE_JUDGE_PROMPT,
                        user_prompt=prompt.text,
                        reply_a=reply_a,
                        reply_b=reply_b,
                    ),
                }
            ],
            stage="validate.divergence",
            record_id=baseline.prompt_id,
        )
        return DivergenceVerdict(
            prompt_id=baseline.prompt_id,
            judge_model=judge.model,
            diverges=bool(payload.get("diverges")),
            kind=str(payload.get("kind", "none")),
            explanation=str(payload.get("explanation", "")).strip(),
            presented_first="candidate" if candidate_first else "baseline",
        )

    results = await gather_bounded([judge_one(baseline) for baseline in todo])
    verdicts = list(existing)
    for result in results:
        if isinstance(result, Exception):
            logger.error("divergence judging failed: %s", result)
            continue
        if result is not None:
            verdicts.append(result)
    return verdicts


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
    if not responses:
        raise RuntimeError(
            f"No responses in {run_dir / records.RESPONSES_FILE}. Run the generate stage first."
        )

    families_by_id = {family.family_id: family for family in families}
    prompts_by_id = {prompt.prompt_id: prompt for prompt in prompts}
    responses_by_prompt = {response.prompt_id: response for response in responses}

    existing_reviews = records.read_jsonl(run_dir / records.REVIEWS_FILE, Review)
    existing_verdicts = records.read_jsonl(run_dir / records.DIVERGENCE_FILE, DivergenceVerdict)

    async with ModelClient.from_config(config, run_dir / records.USAGE_FILE, "validate") as client:
        reviews = await _review_responses(
            client, config, spec, prompts_by_id, families_by_id, responses, existing_reviews
        )
        records.write_jsonl(run_dir / records.REVIEWS_FILE, reviews)

        verdicts = await _judge_divergence(
            client, config, prompts_by_id, responses_by_prompt, baselines, existing_verdicts
        )
        records.write_jsonl(run_dir / records.DIVERGENCE_FILE, verdicts)

        ordered = [r for r in responses if r.prompt_id in prompts_by_id]
        texts = [_training_text(prompts_by_id[r.prompt_id], r) for r in ordered]
        similarity, method = await _similarity_matrix(client, texts, config)

    review_by_response = {review.response_id: review for review in reviews}
    verdict_by_prompt = {verdict.prompt_id: verdict for verdict in verdicts}

    if method == "embeddings":
        duplicate_threshold = float(settings.get("duplicate_threshold_embeddings", 0.92))
        within_family_threshold = float(settings.get("within_family_duplicate_embeddings", 0.985))
    else:
        duplicate_threshold = float(settings.get("duplicate_threshold_jaccard", 0.75))
        within_family_threshold = float(settings.get("within_family_duplicate_jaccard", 0.9))
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
    leakage_threshold = (
        float(settings.get("leakage_threshold_embeddings", 0.85))
        if method == "embeddings"
        else float(settings.get("leakage_threshold_jaccard", 0.6))
    )

    min_fidelity = int(settings.get("min_fidelity", 4))
    min_judgment = int(settings.get("min_judgment_not_terminology", 3))
    min_scenario = int(settings.get("min_scenario_quality", 3))
    keep_revise = bool(settings.get("keep_revise_if_scores_pass", True))
    reject_on_quoted_source = bool(settings.get("reject_on_quoted_source", False))

    decisions: list[Decision] = []
    cue_hit_details: list[dict[str, Any]] = []
    for index, response in enumerate(ordered):
        prompt = prompts_by_id[response.prompt_id]
        family = families_by_id.get(prompt.family_id)
        reasons: list[str] = []
        keep = True

        review = review_by_response.get(response.response_id)
        if review is None:
            keep = False
            reasons.append("no reviewer verdict")
        else:
            if review.verdict == "reject":
                keep = False
                reasons.append(f"reviewer rejected: {review.rationale[:160]}")
            elif review.verdict == "revise":
                if keep_revise and _scores_pass(review, min_fidelity, min_judgment, min_scenario):
                    reasons.append("note: reviewer asked for revision but all scores pass thresholds")
                else:
                    keep = False
                    reasons.append(f"reviewer asked for revision: {review.rationale[:160]}")
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
        divergence_status = "not_applicable"
        divergence_kind = ""
        if prompt.case_type == "divergence":
            verdict = verdict_by_prompt.get(prompt.prompt_id)
            if verdict is None:
                divergence_status = "unverified"
                reasons.append(
                    "note: intended divergence not checked, no baseline answer for this prompt"
                )
            elif verdict.diverges:
                # A difference in reasons alone counts as divergence, not only a
                # difference in the recommended action.
                divergence_status = "confirmed"
                divergence_kind = verdict.kind
            else:
                # Never silently dropped: relabelled and counted.
                divergence_status = "not_confirmed"
                divergence_kind = verdict.kind
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


def _scores_pass(review: Review, min_fidelity: int, min_judgment: int, min_scenario: int) -> bool:
    return (
        _as_int(review.scores.get("fidelity")) >= min_fidelity
        and _as_int(review.scores.get("judgment_not_terminology")) >= min_judgment
        and _as_int(review.scores.get("scenario_quality")) >= min_scenario
    )
