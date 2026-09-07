"""Three-way divergence judging.

The candidate is compared with the 7B base answer AND with a strong generic answer written
without the target specification, because "differs from a weak model" and "differs from a
capable model that has never seen this target" are different claims and only the second is
evidence of a value difference.
"""

from __future__ import annotations

import logging
import random
from collections import Counter
from typing import Any

from pipeline.config import RunConfig
from pipeline.model import ModelClient, gather_bounded
from pipeline.records import (
    BaselineAnswer,
    Decision,
    DivergenceVerdict,
    Family,
    Prompt,
    Response,
)
from pipeline.target import TargetSpec
from prompts import render
from prompts.review import DIVERGENCE_JUDGE_PROMPT

logger = logging.getLogger("pipeline.divergence")


def verdict_from_payload(
    payload: dict[str, Any],
    prompt_id: str,
    judge_model: str,
    label_of: dict[str, str],
    hypothesis_id: str,
) -> DivergenceVerdict:
    """Map the judge's letter-keyed answer back onto candidate, generic and weak.

    The judge never learns which model wrote which reply, so everything it returns is keyed
    by letter or by the role words "generic" and "weak"; this is the only place that
    knows the mapping.
    """
    actions = payload.get("actions") or {}
    pairwise = payload.get("pairwise") or {}
    value_named = str(payload.get("value_named", "")).strip()
    generic_echo = str(payload.get("generic_echo", "")).strip()
    same_claim = bool(payload.get("generic_makes_same_claim"))
    source = str(payload.get("divergence_source", "none")).strip().lower()
    if source not in ("value", "capability", "stipulated", "none"):
        source = "none"
    # If the unspecified assistant already makes the claim, the specification did not
    # produce it, whatever the judge concluded. This flipped five of round 2's 23 value
    # verdicts when the critic checked them by hand.
    if same_claim:
        source = "capability"
    # Both gates: a named value AND a value source.
    diverges = bool(value_named) and source == "value"

    closer_to = str(payload.get("closer_to", "")).strip().lower()
    if closer_to not in ("generic", "weak", "neither"):
        closer_to = ""

    action_of = {kind: str(actions.get(label.lower(), "")).strip() for kind, label in label_of.items()}
    return DivergenceVerdict(
        prompt_id=prompt_id,
        judge_model=judge_model,
        diverges=diverges,
        kind=str(payload.get("kind", "none")),
        explanation=str(payload.get("explanation", "")).strip(),
        presented_first=label_of.get("candidate", ""),
        candidate_action=action_of.get("candidate", ""),
        base_action=action_of.get("weak", ""),
        generic_action=action_of.get("generic", ""),
        closer_to=closer_to,
        value_named=value_named,
        generic_echo=generic_echo,
        generic_makes_same_claim=same_claim,
        divergence_source=source,
        hypothesis_id=str(payload.get("hypothesis_id", "")).strip(),
        diverges_vs_base=bool(pairwise.get("test_vs_weak")),
        diverges_vs_generic=bool(pairwise.get("test_vs_generic")),
        generic_differs_from_base=bool(pairwise.get("generic_vs_weak")),
        label_order=", ".join(
            f"{label}={kind}"
            for label, kind in sorted((label, kind) for kind, label in label_of.items())
        ),
    )


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

        # Shuffle which reply carries which letter. Round 2 always put the candidate in
        # slot A and 23 of 26 verdicts came back preferring it; position must not be a cue.
        # Seeded on the prompt id, so the shuffle is random across items and reproducible
        # for any one of them.
        replies = [("candidate", candidate.answer), ("generic", generic.text), ("weak", base.text)]
        random.Random(prompt_id).shuffle(replies)
        label_of = {kind: "ABC"[index] for index, (kind, _text) in enumerate(replies)}
        text_by_label = {"ABC"[index]: text for index, (_kind, text) in enumerate(replies)}

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
                        reply_a=text_by_label["A"],
                        reply_b=text_by_label["B"],
                        reply_c=text_by_label["C"],
                        candidate_label=label_of["candidate"],
                        generic_label=label_of["generic"],
                    ),
                }
            ],
            stage="validate.divergence",
            record_id=prompt_id,
        )
        return verdict_from_payload(payload, prompt_id, judge.model, label_of, hypothesis_id)

    results = await gather_bounded([judge_one(prompt_id) for prompt_id in comparable])
    for result in results:
        if isinstance(result, Exception):
            logger.error("divergence judging failed: %s", result)
            continue
        if result is not None:
            verdicts.append(result)
    return verdicts


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
