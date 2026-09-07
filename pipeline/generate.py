"""Generation stage: families -> user prompts -> responses.

The coverage plan these stages fill in lives in pipeline/plan.py. Idempotent on a run
directory: families, prompts and responses that already exist are kept, and only the
missing ones are generated.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from pipeline import records
from pipeline.config import RunConfig
from pipeline.model import (
    ModelClient,
    ModelError,
    extract_field,
    extract_list,
    gather_bounded,
)
from pipeline.plan import (
    FamilySlot,
    align_counterfactual_groups,
    avoided_topic_hit,
    pair_counterfactual_slots,
    plan_families,
    selected_layers,
)
from pipeline.records import Family, Prompt, Response, short_id
from pipeline.target import (
    TargetSpec,
    normalise_passage_ids,
    render_for_generator,
    render_key_passages,
)
from prompts import render
from prompts.generation import (
    COUNTERFACTUAL_INSTRUCTIONS,
    SHAPE_REMINDER,
    EXPLICIT_MODE_PROMPT_INSTRUCTIONS,
    EXPLICIT_MODE_RESPONSE_INSTRUCTIONS,
    FAMILY_GENERATION_PROMPT,
    GENERATOR_SYSTEM_PROMPT,
    NEUTRAL_MODE_PROMPT_INSTRUCTIONS,
    NEUTRAL_MODE_RESPONSE_INSTRUCTIONS,
    PROMPT_VARIANT_PROMPT,
    REFRAMING_PROMPT,
    RESPONSE_GENERATION_PROMPT,
    RESPONSE_REVISION_PROMPT,
)
from prompts.review import FIDELITY_REVIEW_PROMPT, REVIEWER_SYSTEM_PROMPT

logger = logging.getLogger("pipeline.generate")


FAMILY_JSON_SHAPE = (
    '{"families": [{"seed_situation": "...", "why_it_is_hard": "...", '
    '"principle_ids": ["..."], "tradeoff_ids": ["..."], "source_passage_ids": ["..."], '
    '"case_type_intent": "ordinary", "varied_fact": "", "situation_features": {...}}]}'
)
PROMPT_JSON_SHAPE = '{"prompts": [{"text": "...", "register": "long_detailed"}]}'


def looks_like_family(item: Any) -> bool:
    return isinstance(item, dict) and bool(str(item.get("seed_situation", "")).strip())


def looks_like_prompt(item: Any) -> bool:
    return isinstance(item, dict) and bool(str(item.get("text", "")).strip())


def dump_debug(run_dir: Path, name: str, content: Any) -> Path:
    """Write a raw model payload to <run_dir>/debug/ so a short batch can be diagnosed.

    Batches that come back short are the one failure mode that is invisible after the
    fact, because the parsed record is simply absent. Keeping the payload costs nothing.
    """
    debug_dir = run_dir / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    path = debug_dir / f"{name}.json"
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text)[:60]


async def generate_families(
    client: ModelClient,
    spec: TargetSpec,
    config: RunConfig,
    run_dir: Path,
    slots: list[FamilySlot],
    existing: list[Family],
    attempt: int = 1,
) -> list[Family]:
    """One generator call per domain batch. Returns all families, old and new.

    A batch sometimes comes back short or empty. Because the stage is idempotent on the
    run directory, the shortfall is simply retried once here rather than left for a
    manual re-run.
    """
    settings = config.generation
    per_call = int(settings.get("families_per_call", 4))
    max_passage_chars = int(settings.get("max_passage_chars_families", 40000))
    layer_ids = selected_layers(spec, config)
    generator = config.role("generator")

    done_by_id = {family.family_id: family for family in existing}
    if len(existing) >= len(slots):
        logger.info("families: %d already present, nothing to generate", len(existing))
        return existing

    remaining = slots[len(existing) :]
    by_domain: dict[str, list[FamilySlot]] = {}
    for slot in remaining:
        by_domain.setdefault(slot.domain, []).append(slot)
    batches: list[tuple[str, list[FamilySlot]]] = []
    # Batch size is forced even so that a plan-time pair is never split in half.
    batch_size = max(2, per_call - (per_call % 2))
    for domain, domain_slots in by_domain.items():
        ordered_slots = sorted(
            domain_slots, key=lambda slot: (slot.counterfactual_group or "~", slot.index)
        )
        for start_index in range(0, len(ordered_slots), batch_size):
            batches.append((domain, ordered_slots[start_index : start_index + batch_size]))

    used_situations = [family.seed_situation[:160] for family in existing]
    spec_text = render_for_generator(spec, layer_ids=layer_ids, stage="families")
    passages_text = render_key_passages(spec, max_chars=max_passage_chars)
    avoid_words = spec.avoid_keywords()

    async def run_batch(domain: str, batch: list[FamilySlot]) -> list[dict[str, Any]]:
        pairs = pair_counterfactual_slots(batch)
        lines = []
        for position, slot in enumerate(batch):
            group = pairs.get(position)
            note = f", contrastive group {group}" if group else ""
            explicit = ", EXPLICIT slice" if slot.mode == "explicit" else ""
            lines.append(
                f"- family {position + 1}: tradeoff_ids={slot.tradeoff_ids or ['(any)']}, "
                f"case_type_intent={slot.case_type_intent!r}{note}{explicit}"
            )
        user_message = render(
            FAMILY_GENERATION_PROMPT,
            target_spec=spec_text,
            key_passages=passages_text,
            n_families=len(batch),
            domain=domain,
            assignments="\n".join(lines),
            counterfactual_instructions=(COUNTERFACTUAL_INSTRUCTIONS if pairs else ""),
            used_situations="\n".join(f"- {s}" for s in used_situations) or "- (none yet)",
        )
        label = f"families_{_safe_name(domain)}_{batch[0].index}"
        return await _request_items(
            client=client,
            role=generator,
            system_prompt=GENERATOR_SYSTEM_PROMPT,
            user_message=user_message,
            wanted=len(batch),
            keys=("families", "family", "scenario_families", "items"),
            looks_like_item=looks_like_family,
            json_shape=FAMILY_JSON_SHAPE,
            run_dir=run_dir,
            label=label,
            stage="generate.families",
            record_id=f"{domain}:{batch[0].index}",
        )

    results = await gather_bounded([run_batch(domain, batch) for domain, batch in batches])

    families = list(existing)
    for (domain, batch), result in zip(batches, results):
        if isinstance(result, Exception):
            logger.error("family batch for domain %s failed: %s", domain, result)
            continue
        if len(result) < len(batch):
            logger.warning(
                "family batch for domain %s returned %d families for %d assignments",
                domain,
                len(result),
                len(batch),
            )
        pairs = pair_counterfactual_slots(batch)
        for position, (slot, item) in enumerate(zip(batch, result)):
            seed = str(item.get("seed_situation", "")).strip()
            if not seed:
                continue
            family_id = short_id("fam", spec.target_id, domain, seed)
            if family_id in done_by_id:
                continue
            group = pairs.get(position)
            split, reason = slot.split, ""
            hit = avoided_topic_hit(seed, avoid_words)
            if hit:
                # Never deleted: reserved with the reason recorded, so the screen is auditable.
                split, reason = "reserved", f"avoided-topic keyword in seed situation: {hit}"
            family = Family(
                family_id=family_id,
                target_id=spec.target_id,
                domain=domain,
                tradeoff_ids=[str(t) for t in (item.get("tradeoff_ids") or slot.tradeoff_ids)],
                principle_ids=[str(p) for p in (item.get("principle_ids") or [])],
                case_type_intent=slot.case_type_intent,
                seed_situation=seed,
                why_it_is_hard=str(item.get("why_it_is_hard", "")).strip(),
                split=split,
                source_passage_ids=normalise_passage_ids(
                    spec, [str(p) for p in (item.get("source_passage_ids") or [])]
                ),
                generator_model=generator.model,
                spec_version=spec.version,
                counterfactual_group_id=(
                    short_id("cf", spec.target_id, group) if group else None
                ),
                varied_fact=str(item.get("varied_fact", "")).strip(),
                situation_features={
                    key: str(value)
                    for key, value in (item.get("situation_features") or {}).items()
                    if value
                },
                reserved_reason=reason,
                mode=slot.mode,
            )
            done_by_id[family_id] = family
            families.append(family)
            used_situations.append(seed[:160])
    align_counterfactual_groups(families)
    records.write_jsonl(run_dir / records.FAMILIES_FILE, families)
    logger.info(
        "families: %d of %d planned (%d new, %d reserved by the avoided-topic screen)",
        len(families),
        len(slots),
        len(families) - len(existing),
        sum(1 for f in families if f.reserved_reason),
    )
    max_attempts = int(settings.get("family_generation_attempts", 2))
    if len(families) < len(slots) and len(families) > len(existing) and attempt < max_attempts:
        logger.info(
            "families: retrying the %d unfilled slots (attempt %d of %d)",
            len(slots) - len(families),
            attempt + 1,
            max_attempts,
        )
        return await generate_families(
            client, spec, config, run_dir, slots, families, attempt + 1
        )
    return families


def mode_instructions(mode: str, forbidden_terms: str, target_name: str) -> str:
    """The cue block a response prompt gets: explicit slices may name the tradition.

    The name is passed in, because a generator told only "you may name the tradition"
    will invent one.
    """
    if mode == "explicit":
        return render(EXPLICIT_MODE_RESPONSE_INSTRUCTIONS, target_name=target_name)
    return render(NEUTRAL_MODE_RESPONSE_INSTRUCTIONS, forbidden_terms=forbidden_terms)


async def _request_items(
    *,
    client: ModelClient,
    role: Any,
    system_prompt: str,
    user_message: str,
    wanted: int,
    keys: tuple[str, ...],
    looks_like_item: Any,
    json_shape: str,
    run_dir: Path,
    label: str,
    stage: str,
    record_id: str,
) -> list[dict[str, Any]]:
    """Ask for `wanted` JSON items, retry once if short, and never lose the raw payload.

    A batch that silently comes back empty is the one failure the artifacts cannot
    explain afterwards, because the missing records leave no trace. So every short or
    unparseable reply is written to <run_dir>/debug/ before the retry.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    items: list[dict[str, Any]] = []
    for attempt in (1, 2):
        try:
            payload, response = await client.complete_json(
                role, messages, stage=stage, record_id=record_id
            )
        except ModelError as error:
            if getattr(error, "raw_text", ""):
                dump_debug(run_dir, f"{label}_attempt{attempt}_unparsed", error.raw_text)
            raise
        items = [
            item
            for item in extract_list(payload, *keys, looks_like_item=looks_like_item)
            if looks_like_item(item)
        ]
        if len(items) >= wanted or attempt == 2:
            if len(items) < wanted:
                dump_debug(
                    run_dir,
                    f"{label}_attempt{attempt}_short",
                    {"wanted": wanted, "got": len(items), "payload": payload,
                     "raw_text": response.text},
                )
            return items
        dump_debug(
            run_dir,
            f"{label}_attempt1_short",
            {"wanted": wanted, "got": len(items), "payload": payload, "raw_text": response.text},
        )
        logger.warning(
            "%s returned %d of %d items; retrying once with an explicit shape reminder "
            "(payload saved to %s)",
            label,
            len(items),
            wanted,
            run_dir / "debug",
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": user_message
                + render(SHAPE_REMINDER, expected=wanted, shape=json_shape),
            },
        ]
    return items


async def generate_prompts(
    client: ModelClient,
    spec: TargetSpec,
    config: RunConfig,
    run_dir: Path,
    families: list[Family],
    existing: list[Prompt],
) -> list[Prompt]:
    """k user prompts per family; eval families also get reframing variants."""
    settings = config.generation
    generator = config.role("generator")
    train_k = int(settings.get("prompts_per_family", 3))
    eval_k = int(settings.get("eval_prompts_per_family", 1))
    reframing_variants = list(settings.get("reframing_variants", ["setting_shift", "fiction"]))
    reframing_families = int(settings.get("reframing_families", 0))
    forbidden = ", ".join(spec.forbidden_terms) or "(none)"

    mode_by_family = {family.family_id: family.mode for family in families}
    families_with_prompts = {prompt.family_id for prompt in existing}
    todo = [family for family in families if family.family_id not in families_with_prompts]
    if not todo:
        logger.info("prompts: %d already present, nothing to generate", len(existing))
        return existing

    async def run_family(family: Family) -> tuple[Family, list[dict[str, Any]]]:
        n_prompts = eval_k if family.split == "eval" else train_k
        mode = mode_by_family.get(family.family_id, "neutral")
        user_message = render(
            PROMPT_VARIANT_PROMPT,
            seed_situation=family.seed_situation,
            why_it_is_hard=family.why_it_is_hard,
            n_prompts=n_prompts,
            mode_instructions=(
                render(EXPLICIT_MODE_PROMPT_INSTRUCTIONS, target_name=spec.name)
                if mode == "explicit"
                else render(NEUTRAL_MODE_PROMPT_INSTRUCTIONS, forbidden_terms=forbidden)
            ),
        )
        items = await _request_items(
            client=client,
            role=generator,
            system_prompt=GENERATOR_SYSTEM_PROMPT,
            user_message=user_message,
            wanted=n_prompts,
            keys=("prompts", "prompt", "messages", "items"),
            looks_like_item=looks_like_prompt,
            json_shape=PROMPT_JSON_SHAPE,
            run_dir=run_dir,
            label=f"prompts_{family.family_id}",
            stage="generate.prompts",
            record_id=family.family_id,
        )
        return family, items

    results = await gather_bounded([run_family(family) for family in todo])

    prompts = list(existing)
    new_prompts: list[Prompt] = []
    for result in results:
        if isinstance(result, Exception):
            logger.error("prompt generation failed: %s", result)
            continue
        family, items = result
        for item in items:
            text = str(item.get("text", "")).strip()
            if not text:
                continue
            new_prompts.append(
                Prompt(
                    prompt_id=short_id("pr", family.family_id, "base", text),
                    family_id=family.family_id,
                    variant="base",
                    text=text,
                    case_type=family.case_type_intent,
                    mode=mode_by_family.get(family.family_id, "neutral"),
                )
            )

    # Reframing variants exist only for eval families: they test surface robustness.
    eval_families = [family for family in families if family.split == "eval"]
    reframe_targets = eval_families[:reframing_families] if reframing_families else []
    reframe_jobs: list[tuple[Prompt, str]] = []
    by_family: dict[str, list[Prompt]] = {}
    for prompt in new_prompts + prompts:
        by_family.setdefault(prompt.family_id, []).append(prompt)
    for position, family in enumerate(reframe_targets):
        base_prompts = [p for p in by_family.get(family.family_id, []) if p.variant == "base"]
        if not base_prompts or not reframing_variants:
            continue
        variant = reframing_variants[position % len(reframing_variants)]
        reframe_jobs.append((base_prompts[0], variant))

    async def run_reframe(base_prompt: Prompt, variant: str) -> tuple[Prompt, str, str]:
        payload, _ = await client.complete_json(
            generator,
            [
                {"role": "system", "content": GENERATOR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": render(
                        REFRAMING_PROMPT,
                        original_prompt=base_prompt.text,
                        variant=variant,
                        forbidden_terms=forbidden,
                    ),
                },
            ],
            stage="generate.reframing",
            record_id=base_prompt.prompt_id,
        )
        return base_prompt, variant, extract_field(payload, "text", "prompt", "message").strip()

    if reframe_jobs:
        reframed = await gather_bounded([run_reframe(p, v) for p, v in reframe_jobs])
        for result in reframed:
            if isinstance(result, Exception):
                logger.error("reframing failed: %s", result)
                continue
            base_prompt, variant, text = result
            if not text:
                continue
            new_prompts.append(
                Prompt(
                    prompt_id=short_id("pr", base_prompt.family_id, variant, text),
                    family_id=base_prompt.family_id,
                    variant=variant,
                    text=text,
                    case_type=base_prompt.case_type,
                    mode=base_prompt.mode,
                )
            )

    prompts.extend(new_prompts)
    records.write_jsonl(run_dir / records.PROMPTS_FILE, prompts)
    logger.info("prompts: %d total (%d new)", len(prompts), len(new_prompts))
    return prompts


async def generate_responses(
    client: ModelClient,
    spec: TargetSpec,
    config: RunConfig,
    run_dir: Path,
    families: list[Family],
    prompts: list[Prompt],
    existing: list[Response],
) -> list[Response]:
    """One deliberation+answer per prompt, with optional critique->revise rounds."""
    settings = config.generation
    generator = config.role("generator")
    revise_rounds = int(settings.get("revise_rounds", 0))
    max_passage_chars = int(settings.get("max_passage_chars_responses", 8000))
    layer_ids = selected_layers(spec, config)
    forbidden = ", ".join(spec.forbidden_terms) or "(none)"
    family_by_id = {family.family_id: family for family in families}

    done = {response.prompt_id for response in existing}
    todo = [prompt for prompt in prompts if prompt.prompt_id not in done]
    if not todo:
        logger.info("responses: %d already present, nothing to generate", len(existing))
        return existing

    async def run_prompt(prompt: Prompt) -> Response | None:
        family = family_by_id.get(prompt.family_id)
        if family is None:
            return None
        spec_text = render_for_generator(
            spec,
            principle_ids=family.principle_ids or None,
            tradeoff_ids=family.tradeoff_ids or None,
            layer_ids=layer_ids,
            stage="responses",
        )
        passages_text = render_key_passages(
            spec, family.source_passage_ids or None, max_chars=max_passage_chars
        )
        messages = [
            {"role": "system", "content": GENERATOR_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": render(
                    RESPONSE_GENERATION_PROMPT,
                    target_spec=spec_text,
                    key_passages=passages_text,
                    user_prompt=prompt.text,
                    why_it_is_hard=family.why_it_is_hard,
                    mode_instructions=mode_instructions(prompt.mode, forbidden, spec.name),
                ),
            },
        ]
        try:
            payload, response = await client.complete_json(
                generator, messages, stage="generate.responses", record_id=prompt.prompt_id
            )
        except ModelError as error:
            if getattr(error, "raw_text", ""):
                dump_debug(run_dir, f"response_{prompt.prompt_id}_unparsed", error.raw_text)
            raise
        if not str(payload.get("answer", "")).strip():
            dump_debug(
                run_dir,
                f"response_{prompt.prompt_id}_empty",
                {"payload": payload, "raw_text": response.text},
            )
        rounds_done = 0
        for _ in range(revise_rounds):
            critique = await _critique_for_revision(
                client, config, spec, prompt, payload, passages_text, forbidden
            )
            if critique is None or critique.get("verdict") == "accept":
                break
            revised, response = await client.complete_json(
                generator,
                [
                    {"role": "system", "content": GENERATOR_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": render(
                            RESPONSE_REVISION_PROMPT,
                            target_spec=spec_text,
                            key_passages=passages_text,
                            user_prompt=prompt.text,
                            deliberation=payload.get("deliberation", ""),
                            answer=payload.get("answer", ""),
                            verdict=critique.get("verdict", ""),
                            issues="\n".join(f"- {i}" for i in critique.get("issues", [])),
                            rationale=critique.get("rationale", ""),
                            mode_instructions=mode_instructions(prompt.mode, forbidden, spec.name),
                        ),
                    },
                ],
                stage="generate.revise",
                record_id=prompt.prompt_id,
            )
            payload = revised
            rounds_done += 1
        return Response(
            response_id=short_id("resp", prompt.prompt_id, generator.model),
            prompt_id=prompt.prompt_id,
            deliberation=str(payload.get("deliberation", "")).strip(),
            answer=str(payload.get("answer", "")).strip(),
            hidden={
                "principles_applied": [str(p) for p in (payload.get("principles_applied") or [])],
                "source_passages": normalise_passage_ids(
                    spec, [str(p) for p in (payload.get("source_passages") or [])]
                ),
                "intended_divergence_note": str(payload.get("intended_divergence_note", "")).strip(),
            },
            generator_model=generator.model,
            usage=dict(response.usage or {}),
            revise_rounds=rounds_done,
            mode=prompt.mode,
        )

    results = await gather_bounded([run_prompt(prompt) for prompt in todo])
    responses = list(existing)
    failures = 0
    for result in results:
        if isinstance(result, Exception):
            failures += 1
            logger.error("response generation failed: %s", result)
            continue
        if result is not None:
            responses.append(result)
    records.write_jsonl(run_dir / records.RESPONSES_FILE, responses)
    logger.info(
        "responses: %d total (%d new, %d failed)",
        len(responses),
        len(responses) - len(existing),
        failures,
    )
    return responses


async def _critique_for_revision(
    client: ModelClient,
    config: RunConfig,
    spec: TargetSpec,
    prompt: Prompt,
    payload: dict[str, Any],
    passages_text: str,
    forbidden: str,
) -> dict[str, Any] | None:
    """In-loop critique used only when revise_rounds > 0. The validate stage reviews again."""
    from pipeline.target import render_for_reviewer

    try:
        critique, _ = await client.complete_json(
            config.role("reviewer"),
            [
                {"role": "system", "content": REVIEWER_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": render(
                        FIDELITY_REVIEW_PROMPT,
                        target_spec=render_for_reviewer(spec),
                        key_passages=passages_text,
                        user_prompt=prompt.text,
                        deliberation=payload.get("deliberation", ""),
                        answer=payload.get("answer", ""),
                        principles_claimed=", ".join(payload.get("principles_applied") or []),
                        passages_claimed=", ".join(payload.get("source_passages") or []),
                        tradeoff_summary="(see the target specification above)",
                        forbidden_terms=forbidden,
                    ),
                },
            ],
            stage="generate.critique",
            record_id=prompt.prompt_id,
        )
        return critique
    except ModelError as error:
        logger.warning("in-loop critique failed for %s: %s", prompt.prompt_id, error)
        return None


async def run_stage(
    config: RunConfig, spec: TargetSpec, run_dir: Path, n_families: int | None = None
) -> dict[str, int]:
    """Entry point for `main.py generate`."""
    settings = config.generation
    total = n_families if n_families is not None else int(settings.get("n_families", 12))
    slots = plan_families(spec, settings, total)

    existing_families = records.read_jsonl(run_dir / records.FAMILIES_FILE, Family)
    existing_prompts = records.read_jsonl(run_dir / records.PROMPTS_FILE, Prompt)
    existing_responses = records.read_jsonl(run_dir / records.RESPONSES_FILE, Response)

    async with ModelClient.from_config(config, run_dir / records.USAGE_FILE, "generate") as client:
        families = await generate_families(
            client, spec, config, run_dir, slots, existing_families
        )
        prompts = await generate_prompts(client, spec, config, run_dir, families, existing_prompts)
        responses = await generate_responses(
            client, spec, config, run_dir, families, prompts, existing_responses
        )
    return {"families": len(families), "prompts": len(prompts), "responses": len(responses)}
