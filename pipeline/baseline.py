"""Baseline stage: the un-finetuned model answers the prompts we need to compare against.

Only prompts that need a comparison are sent: intended-divergence cases (an intended
label is not evidence of divergence) and every eval prompt (for the before/after table).
The base model is a local OpenAI-compatible server, which may simply not be running;
that must produce a clear message, not a traceback, and must not block other stages.
"""

from __future__ import annotations

import logging
from pathlib import Path

from pipeline import records
from dataclasses import replace

from pipeline.config import ModelRole, RunConfig
from pipeline.model import LocalEndpointUnavailable, ModelClient, gather_bounded
from pipeline.records import BaselineAnswer, Family, Prompt
from pipeline.target import TargetSpec
from prompts.baseline import BASELINE_ANSWER_SYSTEM_PROMPT
from prompts.review import STRONG_GENERIC_SYSTEM_PROMPT

logger = logging.getLogger("pipeline.baseline")


class BaselineUnavailable(Exception):
    """The base model endpoint is not reachable. The caller reports it and moves on."""


def prompts_needing_baseline(families: list[Family], prompts: list[Prompt]) -> list[Prompt]:
    family_by_id = {family.family_id: family for family in families}
    needed = []
    for prompt in prompts:
        family = family_by_id.get(prompt.family_id)
        if family is None:
            continue
        if prompt.case_type == "divergence" or family.split == "eval":
            needed.append(prompt)
    return needed


def strong_generic_role(config: RunConfig) -> ModelRole:
    """The generator's own settings with the specification removed.

    Anything the config leaves unset on `strong_generic` is inherited from `generator`, so
    the control cannot silently drift into a weaker model, a shorter budget or a different
    thinking setting. That drift is exactly what made round 2's `value` verdicts
    unreadable: the two legs differed in reasoning effort as well as in the spec.
    """
    generator = config.role("generator")
    if "strong_generic" not in config.roles:
        return replace(generator, name="strong_generic")
    configured = config.roles["strong_generic"]
    raw = (config.raw.get("models") or {}).get("strong_generic") or {}
    return replace(
        configured,
        max_tokens=configured.max_tokens if "max_tokens" in raw else generator.max_tokens,
        extra_body=configured.extra_body if raw.get("extra_body") else dict(generator.extra_body),
        temperature=configured.temperature if "temperature" in raw else generator.temperature,
    )


async def run_strong_generic(
    config: RunConfig, run_dir: Path, spec: TargetSpec | None = None
) -> dict[str, int]:
    """Answer the same prompts with a strong model that has never seen the target spec.

    This is the third leg of the divergence comparison. Without it a judge cannot tell
    "the target values something different" from "the candidate was written by a much
    better model than the 7B baseline", which is what round 1 could not separate.
    """
    prompts = records.read_jsonl(run_dir / records.PROMPTS_FILE, Prompt)
    families = records.read_jsonl(run_dir / records.FAMILIES_FILE, Family)
    existing = records.read_jsonl(run_dir / records.STRONG_BASELINE_FILE, BaselineAnswer)
    done = {answer.prompt_id for answer in existing}
    todo = [p for p in prompts_needing_baseline(families, prompts) if p.prompt_id not in done]
    if not todo:
        logger.info("strong generic: %d answers already present", len(existing))
        return {"strong_generic_answers": len(existing), "new": 0}

    role = strong_generic_role(config)
    # No budget override. The only difference between this leg and the candidate must be
    # the specification: round 2 gave this leg reasoning_effort none and 1600 tokens while
    # the candidate had full reasoning and 24000, so "the generic never reached that point"
    # measured the thinking budget rather than the target. Length is matched by an
    # instruction in the prompt instead of by a smaller budget.
    max_tokens = role.max_tokens

    async with ModelClient.from_config(config, run_dir / records.USAGE_FILE, "baseline") as client:

        async def answer(prompt: Prompt) -> BaselineAnswer:
            response = await client.complete(
                role,
                [
                    {"role": "system", "content": STRONG_GENERIC_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt.text},
                ],
                temperature=role.temperature,
                max_tokens=max_tokens,
                stage="baseline.strong_generic",
                record_id=prompt.prompt_id,
            )
            return BaselineAnswer(
                prompt_id=prompt.prompt_id,
                base_model=role.model,
                text=response.text,
                usage=dict(response.usage or {}),
                kind="strong_generic",
                finish_reason=response.finish_reason,
            )

        results = await gather_bounded([answer(prompt) for prompt in todo])

    answers = list(existing)
    failures = 0
    for result in results:
        if isinstance(result, Exception):
            failures += 1
            logger.error("strong generic answer failed: %s", result)
            continue
        answers.append(result)
    records.write_jsonl(run_dir / records.STRONG_BASELINE_FILE, answers)
    truncated = sum(1 for a in answers if a.truncated)
    logger.info(
        "strong generic: %d answers total (%d new, %d failed, %d truncated)",
        len(answers),
        len(answers) - len(existing),
        failures,
        truncated,
    )
    return {"strong_generic_answers": len(answers), "new": len(answers) - len(existing)}


async def run_stage(config: RunConfig, run_dir: Path) -> dict[str, int]:
    """Entry point for `main.py baseline`. Idempotent: existing answers are kept."""
    families = records.read_jsonl(run_dir / records.FAMILIES_FILE, Family)
    prompts = records.read_jsonl(run_dir / records.PROMPTS_FILE, Prompt)
    existing = records.read_jsonl(run_dir / records.BASELINE_FILE, BaselineAnswer)
    done = {answer.prompt_id for answer in existing}
    todo = [p for p in prompts_needing_baseline(families, prompts) if p.prompt_id not in done]
    if not todo:
        logger.info("baseline: %d answers already present, nothing to do", len(existing))
        return {"baseline_answers": len(existing), "new": 0}

    base_role = config.role("base")
    if not base_role.enabled:
        raise BaselineUnavailable(
            f"The 'base' model role is disabled in {config.path}. Enable it and start the "
            f"local server to collect baseline answers."
        )

    async with ModelClient.from_config(config, run_dir / records.USAGE_FILE, "baseline") as client:

        async def answer(prompt: Prompt) -> BaselineAnswer:
            response = await client.complete(
                base_role,
                [
                    {"role": "system", "content": BASELINE_ANSWER_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt.text},
                ],
                stage="baseline",
                record_id=prompt.prompt_id,
            )
            return BaselineAnswer(
                prompt_id=prompt.prompt_id,
                base_model=base_role.model,
                text=response.text,
                usage=dict(response.usage or {}),
                kind="base",
                finish_reason=response.finish_reason,
            )

        # Probe once so an unreachable server fails immediately with one clear message
        # instead of N retry storms.
        try:
            first = await answer(todo[0])
        except LocalEndpointUnavailable as error:
            raise BaselineUnavailable(str(error)) from None

        rest = await gather_bounded([answer(prompt) for prompt in todo[1:]])

    answers = list(existing) + [first]
    failures = 0
    for result in rest:
        if isinstance(result, Exception):
            failures += 1
            logger.error("baseline answer failed: %s", result)
            continue
        answers.append(result)
    records.write_jsonl(run_dir / records.BASELINE_FILE, answers)
    truncated = [a.prompt_id for a in answers if a.truncated]
    logger.info(
        "baseline: %d answers total (%d new, %d failed, %d truncated)",
        len(answers),
        len(answers) - len(existing),
        failures,
        len(truncated),
    )
    if truncated:
        # A cut-off baseline may never have reached its recommendation; round 1 judged 18
        # such answers as though they had. Those prompts become unverified, not diverging.
        logger.warning(
            "baseline: %d answers were cut off and cannot be compared: %s",
            len(truncated),
            truncated[:8],
        )
    return {"baseline_answers": len(answers), "new": len(answers) - len(existing)}
