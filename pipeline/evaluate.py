"""Evaluation stage: run an endpoint over eval.jsonl and judge each answer.

`--endpoint` names a model role from the config, so the same code evaluates the
local base model before fine-tuning and the adapted model after it. With two
result files it prints and writes a before/after table.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pipeline import records
from pipeline.config import RunConfig
from pipeline.model import LocalEndpointUnavailable, ModelClient, gather_bounded
from pipeline.target import TargetSpec, render_for_reviewer
from prompts import render
from prompts.evaluation import EVAL_ANSWER_SYSTEM_PROMPT, EVAL_JUDGE_PROMPT

logger = logging.getLogger("pipeline.evaluate")


def results_path(run_dir: Path, label: str) -> Path:
    return run_dir / f"eval_results_{label}.jsonl"


async def run_stage(
    config: RunConfig,
    spec: TargetSpec,
    run_dir: Path,
    endpoint_role: str = "base",
    label: str | None = None,
) -> dict[str, Any]:
    """Answer every eval item with `endpoint_role`, then judge each answer."""
    from pipeline.export import EVAL_FILE

    eval_items = list(records.iter_jsonl(run_dir / EVAL_FILE))
    if not eval_items:
        raise RuntimeError(
            f"No evaluation items in {run_dir / EVAL_FILE}. Run the export stage first."
        )
    role = config.role(endpoint_role)
    label = label or endpoint_role
    out_path = results_path(run_dir, label)
    # Null means "use the role's own budget", which is what keeps before/after settings
    # matched: you swap the endpoint, not the generation settings.
    configured_max = config.evaluation.get("answer_max_tokens")
    max_answer_tokens = int(configured_max) if configured_max else role.max_tokens
    temperature = float(config.evaluation.get("temperature", 0.7))

    existing = {row["prompt_id"]: row for row in records.iter_jsonl(out_path)}
    todo = [item for item in eval_items if item["meta"]["prompt_id"] not in existing]
    if not todo:
        logger.info("evaluate: %d results already present for %s", len(existing), label)
        return _summarise(list(existing.values()), label)

    spec_text = render_for_reviewer(spec)

    async with ModelClient.from_config(config, run_dir / records.USAGE_FILE, "evaluate") as client:

        async def answer(item: dict[str, Any]) -> tuple[dict[str, Any], str]:
            response = await client.complete(
                role,
                [
                    {"role": "system", "content": EVAL_ANSWER_SYSTEM_PROMPT},
                    {"role": "user", "content": item["prompt"]},
                ],
                temperature=temperature,
                max_tokens=max_answer_tokens,
                stage=f"evaluate.answer.{label}",
                record_id=item["meta"]["prompt_id"],
            )
            return item, response.text

        answers = await gather_bounded([answer(item) for item in todo])
        answered: list[tuple[dict[str, Any], str]] = []
        for result in answers:
            if isinstance(result, LocalEndpointUnavailable):
                raise RuntimeError(str(result)) from None
            if isinstance(result, Exception):
                logger.error("eval answer failed: %s", result)
                continue
            answered.append(result)

        async def judge(item: dict[str, Any], candidate: str) -> dict[str, Any]:
            payload, _ = await client.complete_json(
                config.role("judge") if "judge" in config.roles else config.role("reviewer"),
                [
                    {
                        "role": "user",
                        "content": render(
                            EVAL_JUDGE_PROMPT,
                            target_spec=spec_text,
                            user_prompt=item["prompt"],
                            expected_behavior=item["expected_behavior"],
                            pass_fail_notes="\n".join(f"- {n}" for n in item["pass_fail_notes"]),
                            candidate_answer=candidate,
                        ),
                    }
                ],
                stage=f"evaluate.judge.{label}",
                record_id=item["meta"]["prompt_id"],
            )
            return {
                "prompt_id": item["meta"]["prompt_id"],
                "family_id": item["family_id"],
                "case_type": item["case_type"],
                "variant": item["variant"],
                "endpoint": label,
                "model": role.model,
                "answer": candidate,
                "pass": bool(payload.get("pass")),
                "principle_notes": [str(n) for n in (payload.get("principle_notes") or [])],
                "failure_modes_hit": [str(f) for f in (payload.get("failure_modes_hit") or [])],
                "rationale": str(payload.get("rationale", "")).strip(),
            }

        judged = await gather_bounded([judge(item, text) for item, text in answered])

    rows = list(existing.values())
    for result in judged:
        if isinstance(result, Exception):
            logger.error("eval judging failed: %s", result)
            continue
        rows.append(result)
    if not rows:
        raise RuntimeError(
            f"No evaluation answers were produced for endpoint '{endpoint_role}'. "
            f"Check the errors above; nothing was written to {out_path.name}."
        )
    records.write_jsonl(out_path, rows)
    logger.info("evaluate: wrote %d results to %s", len(rows), out_path)
    return _summarise(rows, label)


def _summarise(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    by_case: dict[str, dict[str, int]] = {}
    for row in rows:
        bucket = by_case.setdefault(row.get("case_type", "unknown"), {"n": 0, "pass": 0})
        bucket["n"] += 1
        bucket["pass"] += 1 if row.get("pass") else 0
    passed = sum(1 for row in rows if row.get("pass"))
    return {
        "endpoint": label,
        "n": len(rows),
        "pass": passed,
        "pass_rate": round(passed / len(rows), 3) if rows else 0.0,
        "by_case_type": by_case,
    }


def before_after_table(before_path: Path, after_path: Path) -> str:
    """Markdown comparison of two eval result files, plus the per-item flips."""
    before = {row["prompt_id"]: row for row in records.iter_jsonl(before_path)}
    after = {row["prompt_id"]: row for row in records.iter_jsonl(after_path)}
    shared = [pid for pid in before if pid in after]
    if not shared:
        return f"No prompts in common between {before_path.name} and {after_path.name}."

    buckets: dict[str, list[str]] = {}
    for prompt_id in shared:
        buckets.setdefault(before[prompt_id].get("case_type", "unknown"), []).append(prompt_id)

    lines = [
        f"# Before / after on {len(shared)} evaluation prompts",
        "",
        f"before: `{before_path.name}` ({before[shared[0]].get('model','?')})",
        f"after:  `{after_path.name}` ({after[shared[0]].get('model','?')})",
        "",
        "| case type | n | before pass | after pass | change |",
        "|---|---|---|---|---|",
    ]
    for case_type, prompt_ids in sorted(buckets.items()):
        before_pass = sum(1 for pid in prompt_ids if before[pid].get("pass"))
        after_pass = sum(1 for pid in prompt_ids if after[pid].get("pass"))
        lines.append(
            f"| {case_type} | {len(prompt_ids)} | {before_pass} | {after_pass} "
            f"| {after_pass - before_pass:+d} |"
        )
    total_before = sum(1 for pid in shared if before[pid].get("pass"))
    total_after = sum(1 for pid in shared if after[pid].get("pass"))
    lines.append(
        f"| **all** | {len(shared)} | {total_before} | {total_after} "
        f"| {total_after - total_before:+d} |"
    )

    gained = [pid for pid in shared if after[pid].get("pass") and not before[pid].get("pass")]
    lost = [pid for pid in shared if before[pid].get("pass") and not after[pid].get("pass")]
    lines += ["", f"Newly passing: {len(gained)}", f"Newly failing: {len(lost)}", ""]
    for prompt_id in lost[:5]:
        lines.append(f"- regression `{prompt_id}`: {after[prompt_id].get('rationale','')[:200]}")
    return "\n".join(lines) + "\n"


def write_before_after(before_path: Path, after_path: Path, out_path: Path) -> str:
    table = before_after_table(before_path, after_path)
    out_path.write_text(table, encoding="utf-8")
    return table
