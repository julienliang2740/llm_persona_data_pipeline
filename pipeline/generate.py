"""Generation stage: families -> user prompts -> responses.

The coverage plan these stages fill in lives in pipeline/plan.py. Idempotent on a run
directory: families, prompts and responses that already exist are kept, and only the
missing ones are generated.
"""

from __future__ import annotations

import hashlib
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
from pipeline.validate import jaccard  # reframing variants that copy their base are rejected
from pipeline.target import (
    TargetSpec,
    normalise_passage_ids,
    split_passage_citation,
    render_for_generator,
    render_key_passages,
)
from prompts import render
from prompts.generation import (
    ARCHAIC_EXAMPLES_BLOCK,
    COUNTERFACTUAL_INSTRUCTIONS,
    DEFAULT_DELIBERATION_SHAPE,
    HYPOTHESIS_BLOCK,
    REFRAMING_VARIANT_INSTRUCTIONS,
    SHAPE_REMINDER,
    STIPULATION_GUARD,
    VARIED_FACT_FIELD,
    EXPLICIT_MODE_PROMPT_INSTRUCTIONS,
    EXPLICIT_MODE_RESPONSE_INSTRUCTIONS,
    FAMILY_GENERATION_PROMPT,
    GENERATOR_SYSTEM_PROMPT,
    NEUTRAL_MODE_PROMPT_INSTRUCTIONS,
    NEUTRAL_MODE_RESPONSE_INSTRUCTIONS,
    PROMPT_VARIANT_PROMPT,
    REFRAMING_PROMPT,
    RESPONSE_GENERATION_PROMPT,
)

logger = logging.getLogger("pipeline.generate")


class IncompleteGroupError(RuntimeError):
    """A planned counterfactual pair produced only one of its two families."""


FAMILY_JSON_SHAPE = (
    '{"families": [{"seed_situation": "...", "why_it_is_hard": "...", '
    '"principle_ids": ["..."], "tradeoff_ids": ["..."], "source_passage_ids": ["..."], '
    '"case_type_intent": "ordinary", "divergence_hypothesis_id": "", "varied_fact": "", '
    '"situation_features": {...}}]}'
)
PROMPT_JSON_SHAPE = '{"prompts": [{"text": "...", "register": "long_detailed"}]}'


def _split_passage_citations(
    spec: TargetSpec, returned: list[Any], max_passages: int = 3
) -> tuple[list[str], dict[str, str]]:
    """Split "<id>: <what it grounded>" citations into normalised ids and their clauses.

    Capped at three. Round-1 responses listed up to five passages with no statement of what
    each one supported, which made the citation unauditable.
    """
    ids: list[str] = []
    notes: dict[str, str] = {}
    for entry in returned:
        passage_id, clause = split_passage_citation(spec, str(entry))
        if not passage_id or passage_id in notes:
            continue
        notes[passage_id] = clause
        ids.append(passage_id)
        if len(ids) >= max_passages:
            break
    return ids, notes


def _keeps_deliberation(prompt_id: str, fraction: float) -> bool:
    """Deterministic per-prompt draw for the no-deliberation ablation slice."""
    if fraction >= 1.0:
        return True
    if fraction <= 0.0:
        return False
    digest = int(hashlib.sha256(prompt_id.encode("utf-8")).hexdigest()[:8], 16)
    return (digest % 1000) / 1000.0 < fraction


def _merge_situation_features(slot: FamilySlot, item: dict[str, Any]) -> dict[str, str]:
    """The plan owns the closed enums; the generator only adds relationship and a note."""
    returned = item.get("situation_features") or {}
    features = {
        "role_type": slot.role_type,
        "harm_severity": slot.harm_severity,
        "urgency": slot.urgency,
        "public_or_private": slot.public_or_private,
    }
    for key in ("relationship", "note"):
        value = str(returned.get(key, "")).strip()
        if value:
            features[key] = value
    return {key: value for key, value in features.items() if value}


def _situation_signature(family: Family) -> str:
    """What the generator is shown about an existing family, so it does not repeat it.

    The structural key matters as much as the prose: round 1 produced four pairs that were
    the same situation in different words, which a prose-only list did not prevent.
    """
    features = family.situation_features or {}
    parts = [
        family.domain,
        features.get("role_type", ""),
        features.get("harm_severity", ""),
        features.get("relationship", ""),
    ]
    shape = "/".join(part for part in parts if part)
    return f"[{shape}] {family.seed_situation[:150]}"


def validated_ids(
    returned: Any, known: set[str], fallback: list[str], label: str, family_hint: str
) -> list[str]:
    """Keep only ids the spec actually defines; fall back to the slot's assignment.

    A generator returned the tradeoff id "f orgiveness_vs_protection" with a stray space.
    It resolved to nothing, so the response prompt for three Catholic families said
    "(no tradeoffs recorded)" where the tradeoff should have been.
    """
    values = [str(item).strip() for item in (returned or []) if str(item).strip()]
    good = [value for value in values if value in known]
    bad = [value for value in values if value not in known]
    if bad:
        logger.warning(
            "%s: generator returned %s id(s) not in the spec: %s; falling back to %s",
            family_hint,
            label,
            bad,
            fallback or "(none)",
        )
    return good or list(fallback)


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
    existing = _backfill_slot_indices(existing, slots)
    filled = {family.slot_index for family in existing if family.slot_index >= 0}
    # Retries refill the slot indices that are actually empty. Matching by count instead
    # regenerated an already-filled slot and silently dropped a planned pair.
    remaining = [slot for slot in slots if slot.slot_index not in filled]
    if not remaining:
        logger.info("families: all %d planned slots are filled", len(slots))
        _require_complete_groups(existing, slots)
        return existing

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

    hypothesis_text = {
        str(h.get("id")): " ".join(str(h.get("description", "")).split())[:220]
        for h in spec.divergence_hypotheses
        if h.get("id")
    }
    choice_text = {
        str(c.get("id")): " ".join(str(c.get("question", "")).split())[:200]
        for c in spec.unresolved_choices
        if c.get("id")
    }
    known_tradeoffs = {str(t.get("id")) for t in spec.tradeoffs if t.get("id")}
    known_principles = {str(p.get("id")) for p in spec.principles if p.get("id")}
    known_hypotheses = {str(h.get("id")) for h in spec.divergence_hypotheses if h.get("id")}
    used_situations = [_situation_signature(family) for family in existing]
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
            # Everything the plan decided must reach the generator as an assignment; the
            # enums are merged back from the slot afterwards, so an unstated one is unplanned.
            parts = [
                f"tradeoff_ids={slot.tradeoff_ids or ['(any)']}",
                f"case_type_intent={slot.case_type_intent!r}",
            ]
            if slot.institution:
                parts.append(f"institution={slot.institution!r}")
            for field_name in ("role_type", "harm_severity", "urgency", "public_or_private", "asker_stance"):
                value = getattr(slot, field_name, "")
                if value:
                    parts.append(f"{field_name}={value}")
            if slot.divergence_hypothesis_id:
                parts.append(
                    f"divergence_hypothesis_id={slot.divergence_hypothesis_id!r}"
                    f" ({hypothesis_text.get(slot.divergence_hypothesis_id, '')})"
                )
            if slot.unresolved_choice_id:
                parts.append(
                    f"open_question={slot.unresolved_choice_id!r}"
                    f" ({choice_text.get(slot.unresolved_choice_id, '')})"
                )
            lines.append(f"- family {position + 1}: " + ", ".join(parts) + note + explicit)
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
            if not (item.get("situation_features") or {}).get("relationship"):
                # Round 1 shipped families with no recorded features at all, which made the
                # coverage table and the structural dedupe key meaningless.
                logger.warning(
                    "slot %d (%s) returned no relationship in situation_features; the plan's "
                    "assigned axes are still used",
                    slot.slot_index,
                    domain,
                )
            family_id = short_id("fam", spec.target_id, domain, seed)
            if family_id in done_by_id:
                continue
            group = pairs.get(position)
            split, reason = slot.split, ""
            hit = avoided_topic_hit(seed, avoid_words)
            if hit:
                # Never deleted: reserved with the reason recorded, so the screen is auditable.
                split, reason = "reserved", f"avoided-topic keyword in seed situation: {hit}"
            hint = f"slot {slot.slot_index} ({domain})"
            family = Family(
                family_id=family_id,
                target_id=spec.target_id,
                domain=domain,
                tradeoff_ids=validated_ids(
                    item.get("tradeoff_ids"), known_tradeoffs, slot.tradeoff_ids, "tradeoff", hint
                ),
                principle_ids=validated_ids(
                    item.get("principle_ids"), known_principles, [], "principle", hint
                ),
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
                situation_features=_merge_situation_features(slot, item),
                reserved_reason=reason,
                mode=slot.mode,
                slot_index=slot.slot_index,
                asker_stance=slot.asker_stance,
                institution=slot.institution,
                layers_generated=list(layer_ids),
                divergence_hypothesis_id=(
                    validated_ids(
                        [item.get("divergence_hypothesis_id") or slot.divergence_hypothesis_id],
                        known_hypotheses,
                        [slot.divergence_hypothesis_id] if slot.divergence_hypothesis_id else [],
                        "divergence hypothesis",
                        hint,
                    )
                    or [""]
                )[0],
            )
            done_by_id[family_id] = family
            families.append(family)
            used_situations.append(_situation_signature(family))
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
    still_empty = [s.slot_index for s in slots if s.slot_index not in {f.slot_index for f in families}]
    if still_empty and len(families) > len(existing) and attempt < max_attempts:
        logger.info(
            "families: retrying slot indices %s (attempt %d of %d)",
            still_empty,
            attempt + 1,
            max_attempts,
        )
        return await generate_families(
            client, spec, config, run_dir, slots, families, attempt + 1
        )
    if still_empty:
        logger.warning("families: slot indices %s are still unfilled", still_empty)
    _require_complete_groups(families, slots)
    return families


def _backfill_slot_indices(families: list[Family], slots: list[FamilySlot]) -> list[Family]:
    """Give slot indices to families written before the field existed, in file order."""
    unset = [family for family in families if family.slot_index < 0]
    if not unset:
        return families
    taken = {family.slot_index for family in families if family.slot_index >= 0}
    free = [slot.slot_index for slot in slots if slot.slot_index not in taken]
    for family, slot_index in zip(unset, free):
        family.slot_index = slot_index
    logger.info("families: backfilled slot indices for %d pre-existing families", len(unset))
    return families


def _require_complete_groups(families: list[Family], slots: list[FamilySlot]) -> None:
    """A half-generated contrastive pair is worse than none: stop rather than ship it."""
    planned: dict[str, list[int]] = {}
    for slot in slots:
        if slot.counterfactual_group:
            planned.setdefault(slot.counterfactual_group, []).append(slot.slot_index)
    filled = {family.slot_index for family in families}
    incomplete = {
        label: [index for index in members if index not in filled]
        for label, members in planned.items()
        if any(index not in filled for index in members)
    }
    if incomplete:
        raise IncompleteGroupError(
            "Contrastive groups are incomplete, so the contrast they exist to draw would "
            "be lost. Missing slot indices per group: "
            + "; ".join(f"{label}: {missing}" for label, missing in sorted(incomplete.items()))
            + ". Re-run the generate stage on the same --run to fill them."
        )


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
    # The stipulation guard quotes the family's own hypothesis, so the writer knows the
    # specific sentence it must not put in the user's mouth.
    hypothesis_text = {
        str(item.get("id")): " ".join(str(item.get("description", "")).split())
        for item in spec.divergence_hypotheses
        if item.get("id")
    }

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
            stipulation_guard=(
                render(
                    STIPULATION_GUARD,
                    hypothesis=hypothesis_text.get(family.divergence_hypothesis_id)
                    or "this target reaches a different conclusion from a general assistant",
                )
                if family.case_type_intent == "divergence"
                else ""
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
                    register=str(item.get("register", "")).strip(),
                    question_kind=str(item.get("question_kind", "")).strip(),
                )
            )

    # Reframing variants exist only for eval families: they test surface robustness.
    eval_families = [family for family in families if family.split == "eval"]
    reframe_targets = eval_families[:reframing_families] if reframing_families else []
    by_family: dict[str, list[Prompt]] = {}
    for prompt in new_prompts + prompts:
        by_family.setdefault(prompt.family_id, []).append(prompt)

    reframe_jobs: list[tuple[Prompt, str, Family]] = []
    for position, family in enumerate(reframe_targets):
        family_prompts = by_family.get(family.family_id, [])
        if any(prompt.variant != "base" for prompt in family_prompts):
            # Already reframed on an earlier pass; a resume must not add a second variant.
            continue
        base_prompts = [p for p in family_prompts if p.variant == "base"]
        if not base_prompts or not reframing_variants:
            continue
        # Cycle deterministically so all five variants are exercised across a run.
        variant = reframing_variants[position % len(reframing_variants)]
        reframe_jobs.append((base_prompts[0], variant, family))

    async def run_reframe(
        base_prompt: Prompt, variant: str, family: Family
    ) -> tuple[Prompt, str, str]:
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
                        variant_instruction=REFRAMING_VARIANT_INSTRUCTIONS.get(variant, ""),
                        stance=family.asker_stance or "unchanged from the original",
                        forbidden_terms=forbidden,
                    ),
                },
            ],
            stage="generate.reframing",
            record_id=base_prompt.prompt_id,
        )
        return base_prompt, variant, extract_field(payload, "text", "prompt", "message").strip()

    if reframe_jobs:
        reframed = await gather_bounded(
            [run_reframe(prompt, variant, family) for prompt, variant, family in reframe_jobs]
        )
        max_overlap = float(settings.get("reframing_max_jaccard", 0.55))
        for result in reframed:
            if isinstance(result, Exception):
                logger.error("reframing failed: %s", result)
                continue
            base_prompt, variant, text = result
            if not text:
                continue
            overlap = jaccard(base_prompt.text, text)
            if overlap > max_overlap:
                # A variant that still shares most of its wording tests nothing.
                logger.warning(
                    "reframing %s as %s overlapped its base at %.2f (limit %.2f); dropped",
                    base_prompt.prompt_id,
                    variant,
                    overlap,
                    max_overlap,
                )
                continue
            new_prompts.append(
                Prompt(
                    prompt_id=short_id("pr", base_prompt.family_id, variant, text),
                    family_id=base_prompt.family_id,
                    variant=variant,
                    text=text,
                    case_type=base_prompt.case_type,
                    mode=base_prompt.mode,
                    register=base_prompt.register,
                    question_kind=base_prompt.question_kind,
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
    max_passage_chars = int(settings.get("max_passage_chars_responses", 8000))
    layer_ids = selected_layers(spec, config)
    forbidden = ", ".join(spec.forbidden_terms) or "(none)"
    family_by_id = {family.family_id: family for family in families}
    # A target that describes how it deliberates replaces the default instruction entirely.
    deliberation_shape = spec.deliberation_shape or DEFAULT_DELIBERATION_SHAPE
    archaic_examples = (
        render(ARCHAIC_EXAMPLES_BLOCK, examples="; ".join(spec.archaic_register_examples))
        if spec.archaic_register_examples
        else ""
    )
    hypothesis_text = {
        str(h.get("id")): " ".join(str(h.get("description", "")).split())
        for h in spec.divergence_hypotheses
        if h.get("id")
    }
    # A no-deliberation ablation slice: config decides what share keeps its deliberation.
    deliberation_fraction = float(settings.get("deliberation_fraction", 1.0))

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
                    deliberation_shape=deliberation_shape,
                    archaic_examples=archaic_examples,
                    hypothesis_block=(
                        render(
                            HYPOTHESIS_BLOCK,
                            hypothesis=hypothesis_text[family.divergence_hypothesis_id],
                        )
                        if family.divergence_hypothesis_id in hypothesis_text
                        else ""
                    ),
                    mode_instructions=mode_instructions(prompt.mode, forbidden, spec.name),
                    varied_fact_field=(
                        render(VARIED_FACT_FIELD, varied_fact=family.varied_fact)
                        if family.counterfactual_group_id and family.varied_fact
                        else ""
                    ),
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
        source_passages, passage_notes = _split_passage_citations(
            spec, payload.get("source_passages") or [], max_passages=3
        )
        keep_deliberation = _keeps_deliberation(prompt.prompt_id, deliberation_fraction)
        return Response(
            response_id=short_id("resp", prompt.prompt_id, generator.model),
            prompt_id=prompt.prompt_id,
            deliberation=(
                str(payload.get("deliberation", "")).strip() if keep_deliberation else ""
            ),
            answer=str(payload.get("answer", "")).strip(),
            hidden={
                "principles_applied": [str(p) for p in (payload.get("principles_applied") or [])],
                "source_passages": source_passages,
                "source_passage_notes": passage_notes,
                "intended_divergence_note": str(payload.get("intended_divergence_note", "")).strip(),
                "hypothesis_id": family.divergence_hypothesis_id,
            },
            generator_model=generator.model,
            usage=dict(response.usage or {}),
            revise_rounds=0,
            mode=prompt.mode,
            expected_actions=str(payload.get("expected_actions", "")).strip(),
            varied_fact_effect=str(payload.get("varied_fact_effect", "")).strip(),
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
