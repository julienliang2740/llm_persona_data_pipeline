"""Validation stage: run the checks, then decide what to keep and why.

The checks themselves live in pipeline/similarity.py, pipeline/review.py and
pipeline/divergence.py. This module orders them, turns their output into one Decision per
response, and writes the artifacts.

`find_cue_hits`, `jaccard`, `cosine` and `tokenize` are re-exported here because plan.py,
generate.py, export.py and several tests import them from this module.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pipeline import records
from pipeline.config import RunConfig
from pipeline.divergence import _family_divergence_rates, _judge_divergence
from pipeline.model import ModelClient
from pipeline.records import (
    BaselineAnswer,
    Decision,
    DivergenceVerdict,
    Family,
    Prompt,
    Response,
    Review,
)
from pipeline.review import (
    _review_from_payload,  # noqa: F401  (imported from this module by tests)
    _review_responses,
    _revise_flagged_responses,
    _scores_pass,
    flag_score_conflicts,
    missing_score_keys,  # noqa: F401  (imported from this module by tests)
)
from pipeline.similarity import (
    _calibration,
    _comparison_text,
    _similarity_matrix,
    _write_similarity_pairs,
    all_pair_scores,
    calibrated_threshold,
    cosine,  # noqa: F401  (re-exported)
    find_cue_hits,
    find_near_duplicates,
    jaccard,  # noqa: F401  (re-exported)
    max_leakage,
    tokenize,  # noqa: F401  (re-exported)
)
from pipeline.target import TargetSpec

logger = logging.getLogger("pipeline.validate")

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
        "reviewer_flag_score_conflicts": flag_score_conflicts(reviews),
    }
    logger.info("validate: %s", summary)
    return summary


