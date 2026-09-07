"""Coverage planning: how many families, of what kind, in which domain and split.

Pure functions over a TargetSpec and the config. No model calls and no file IO happen
here, so the whole coverage plan can be inspected and tested without spending anything.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from pipeline.config import RunConfig
from pipeline.records import Family
from pipeline.target import TargetSpec
from pipeline.validate import find_cue_hits


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
    for position in stratified_indices(slots, n_divergence, offset=0.0):
        slots[position].case_type_intent = "divergence"
    eval_positions = stratified_indices(slots, n_eval, offset=0.5)
    for position in eval_positions:
        slots[position].split = "eval"
    for position in stratified_indices(slots, n_reserved, exclude=set(eval_positions), offset=0.25):
        slots[position].split = "reserved"
    # Contrastive pairs must be written together, so both members sit in the same domain
    # and share a tradeoff: they are one situation with one fact changed. A domain with
    # fewer than two families cannot host a pair, so a very small pilot may produce none.
    assign_counterfactual_pairs(slots, round(n_families * counterfactual_share))
    for position in stratified_indices(slots, round(n_families * explicit_share), offset=0.4):
        slots[position].mode = "explicit"
    return slots


def assign_counterfactual_pairs(slots: list[FamilySlot], wanted_slots: int) -> int:
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


def stratified_indices(
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


def pair_counterfactual_slots(batch: list[FamilySlot]) -> dict[int, str]:
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


def align_counterfactual_groups(families: list[Family]) -> None:
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


def selected_layers(spec: TargetSpec, config: RunConfig) -> list[str]:
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


def avoided_topic_hit(text: str, avoid_words: list[str]) -> str:
    """Cheap keyword screen. Empty when the spec supplies no avoid_keywords."""
    if not avoid_words:
        return ""
    hits = find_cue_hits(text, avoid_words)
    return hits[0] if hits else ""
