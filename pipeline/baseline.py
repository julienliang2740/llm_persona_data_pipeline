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
from pipeline.config import RunConfig
from pipeline.model import LocalEndpointUnavailable, ModelClient, gather_bounded
from pipeline.records import BaselineAnswer, Family, Prompt
from prompts.evaluation import EVAL_ANSWER_SYSTEM_PROMPT

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
                    {"role": "system", "content": EVAL_ANSWER_SYSTEM_PROMPT},
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
    logger.info(
        "baseline: %d answers total (%d new, %d failed)",
        len(answers),
        len(answers) - len(existing),
        failures,
    )
    return {"baseline_answers": len(answers), "new": len(answers) - len(existing)}
