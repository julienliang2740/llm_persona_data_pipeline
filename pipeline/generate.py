"""Generation stage: coverage plan -> families -> user prompts -> responses.

Idempotent on a run directory: families, prompts and responses that already exist
are kept, and only the missing ones are generated.
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
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
from pipeline.records import Family, Prompt, Response, short_id
from pipeline.validate import find_cue_hits
from pipeline.target import (
    TargetSpec,
    normalise_passage_ids,
    render_for_generator,
    render_key_passages,
)
from prompts import render
from prompts.generation import (
    COUNTERFACTUAL_INSTRUCTIONS,
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


@dataclass
class FamilySlot:
    """One planned family: which domain, which tradeoff, ordinary or divergence, which split."""

    index: int
    domain: str
    tradeoff_ids: list[str]
    case_type_intent: str
    split: str
    # Paired at plan time with another slot in the same domain, so both members are
    # generated in one call and can genuinely be the same situation.
    counterfactual_group: str | None = None
    mode: str = "neutral"  # neutral | explicit


def plan_families(spec: TargetSpec, settings: dict[str, Any], n_families: int) -> list[FamilySlot]:
    """Allocate families over domains by weight, then over tradeoffs, then over splits.

    Deterministic, so a re-run with the same sizes plans the same coverage.
    """
    weights = spec.domain_weights()
    exact = [(domain_id, weight * n_families) for domain_id, weight in weights]
    counts = {domain_id: int(value) for domain_id, value in exact}
    remainder = n_families - sum(counts.values())
    for domain_id, value in sorted(exact, key=lambda pair: pair[1] - int(pair[1]), reverse=True):
        if remainder <= 0:
            break
        counts[domain_id] += 1
        remainder -= 1
    # Interleave domains so that eval and divergence slots spread across all of them.
    ordered_domains: list[str] = []
    while sum(counts.values()) > 0:
        for domain_id, _ in weights:
            if counts.get(domain_id, 0) > 0:
                ordered_domains.append(domain_id)
                counts[domain_id] -= 1

    tradeoff_ids = [t["id"] for t in spec.tradeoffs] or [""]
    divergence_share = float(settings.get("divergence_fraction", 0.35))
    eval_share = float(settings.get("eval_family_fraction", 0.2))
    reserved_share = float(settings.get("reserved_family_fraction", 0.0))
    counterfactual_share = float(settings.get("counterfactual_fraction", 0.0))
    explicit_share = float(settings.get("explicit_fraction", 0.0))
    n_divergence = round(n_families * divergence_share)
    n_eval = max(1, round(n_families * eval_share)) if n_families > 1 else 0
    n_reserved = round(n_families * reserved_share)

    slots: list[FamilySlot] = []
    for index, domain_id in enumerate(ordered_domains):
        tradeoff = tradeoff_ids[index % len(tradeoff_ids)]
        slots.append(
            FamilySlot(
                index=index,
                domain=domain_id,
                tradeoff_ids=[tradeoff] if tradeoff else [],
                case_type_intent="ordinary",
                split="train",
            )
        )
    # Divergence, eval and reserved are each spread across domains rather than taken
    # from consecutive slots, so no domain ends up carrying all of one label.
    for position in _stratified_indices(slots, n_divergence, offset=0.0):
        slots[position].case_type_intent = "divergence"
    eval_positions = _stratified_indices(slots, n_eval, offset=0.5)
    for position in eval_positions:
        slots[position].split = "eval"
    for position in _stratified_indices(slots, n_reserved, exclude=set(eval_positions), offset=0.25):
        slots[position].split = "reserved"
    # Contrastive pairs must be written together, so both members sit in the same domain
    # and share a tradeoff: they are one situation with one fact changed. A domain with
    # fewer than two families cannot host a pair, so a very small pilot may produce none.
    _assign_counterfactual_pairs(slots, round(n_families * counterfactual_share))
    for position in _stratified_indices(slots, round(n_families * explicit_share), offset=0.4):
        slots[position].mode = "explicit"
    return slots


def _assign_counterfactual_pairs(slots: list[FamilySlot], wanted_slots: int) -> int:
    """Pair up slots inside each domain until `wanted_slots` are grouped. Returns pair count.

    Pairs are allocated to the largest domains first, spread evenly inside each domain,
    and the second member copies the first member's tradeoff so the pair really is one
    situation with one fact changed.
    """
    positions_by_domain: dict[str, list[int]] = {}
    for index, slot in enumerate(slots):
        positions_by_domain.setdefault(slot.domain, []).append(index)
    capacity = {domain: len(p) // 2 for domain, p in positions_by_domain.items()}
    allocation = {domain: 0 for domain in positions_by_domain}
    pairs_left = wanted_slots // 2
    while pairs_left > 0 and any(allocation[d] < capacity[d] for d in positions_by_domain):
        for domain in sorted(positions_by_domain, key=lambda d: -len(positions_by_domain[d])):
            if pairs_left <= 0:
                break
            if allocation[domain] < capacity[domain]:
                allocation[domain] += 1
                pairs_left -= 1

    pair_number = 0
    for domain in sorted(positions_by_domain):
        positions = positions_by_domain[domain]
        wanted_pairs = allocation[domain]
        if wanted_pairs <= 0:
            continue
        # Evenly spaced pair starts, so pairs are not all bunched at the front.
        step = len(positions) / wanted_pairs
        used: set[int] = set()
        for pair_index in range(wanted_pairs):
            start = int(pair_index * step)
            while start + 1 < len(positions) and (start in used or start + 1 in used):
                start += 1
            if start + 1 >= len(positions):
                continue
            used.update({start, start + 1})
            pair_number += 1
            label = f"g{pair_number}"
            first, second = slots[positions[start]], slots[positions[start + 1]]
            first.counterfactual_group = label
            second.counterfactual_group = label
            second.tradeoff_ids = list(first.tradeoff_ids)
    return pair_number


def _stratified_indices(
    slots: list[FamilySlot],
    count: int,
    exclude: set[int] | None = None,
    offset: float = 0.0,
) -> list[int]:
    """Pick `count` slot positions, allocated across domains in proportion to their size.

    Within a domain the picks are evenly spaced. Deterministic for a given input.
    """
    if count <= 0 or not slots:
        return []
    excluded = exclude or set()
    groups: dict[str, list[int]] = {}
    for index, slot in enumerate(slots):
        if index not in excluded:
            groups.setdefault(slot.domain, []).append(index)
    names = sorted(groups)
    available = sum(len(groups[name]) for name in names)
    if available == 0:
        return []
    count = min(count, available)
    exact = {name: len(groups[name]) * count / available for name in names}
    allocation = {name: int(value) for name, value in exact.items()}
    remaining = count - sum(allocation.values())
    for name in sorted(names, key=lambda n: exact[n] - int(exact[n]), reverse=True):
        if remaining <= 0:
            break
        if allocation[name] < len(groups[name]):
            allocation[name] += 1
            remaining -= 1

    picked: list[int] = []
    for name in names:
        wanted = allocation[name]
        members = groups[name]
        if wanted <= 0:
            continue
        step = len(members) / wanted
        chosen: list[int] = []
        for position in range(wanted):
            member = members[min(len(members) - 1, int(offset * step + position * step))]
            if member not in chosen:
                chosen.append(member)
        for member in members:  # fill any collisions from rounding
            if len(chosen) >= wanted:
                break
            if member not in chosen:
                chosen.append(member)
        picked.extend(chosen)
    return sorted(picked)


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
    layer_ids = _selected_layers(spec, config)
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
        pairs = _pair_counterfactual_slots(batch)
        lines = []
        for position, slot in enumerate(batch):
            group = pairs.get(position)
            note = f", contrastive group {group}" if group else ""
            explicit = ", EXPLICIT slice" if slot.mode == "explicit" else ""
            lines.append(
                f"- family {position + 1}: tradeoff_ids={slot.tradeoff_ids or ['(any)']}, "
                f"case_type_intent={slot.case_type_intent!r}{note}{explicit}"
            )
        payload, _ = await client.complete_json(
            generator,
            [
                {"role": "system", "content": GENERATOR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": render(
                        FAMILY_GENERATION_PROMPT,
                        target_spec=spec_text,
                        key_passages=passages_text,
                        n_families=len(batch),
                        domain=domain,
                        assignments="\n".join(lines),
                        counterfactual_instructions=(
                            COUNTERFACTUAL_INSTRUCTIONS if pairs else ""
                        ),
                        used_situations="\n".join(f"- {s}" for s in used_situations)
                        or "- (none yet)",
                    ),
                },
            ],
            stage="generate.families",
            record_id=f"{domain}:{batch[0].index}",
        )
        return extract_list(payload, "families", "family", "scenario_families", "items")

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
        pairs = _pair_counterfactual_slots(batch)
        for position, (slot, item) in enumerate(zip(batch, result)):
            seed = str(item.get("seed_situation", "")).strip()
            if not seed:
                continue
            family_id = short_id("fam", spec.target_id, domain, seed)
            if family_id in done_by_id:
                continue
            group = pairs.get(position)
            split, reason = slot.split, ""
            hit = _avoided_topic_hit(seed, avoid_words)
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
    _align_counterfactual_groups(families)
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


def mode_instructions(mode: str, forbidden_terms: str) -> str:
    """The cue block a response prompt gets: explicit slices may name the tradition."""
    if mode == "explicit":
        return EXPLICIT_MODE_RESPONSE_INSTRUCTIONS
    return render(NEUTRAL_MODE_RESPONSE_INSTRUCTIONS, forbidden_terms=forbidden_terms)


def _selected_layers(spec: TargetSpec, config: RunConfig) -> list[str]:
    """Config target_layers wins; otherwise the spec's own generate_by_default flags."""
    configured = config.generation.get("target_layers")
    if configured:
        known = {str(layer.get("id")) for layer in spec.layers}
        unknown = [name for name in configured if name not in known]
        if unknown:
            raise ValueError(
                f"config generation.target_layers names layers that target "
                f"'{spec.target_id}' does not define: {unknown}. Known: {sorted(known)}"
            )
        return [str(name) for name in configured]
    return spec.default_layer_ids()


def _pair_counterfactual_slots(batch: list[FamilySlot]) -> dict[int, str]:
    """Group labels for the slots in this batch, keeping only complete pairs.

    Pairing happens in the plan. A group whose partner fell into a different batch is
    dropped here, because a contrastive group of one has nothing to contrast with.
    """
    counts: Counter[str] = Counter(
        slot.counterfactual_group for slot in batch if slot.counterfactual_group
    )
    return {
        position: slot.counterfactual_group
        for position, slot in enumerate(batch)
        if slot.counterfactual_group and counts[slot.counterfactual_group] >= 2
    }


def _avoided_topic_hit(text: str, avoid_words: list[str]) -> str:
    """Cheap keyword screen. Empty when the spec supplies no avoid_keywords."""
    if not avoid_words:
        return ""
    hits = find_cue_hits(text, avoid_words)
    return hits[0] if hits else ""


def _align_counterfactual_groups(families: list[Family]) -> None:
    """Give every member of a counterfactual group the same split.

    The group is the unit of splitting, so a contrast cannot straddle train and eval.
    The strictest split any member carries wins: reserved beats eval beats train.
    """
    priority = {"train": 0, "eval": 1, "reserved": 2}
    groups: dict[str, list[Family]] = {}
    for family in families:
        if family.counterfactual_group_id:
            groups.setdefault(family.counterfactual_group_id, []).append(family)
    for members in groups.values():
        winner = max(members, key=lambda f: priority.get(f.split, 0))
        for family in members:
            if family.split != winner.split:
                family.split = winner.split
                if winner.reserved_reason and not family.reserved_reason:
                    family.reserved_reason = (
                        f"follows its counterfactual group: {winner.reserved_reason}"
                    )


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
                EXPLICIT_MODE_PROMPT_INSTRUCTIONS
                if mode == "explicit"
                else render(NEUTRAL_MODE_PROMPT_INSTRUCTIONS, forbidden_terms=forbidden)
            ),
        )
        payload, _ = await client.complete_json(
            generator,
            [
                {"role": "system", "content": GENERATOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            stage="generate.prompts",
            record_id=family.family_id,
        )
        return family, extract_list(payload, "prompts", "prompt", "messages", "items")

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
    layer_ids = _selected_layers(spec, config)
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
                    mode_instructions=mode_instructions(prompt.mode, forbidden),
                ),
            },
        ]
        payload, response = await client.complete_json(
            generator, messages, stage="generate.responses", record_id=prompt.prompt_id
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
                            mode_instructions=mode_instructions(prompt.mode, forbidden),
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
