"""Export stage: family-based split, sft_train.jsonl, eval.jsonl, manifest.json.

Splitting is by family, never by response, so paraphrases of one situation cannot
straddle train and eval. Reserved families go nowhere: they are held for later.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline import records
from pipeline.config import RunConfig
from pipeline.model import format_cost, summarise_usage
from pipeline.records import Decision, Family, Prompt, Response, Review
from pipeline.target import TargetSpec, normalise_passage_ids
from pipeline.validate import find_cue_hits

logger = logging.getLogger("pipeline.export")

SFT_FILE = "sft_train.jsonl"
EVAL_FILE = "eval.jsonl"
MANIFEST_FILE = "manifest.json"


def render_assistant_message(response: Response) -> str:
    """The one fixed rendering used for every training row: deliberation, blank line, answer."""
    deliberation = response.deliberation.strip()
    answer = response.answer.strip()
    if not deliberation:
        return answer
    return f"{deliberation}\n\n{answer}"


def derive_grading_key(
    spec: TargetSpec, response: Response, review: Review | None
) -> tuple[str, list[str]]:
    """Build expected_behavior and pass_fail_notes from the hidden metadata and the review.

    No extra model call: the writer already recorded which principles it applied, and the
    specification already records what honouring and failing each principle looks like.
    """
    principle_ids = response.hidden.get("principles_applied") or []
    principles = [spec.principle(pid) for pid in principle_ids]
    principles = [p for p in principles if p]

    sentences: list[str] = []
    for principle in principles:
        sentences.append(
            f"{principle.get('name')}: {str(principle.get('description', '')).strip().rstrip('.')}."
        )
    note = response.hidden.get("intended_divergence_note") or ""
    if note:
        sentences.append(f"A generic assistant would probably instead: {note.strip()}")
    if not sentences:
        sentences.append(
            "An adequate reply engages the concrete obligations in this situation and takes a "
            "position rather than listing considerations."
        )

    notes: list[str] = []
    for principle in principles:
        for indicator in (principle.get("positive_indicators") or [])[:2]:
            notes.append(f"PASS if the reply {str(indicator).strip().rstrip('.')}.")
        for failure in (principle.get("failure_modes") or [])[:2]:
            notes.append(f"FAIL if the reply {str(failure).strip().rstrip('.')}.")
    if review is not None:
        for issue in review.issues[:2]:
            notes.append(f"NOTE from review of the reference answer: {issue}")
    if not notes:
        notes.append("PASS if the reply gives concrete, actionable judgment rather than hedging.")
    return " ".join(sentences), notes[:8]


def _passage_ids_in_assistant_text(
    spec: TargetSpec, train_rows: list[dict[str, Any]], eval_rows: list[dict[str, Any]]
) -> set[str]:
    """Passage ids are internal provenance. None may reach text a model or user sees."""
    ids = [passage.id for passage in spec.key_passages]
    if not ids:
        return set()
    found: set[str] = set()
    texts = [row["messages"][1]["content"] for row in train_rows]
    texts += [row["prompt"] for row in eval_rows]
    texts += [row["reference_answer"] for row in eval_rows]
    for text in texts:
        found.update(find_cue_hits(text, ids))
    return found


def license_constraints(spec: TargetSpec) -> list[dict[str, str]]:
    """Distinct licence terms on the grounding sources, so restrictions travel with the data."""
    seen: dict[tuple[str, str], dict[str, str]] = {}
    for entry in spec.reference_material:
        if str(entry.get("use", "")).strip() != "grounding":
            continue
        licence = str(entry.get("license") or "not recorded").strip()
        key = (licence, "grounding")
        if key not in seen:
            seen[key] = {"license": licence, "use": "grounding", "sources": entry.get("id", "")}
        else:
            seen[key]["sources"] += f", {entry.get('id', '')}"
    return list(seen.values())


def run_stage(config: RunConfig, spec: TargetSpec, run_dir: Path) -> dict[str, Any]:
    """Entry point for `main.py export`. Writes the three deliverables into the run dir."""
    families = records.read_jsonl(run_dir / records.FAMILIES_FILE, Family)
    prompts = records.read_jsonl(run_dir / records.PROMPTS_FILE, Prompt)
    responses = records.read_jsonl(run_dir / records.RESPONSES_FILE, Response)
    decisions = records.read_jsonl(run_dir / records.DECISIONS_FILE, Decision)
    reviews = records.read_jsonl(run_dir / records.REVIEWS_FILE, Review)
    if not decisions:
        raise RuntimeError(
            f"No decisions in {run_dir / records.DECISIONS_FILE}. Run the validate stage first."
        )

    duplicate_family_ids = sorted(
        {f.family_id for f in families if sum(1 for g in families if g.family_id == f.family_id) > 1}
    )
    if duplicate_family_ids:
        raise RuntimeError(
            f"Split integrity failure: {records.FAMILIES_FILE} repeats family ids "
            f"{duplicate_family_ids}; one family cannot carry two splits."
        )
    family_by_id = {family.family_id: family for family in families}
    prompt_by_id = {prompt.prompt_id: prompt for prompt in prompts}
    review_by_response = {review.response_id: review for review in reviews}
    decision_by_response = {decision.response_id: decision for decision in decisions}

    train_rows: list[dict[str, Any]] = []
    eval_rows: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()

    for response in responses:
        decision = decision_by_response.get(response.response_id)
        if decision is None or not decision.keep:
            continue
        prompt = prompt_by_id.get(response.prompt_id)
        if prompt is None:
            continue
        family = family_by_id.get(prompt.family_id)
        if family is None:
            continue
        meta = {
            "response_id": response.response_id,
            "prompt_id": prompt.prompt_id,
            "family_id": family.family_id,
            "target_id": spec.target_id,
            "spec_version": spec.version,
            "domain": family.domain,
            "case_type": decision.final_case_type,
            "variant": prompt.variant,
            "mode": prompt.mode,
            "counterfactual_group_id": family.counterfactual_group_id,
            "varied_fact": family.varied_fact,
            "situation_features": family.situation_features,
            "principles_applied": response.hidden.get("principles_applied") or [],
            # Repaired here too, so runs generated before the fix still export usable ids.
            "source_passages": normalise_passage_ids(
                spec, [str(p) for p in (response.hidden.get("source_passages") or [])]
            ),
            "generator_model": response.generator_model,
            "divergence_status": decision.divergence_status,
            "divergence_kind": decision.divergence_kind,
        }
        if family.split == "train":
            train_rows.append(
                {
                    "messages": [
                        {"role": "user", "content": prompt.text},
                        {"role": "assistant", "content": render_assistant_message(response)},
                    ],
                    "meta": meta,
                }
            )
            counts[f"train:{family.domain}"] += 1
            counts[f"train_case:{decision.final_case_type}"] += 1
        elif family.split == "eval":
            expected, pass_fail = derive_grading_key(
                spec, response, review_by_response.get(response.response_id)
            )
            eval_rows.append(
                {
                    "prompt": prompt.text,
                    "case_type": decision.final_case_type,
                    "family_id": family.family_id,
                    "variant": prompt.variant,
                    "expected_behavior": expected,
                    "pass_fail_notes": pass_fail,
                    "reference_answer": render_assistant_message(response),
                    "meta": meta,
                }
            )
            counts[f"eval:{family.domain}"] += 1
            counts[f"eval_case:{decision.final_case_type}"] += 1
            if prompt.variant != "base":
                counts["eval_case:reframing"] += 1

    def split_groups(rows: list[dict[str, Any]]) -> set[str]:
        return {
            row["meta"]["counterfactual_group_id"] or row["meta"]["family_id"] for row in rows
        }

    overlap = split_groups(train_rows) & split_groups(eval_rows)
    if overlap:
        raise RuntimeError(
            f"Split integrity failure: these families or counterfactual groups appear in "
            f"both train and eval: {sorted(overlap)}"
        )
    leaks = _passage_ids_in_assistant_text(spec, train_rows, eval_rows)
    if leaks:
        raise RuntimeError(
            f"Hidden metadata leaked into user-visible text: passage ids {sorted(leaks)} "
            f"appear in an assistant message or an evaluation prompt. The rendering template "
            f"must never include record fields."
        )

    records.write_jsonl(run_dir / SFT_FILE, train_rows)
    records.write_jsonl(run_dir / EVAL_FILE, eval_rows)

    usage = summarise_usage(run_dir / records.USAGE_FILE, config.pricing)
    manifest = {
        "target_id": spec.target_id,
        "target_name": spec.name,
        "spec_version": spec.version,
        "run_id": run_dir.name,
        "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "config_file": str(config.path),
        "config_hash": config.config_hash(),
        "models": {name: role.model for name, role in config.roles.items() if role.enabled},
        "counts": {
            "families": len(families),
            "families_train": sum(1 for f in families if f.split == "train"),
            "families_eval": sum(1 for f in families if f.split == "eval"),
            "families_reserved": sum(1 for f in families if f.split == "reserved"),
            "prompts": len(prompts),
            "responses": len(responses),
            "kept": sum(1 for d in decisions if d.keep),
            "dropped": sum(1 for d in decisions if not d.keep),
            "sft_train_rows": len(train_rows),
            "eval_rows": len(eval_rows),
            "explicit_mode_rows": sum(
                1 for row in train_rows + eval_rows if row["meta"]["mode"] == "explicit"
            ),
            "counterfactual_groups": len(
                {
                    row["meta"]["counterfactual_group_id"]
                    for row in train_rows + eval_rows
                    if row["meta"]["counterfactual_group_id"]
                }
            ),
            "by_bucket": dict(sorted(counts.items())),
        },
        "license_constraints": license_constraints(spec),
        "redistribution_note": config.raw.get("redistribution_note", ""),
        "cost": {
            "usd": usage["cost_usd"] if usage["cost_known"] else None,
            "display": format_cost(usage),
            "calls": usage["calls"],
            "prompt_tokens": usage["prompt_tokens"],
            "completion_tokens": usage["completion_tokens"],
            "reasoning_tokens": usage["reasoning_tokens"],
        },
    }
    (run_dir / MANIFEST_FILE).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    logger.info(
        "export: %d training rows, %d eval rows -> %s",
        len(train_rows),
        len(eval_rows),
        run_dir,
    )
    return {"sft_train_rows": len(train_rows), "eval_rows": len(eval_rows)}
