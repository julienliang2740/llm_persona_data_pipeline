"""Coverage planning: how many families, of what kind, in which domain and split.

Pure functions over a TargetSpec and the config. No model calls and no file IO happen
here, so the whole coverage plan can be inspected and tested without spending anything.

The plan is built by construction rather than checked afterwards. Round 1 lost
counterfactual pairs to a count-based retry, drew 37.5% eval against a configured 25%,
and never touched a single unresolved tradeoff in two of four targets. Each of those is
now either impossible to express or a hard error before any model is called.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from pipeline.config import RunConfig
from pipeline.institutions import INSTITUTIONS, INSTITUTIONS_BY_SECTOR
from pipeline.records import (
    ASKER_STANCE,
    ASKER_STANCE_MIX,
    ROLE_TYPE_MIX,
    HARM_SEVERITY,
    PUBLIC_OR_PRIVATE,
    ROLE_TYPE,
    URGENCY,
    Family,
)
from pipeline.target import TargetSpec
from pipeline.validate import find_cue_hits


class PlanError(ValueError):
    """The coverage plan cannot be built as configured. Raised before any model call."""


@dataclass
class FamilySlot:
    """One planned family. Everything the generator is told to vary is decided here."""

    slot_index: int
    domain: str
    tradeoff_ids: list[str] = field(default_factory=list)
    case_type_intent: str = "ordinary"
    split: str = "train"
    counterfactual_group: str | None = None
    mode: str = "neutral"
    divergence_hypothesis_id: str = ""
    unresolved_choice_id: str = ""
    # Filled in by A3 structural diversity; empty until then.
    asker_stance: str = ""
    institution: str = ""
    #: For a slot in a counterfactual group, the one feature that differs from its partner.
    varied_axis: str = ""
    role_type: str = ""
    harm_severity: str = ""
    urgency: str = ""
    public_or_private: str = ""

    @property
    def index(self) -> int:
        """Backwards-compatible alias: the slot index is the slot's identity."""
        return self.slot_index

    @property
    def structural_key(self) -> str:
        tradeoff = self.tradeoff_ids[0] if self.tradeoff_ids else ""
        return "|".join([tradeoff, self.role_type, self.harm_severity, self.domain])


def plan_families(
    spec: TargetSpec, settings: dict[str, Any], n_families: int
) -> list[FamilySlot]:
    """Build the whole coverage plan. Deterministic for a given spec, settings and size."""
    if n_families <= 0:
        raise PlanError(f"n_families must be positive, got {n_families}.")

    slots = [
        FamilySlot(slot_index=index, domain=domain)
        for index, domain in enumerate(_ordered_domains(spec, n_families))
    ]
    # Pairs are formed first and everything else is decided per unit, where a pair is one
    # unit. Assigning tradeoffs first and pairing afterwards let the copy-to-partner step
    # overwrite coverage: theravada went from 7 unresolved tradeoffs covered to 2.
    assign_counterfactual_pairs(
        slots, round(n_families * float(settings.get("counterfactual_fraction", 0.0)))
    )
    units = plan_units(slots)
    # Divergence is counted in families, not units: a pair contributes two.
    assign_divergence_intent(slots, units, float(settings.get("divergence_fraction", 0.35)))
    representatives = [slots[unit[0]] for unit in units]
    assign_tradeoffs(spec, representatives, settings)
    assign_modes(representatives, float(settings.get("explicit_fraction", 0.0)))
    assign_situation_features(representatives)
    assign_institutions(representatives, seed=spec.target_id)
    _propagate_within_groups(slots, units)
    assign_splits(slots, settings)

    problems = check_plan(spec, slots, settings)
    fatal = [problem for problem in problems if problem.startswith("ERROR")]
    if fatal:
        raise PlanError(
            f"Coverage plan for '{spec.target_id}' at n={n_families} is not usable:\n  - "
            + "\n  - ".join(fatal)
        )
    return slots


# -- domains ----------------------------------------------------------------


def _ordered_domains(spec: TargetSpec, n_families: int) -> list[str]:
    """Allocate families over domains by weight, interleaved so labels spread evenly."""
    weights = spec.domain_weights()
    exact = [(domain_id, weight * n_families) for domain_id, weight in weights]
    counts = {domain_id: int(value) for domain_id, value in exact}
    remainder = n_families - sum(counts.values())
    for domain_id, value in sorted(exact, key=lambda pair: pair[1] - int(pair[1]), reverse=True):
        if remainder <= 0:
            break
        counts[domain_id] += 1
        remainder -= 1
    ordered: list[str] = []
    while sum(counts.values()) > 0:
        for domain_id, _ in weights:
            if counts.get(domain_id, 0) > 0:
                ordered.append(domain_id)
                counts[domain_id] -= 1
    return ordered


# -- case type and coverage floors -------------------------------------------


def assign_divergence_intent(
    slots: list[FamilySlot], units: list[tuple[int, ...]], divergence_fraction: float
) -> None:
    """Mark whole units as divergence cases until the family target is reached."""
    wanted = round(len(slots) * divergence_fraction)
    # Offset 0: the eval draw deliberately uses a different one. Sharing it made 7 of 8
    # eval families divergence-intent against a configured half.
    for unit in _draw_units(slots, units, wanted, skip=set(), offset=0):
        for slot_index in unit:
            slots[slot_index].case_type_intent = "divergence"


def assign_tradeoffs(spec: TargetSpec, slots: list[FamilySlot], settings: dict[str, Any]) -> None:
    """Give every slot a tradeoff, an unresolved choice where relevant, and a hypothesis.

    Coverage floors first: no tradeoff gets a second family while another is uncovered,
    and unresolved tradeoffs are covered before resolved ones. Round 1 assigned
    `tradeoff_ids[index % len(tradeoff_ids)]`, which at n=8 could only ever reach the
    first eight tradeoffs in YAML order and touched zero unresolved ones in two targets.
    """
    unresolved = [t["id"] for t in spec.tradeoffs if t.get("unresolved")]
    resolved = [t["id"] for t in spec.tradeoffs if not t.get("unresolved")]
    if not unresolved and not resolved:
        return

    share = float(settings.get("unresolved_tradeoff_fraction", 0.25))
    wanted_unresolved = round(len(slots) * share)
    if unresolved:
        # Raise the allocation when needed to reach every unresolved tradeoff once,
        # but never let hedging cases take more than half the run.
        wanted_unresolved = max(wanted_unresolved, min(len(unresolved), len(slots) // 2))
    wanted_unresolved = min(wanted_unresolved, len(slots) if not resolved else len(slots) - 1)
    unresolved_positions = set(stratified_indices(slots, wanted_unresolved, offset=0.3))

    unresolved_cycle = _coverage_cycle(unresolved)
    resolved_cycle = _coverage_cycle(resolved)
    for slot in slots:
        pool = unresolved_cycle if (slot.slot_index in unresolved_positions and unresolved) else resolved_cycle
        if not pool.pool:
            pool = unresolved_cycle if unresolved_cycle.pool else resolved_cycle
        slot.tradeoff_ids = [pool.take()]

    _assign_unresolved_choices(spec, slots)
    assign_divergence_hypotheses(spec, slots)


class _coverage_cycle:
    """Round-robin that exhausts every item once before repeating any of them."""

    def __init__(self, pool: list[str]) -> None:
        self.pool = list(pool)
        self._remaining = list(pool)

    def take(self) -> str:
        if not self.pool:
            return ""
        if not self._remaining:
            self._remaining = list(self.pool)
        return self._remaining.pop(0)


def _assign_unresolved_choices(spec: TargetSpec, slots: list[FamilySlot]) -> None:
    """Cover every `mark_ambiguous` interpretation choice before repeating one."""
    choices = [
        str(choice.get("id"))
        for choice in spec.unresolved_choices
        if str(choice.get("generation_policy", "")).strip() == "mark_ambiguous"
    ]
    if not choices:
        return
    cycle = _coverage_cycle(choices)
    # Attach them to the slots already carrying an unresolved tradeoff where possible,
    # so the hedging cases cluster rather than diluting every family.
    unresolved_ids = {t["id"] for t in spec.tradeoffs if t.get("unresolved")}
    carriers = [s for s in slots if set(s.tradeoff_ids) & unresolved_ids] or slots
    for position in stratified_indices(carriers, min(len(choices), len(carriers))):
        carriers[position].unresolved_choice_id = cycle.take()


def assign_divergence_hypotheses(spec: TargetSpec, slots: list[FamilySlot]) -> None:
    """Every divergence-intent slot names the hypothesis it is written to instantiate.

    Round 1 had no such field, and hand-mapping afterwards found 2 of 9 to 3 of 11
    hypotheses exercised per target. Round-robin here makes coverage a plan property.
    """
    hypotheses = [str(item.get("id")) for item in spec.divergence_hypotheses if item.get("id")]
    if not hypotheses:
        return
    cycle = _coverage_cycle(hypotheses)
    for slot in slots:
        if slot.case_type_intent == "divergence":
            slot.divergence_hypothesis_id = cycle.take()


# -- counterfactual pairs ----------------------------------------------------


def assign_counterfactual_pairs(slots: list[FamilySlot], wanted_slots: int) -> int:
    """Pair slots inside each domain. Runs BEFORE the split is drawn.

    Both members share domain, tradeoff, hypothesis and case type: a contrastive pair is
    one situation with one fact changed, so everything except that fact must match.
    """
    if wanted_slots < 2:
        return 0
    positions_by_domain: dict[str, list[int]] = {}
    for slot in slots:
        positions_by_domain.setdefault(slot.domain, []).append(slot.slot_index)
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
            slots[positions[start]].counterfactual_group = label
            slots[positions[start + 1]].counterfactual_group = label
    return pair_number


def plan_units(slots: list[FamilySlot]) -> list[tuple[int, ...]]:
    """Slot indices grouped into planning units: a counterfactual pair counts as one."""
    groups = counterfactual_groups(slots)
    units = [tuple(sorted(members)) for members in groups.values()]
    units += [(slot.slot_index,) for slot in slots if not slot.counterfactual_group]
    return sorted(units)


#: The axes a contrastive pair may vary, cycled across groups. Round 2 hard-coded harm
#: severity for every pair, and only one of the four flipped the recommended action: a
#: minor and a career-affecting condition drew the same advice. Intensity is the axis a
#: target is least likely to pivot on.
VARIED_AXES = ("harm_severity", "role_type", "public_or_private", "urgency", "asker_stance")


def _propagate_within_groups(slots: list[FamilySlot], units: list[tuple[int, ...]]) -> None:
    """Copy the unit's decisions onto the partner slot, varying exactly one axis.

    Both members share the tradeoff, the case type, the hypothesis, the mode and the
    setting. Which single axis differs is cycled across groups so a run does not test the
    same kind of contrast every time.
    """
    group_number = 0
    for unit in units:
        if len(unit) < 2:
            continue
        first = slots[unit[0]]
        axis = VARIED_AXES[group_number % len(VARIED_AXES)]
        group_number += 1
        first.varied_axis = axis
        for slot_index in unit[1:]:
            partner = slots[slot_index]
            partner.tradeoff_ids = list(first.tradeoff_ids)
            partner.case_type_intent = first.case_type_intent
            partner.divergence_hypothesis_id = first.divergence_hypothesis_id
            partner.unresolved_choice_id = first.unresolved_choice_id
            partner.mode = first.mode
            partner.varied_axis = axis
            # Everything is held constant except the one axis this group varies.
            partner.institution = first.institution
            partner.role_type = first.role_type
            partner.asker_stance = first.asker_stance
            partner.public_or_private = first.public_or_private
            partner.urgency = first.urgency
            partner.harm_severity = first.harm_severity
            setattr(partner, axis, _contrasting_value(axis, getattr(first, axis)))


def assign_situation_features(slots: list[FamilySlot]) -> None:
    """Plan the structural features rather than letting the generator pick them.

    Round 1 recorded these as free text and got one dominant value per axis, plus four
    pairs of families in one domain that were the same situation twice. The plan-time rule
    is that no two families in a domain share (tradeoff, role_type, harm_severity).
    """
    stance_cycle = _proportional_cycle(ASKER_STANCE_MIX, len(slots))
    # role_type gets its own enforced mix rather than being the outer loop of a
    # (role, harm) product. As a product it needed four slots in one domain before the
    # role advanced, and since almost every domain held one family, every family in every
    # target came out no_authority; holds_authority and institution never occurred at all.
    role_cycle = _proportional_cycle(ROLE_TYPE_MIX, len(slots))
    for position, slot in enumerate(slots):
        slot.asker_stance = stance_cycle[position]
        slot.role_type = role_cycle[position]
        slot.urgency = URGENCY[position % len(URGENCY)]
        slot.public_or_private = PUBLIC_OR_PRIVATE[(position // 2) % len(PUBLIC_OR_PRIVATE)]

    # harm_severity is then chosen per domain to keep the structural key unique, with the
    # role already fixed; a domain larger than the key space repeats only once it must.
    by_domain: dict[str, list[FamilySlot]] = {}
    for slot in slots:
        by_domain.setdefault(slot.domain, []).append(slot)
    for domain_slots in by_domain.values():
        used: set[tuple[str, str, str]] = set()
        for offset, slot in enumerate(domain_slots):
            tradeoff = slot.tradeoff_ids[0] if slot.tradeoff_ids else ""
            for step in range(len(HARM_SEVERITY)):
                harm = HARM_SEVERITY[(offset + step) % len(HARM_SEVERITY)]
                if (tradeoff, slot.role_type, harm) not in used:
                    break
            used.add((tradeoff, slot.role_type, harm))
            slot.harm_severity = harm


def _proportional_cycle(mix: dict[str, float], count: int) -> list[str]:
    """A list of `count` labels matching `mix` as closely as whole numbers allow.

    Interleaved rather than blocked, so a truncated run still holds the mixture.
    """
    if count <= 0:
        return []
    exact = {name: share * count for name, share in mix.items()}
    allocation = {name: int(value) for name, value in exact.items()}
    remaining = count - sum(allocation.values())
    for name in sorted(exact, key=lambda n: exact[n] - int(exact[n]), reverse=True):
        if remaining <= 0:
            break
        allocation[name] += 1
        remaining -= 1
    pools = {name: allocation[name] for name in sorted(mix, key=lambda n: -mix[n])}
    out: list[str] = []
    while len(out) < count:
        for name in list(pools):
            if pools[name] > 0:
                out.append(name)
                pools[name] -= 1
                if len(out) >= count:
                    break
    return out


def assign_institutions(slots: list[FamilySlot], seed: str = "") -> None:
    """One institution per slot, sectors first and offset per target.

    Walking a sector-ordered flat list from index 0 gave every target the same first seven
    institutions: six healthcare plus one college, so 28 of 32 round-2 families were
    clinical and eight of nine sectors were never reached. Sectors are now round-robined
    before institutions within them, and the starting point is derived from the target id,
    so a target's families span as many sectors as it has families and two targets do not
    line up slot for slot.
    """
    if not INSTITUTIONS:
        return
    sectors = sorted(INSTITUTIONS_BY_SECTOR)
    offset = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16) if seed else 0
    for position, slot in enumerate(slots):
        sector = sectors[(offset + position) % len(sectors)]
        options = INSTITUTIONS_BY_SECTOR[sector]
        # Advance within the sector once the walk comes round to it again.
        within = (offset // len(sectors) + position // len(sectors)) % len(options)
        slot.institution = options[within]


def counterfactual_groups(slots: list[FamilySlot]) -> dict[str, list[int]]:
    groups: dict[str, list[int]] = {}
    for slot in slots:
        if slot.counterfactual_group:
            groups.setdefault(slot.counterfactual_group, []).append(slot.slot_index)
    return groups


# -- splits ------------------------------------------------------------------


def assign_splits(slots: list[FamilySlot], settings: dict[str, Any]) -> None:
    """Draw eval and reserved over whole units, where a counterfactual pair is one unit.

    Drawing over slots let `align_counterfactual_groups` promote a pair's partner into
    eval afterwards, which is how a configured 25% became an actual 37.5%. At most half
    the groups may go to eval, so the contrast is exercised on both sides of the split.

    Held-out tradeoffs are placed first and count towards the eval target rather than
    adding to it, so holding one out does not quietly enlarge the eval set.
    """
    units = plan_units(slots)
    group_units = [unit for unit in units if len(unit) > 1]
    # Round up, so with exactly one group `1 // 2 == 0` no longer makes the whole list
    # ineligible. Round 2 put every pair in train in all four targets, and varied_fact was
    # empty on all 14 eval rows as a result.
    eval_ineligible = set(group_units[math.ceil(len(group_units) / 2) :])

    wanted_eval = round(len(slots) * float(settings.get("eval_family_fraction", 0.0)))
    if len(slots) > 1:
        wanted_eval = max(1, wanted_eval)
    wanted_reserved = round(len(slots) * float(settings.get("reserved_family_fraction", 0.0)))

    held_out = hold_out_tradeoffs(slots, int(settings.get("held_out_tradeoffs", 0)))
    held_units = {
        unit
        for unit in units
        if any(set(slots[index].tradeoff_ids) & held_out for index in unit)
    }
    held_families = sum(len(unit) for unit in held_units)
    for unit in held_units:
        for slot_index in unit:
            slots[slot_index].split = "eval"

    remaining_eval = max(0, wanted_eval - held_families)
    # Draw eval separately from the divergence units and the ordinary ones, in the
    # configured proportion. A single draw over the same round-robin the divergence draw
    # used put 7 of 8 eval families on divergence against a configured half; a different
    # offset alone does not fix it, because half the units carry the label either way.
    divergence_fraction = float(settings.get("divergence_fraction", 0.35))
    held_divergence = sum(
        1
        for unit in held_units
        for index in unit
        if slots[index].case_type_intent == "divergence"
    )
    wanted_eval_divergence = max(
        0, round(wanted_eval * divergence_fraction) - held_divergence
    )
    is_divergence = lambda unit: slots[unit[0]].case_type_intent == "divergence"
    divergence_units = [unit for unit in units if is_divergence(unit)]
    ordinary_units = [unit for unit in units if not is_divergence(unit)]
    skip = eval_ineligible | held_units
    chosen_eval = _draw_units(
        slots, divergence_units, wanted_eval_divergence, skip=skip, offset=2
    )
    chosen_eval += _draw_units(
        slots,
        ordinary_units,
        remaining_eval - sum(len(unit) for unit in chosen_eval),
        skip=skip,
        offset=1,
    )
    for unit in chosen_eval:
        for slot_index in unit:
            slots[slot_index].split = "eval"

    chosen_reserved = _draw_units(
        slots,
        units,
        wanted_reserved,
        skip=eval_ineligible | held_units | set(chosen_eval),
        offset=4,
    )
    for unit in chosen_reserved:
        for slot_index in unit:
            slots[slot_index].split = "reserved"


def hold_out_tradeoffs(slots: list[FamilySlot], count: int) -> set[str]:
    """Choose tradeoffs whose every family goes to eval, for a novel-transfer slice.

    Picks the least-used tradeoffs, so holding one out costs the training set least.
    """
    if count <= 0:
        return set()
    usage = Counter(tid for slot in slots for tid in slot.tradeoff_ids)
    if len(usage) <= count:
        return set()
    ordered = sorted(usage, key=lambda tid: (usage[tid], tid))
    return set(ordered[:count])


def _draw_units(
    slots: list[FamilySlot],
    units: list[tuple[int, ...]],
    wanted_families: int,
    skip: set[tuple[int, ...]],
    offset: int = 0,
) -> list[tuple[int, ...]]:
    """Pick whole units until `wanted_families` slots are covered, spread across domains.

    Round-robins over domains so the eval set is not drawn from one corner of the target;
    a unit is never split, so a contrastive pair lands whole on one side.
    """
    if wanted_families <= 0:
        return []
    available = [unit for unit in units if unit not in skip]
    if not available:
        return []
    by_domain: dict[str, list[tuple[int, ...]]] = {}
    for unit in available:
        by_domain.setdefault(slots[unit[0]].domain, []).append(unit)
    for pool in by_domain.values():
        pool.sort()
    cursors = {domain: offset % len(pool) for domain, pool in by_domain.items()}
    order = sorted(by_domain, key=lambda domain: (-len(by_domain[domain]), domain))

    chosen: list[tuple[int, ...]] = []
    taken: set[tuple[int, ...]] = set()
    covered = 0
    while covered < wanted_families:
        progressed = False
        for domain in order:
            if covered >= wanted_families:
                break
            pool = by_domain[domain]
            for _ in range(len(pool)):
                unit = pool[cursors[domain] % len(pool)]
                cursors[domain] += 1
                if unit in taken:
                    continue
                if covered + len(unit) > wanted_families and covered > 0:
                    continue
                taken.add(unit)
                chosen.append(unit)
                covered += len(unit)
                progressed = True
                break
        if not progressed:
            break
    return chosen


def assign_modes(slots: list[FamilySlot], explicit_fraction: float) -> None:
    for position in stratified_indices(slots, round(len(slots) * explicit_fraction), offset=0.4):
        slots[position].mode = "explicit"


# -- shared helpers -----------------------------------------------------------


def stratified_indices(
    slots: list[FamilySlot],
    count: int,
    exclude: set[int] | None = None,
    offset: float = 0.0,
) -> list[int]:
    """Pick `count` positions in `slots`, allocated across domains by domain size."""
    if count <= 0 or not slots:
        return []
    excluded = exclude or set()
    groups: dict[str, list[int]] = {}
    for position, slot in enumerate(slots):
        if position not in excluded:
            groups.setdefault(slot.domain, []).append(position)
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
        for member in members:
            if len(chosen) >= wanted:
                break
            if member not in chosen:
                chosen.append(member)
        picked.extend(chosen)
    return sorted(picked)


def pair_counterfactual_slots(batch: list[FamilySlot]) -> dict[int, str]:
    """Group labels for the slots in one generation batch, keeping only complete pairs."""
    counts: Counter[str] = Counter(
        slot.counterfactual_group for slot in batch if slot.counterfactual_group
    )
    return {
        position: slot.counterfactual_group
        for position, slot in enumerate(batch)
        if slot.counterfactual_group and counts[slot.counterfactual_group] >= 2
    }


def align_counterfactual_groups(families: list[Family]) -> None:
    """Keep a group on one side of the split.

    The plan already places groups whole, so this only repairs a family that arrived from
    an older run or was reserved by the avoided-topic screen after generation.
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


#: The two ends of each axis a pair can be contrasted along.
_AXIS_VALUES = {
    "harm_severity": HARM_SEVERITY,
    "role_type": ROLE_TYPE,
    "public_or_private": PUBLIC_OR_PRIVATE,
    "urgency": URGENCY,
    "asker_stance": ASKER_STANCE,
}


def _contrasting_value(axis: str, value: str) -> str:
    """The far end of `axis` from `value`, so the pair differs as widely as the axis allows."""
    options = _AXIS_VALUES.get(axis, ())
    if not options:
        return value
    if value == options[0]:
        return options[-1]
    return options[0]


def selected_layers(spec: TargetSpec, config: RunConfig) -> list[str]:
    """Config target_layers wins; otherwise the spec's own generate_by_default flags."""
    configured = config.generation.get("target_layers")
    if configured:
        known = {str(layer.get("id")) for layer in spec.layers}
        unknown = [name for name in configured if name not in known]
        if unknown:
            raise PlanError(
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


# -- plan validation ----------------------------------------------------------


def _same_group(slots: list[FamilySlot], indices: list[int]) -> bool:
    """Two members of one contrastive pair share a key by design."""
    labels = {slots[index].counterfactual_group for index in indices}
    return len(labels) == 1 and None not in labels


def check_plan(
    spec: TargetSpec, slots: list[FamilySlot], settings: dict[str, Any]
) -> list[str]:
    """Every plan invariant, as ERROR (refuse to run) or WARN (log and continue)."""
    problems: list[str] = []
    total = len(slots)

    eval_count = sum(1 for slot in slots if slot.split == "eval")
    wanted_eval = round(total * float(settings.get("eval_family_fraction", 0.0)))
    if total > 1:
        wanted_eval = max(1, wanted_eval)
    held_out = hold_out_tradeoffs(slots, int(settings.get("held_out_tradeoffs", 0)))
    held_families = sum(1 for slot in slots if set(slot.tradeoff_ids) & held_out)
    if held_families > wanted_eval:
        problems.append(
            f"WARN held-out tradeoffs account for {held_families} families, more than the "
            f"eval target of {wanted_eval}; the eval set is larger than configured."
        )
    elif abs(eval_count - wanted_eval) > 1:
        problems.append(
            f"ERROR eval split is {eval_count} of {total} families, but "
            f"eval_family_fraction asks for {wanted_eval} (tolerance is one family)."
        )

    eval_slots = [slot for slot in slots if slot.split == "eval"]
    if eval_slots:
        eval_divergence = sum(1 for slot in eval_slots if slot.case_type_intent == "divergence")
        wanted_divergence = round(len(eval_slots) * float(settings.get("divergence_fraction", 0.35)))
        if abs(eval_divergence - wanted_divergence) > 1:
            problems.append(
                f"WARN eval holds {eval_divergence} divergence of {len(eval_slots)} families, "
                f"but divergence_fraction asks for about {wanted_divergence}; the eval set "
                f"does not reflect the configured mix."
            )

    for label, members in counterfactual_groups(slots).items():
        splits = {slots[i].split for i in members}
        if len(members) != 2:
            problems.append(
                f"ERROR counterfactual group {label} has {len(members)} members; a "
                f"contrast needs exactly two."
            )
        if len(splits) > 1:
            problems.append(
                f"ERROR counterfactual group {label} straddles splits {sorted(splits)}."
            )
        domains = {slots[i].domain for i in members}
        if len(domains) > 1:
            problems.append(
                f"ERROR counterfactual group {label} spans domains {sorted(domains)}; a "
                f"contrast must hold everything but one fact constant."
            )

    groups = counterfactual_groups(slots)
    if groups:
        in_train = sum(
            1 for members in groups.values() if slots[members[0]].split == "train"
        )
        if in_train == 0 and len(groups) > 1:
            problems.append(
                f"WARN all {len(groups)} counterfactual groups are outside train; the "
                f"contrast is never seen during training."
            )

    for tradeoff_id in sorted(held_out):
        stray = [
            slot.slot_index
            for slot in slots
            if tradeoff_id in slot.tradeoff_ids and slot.split != "eval"
        ]
        if stray:
            problems.append(
                f"ERROR held-out tradeoff {tradeoff_id} still has training families at "
                f"slots {stray}."
            )

    seen_keys: dict[str, list[int]] = {}
    for slot in slots:
        if slot.role_type or slot.harm_severity:
            seen_keys.setdefault(slot.structural_key, []).append(slot.slot_index)
    repeats = {
        key: indices
        for key, indices in seen_keys.items()
        if len(indices) > 1 and not _same_group(slots, indices)
    }
    if repeats:
        problems.append(
            f"WARN {len(repeats)} structural key(s) repeat inside a domain, so those "
            f"families risk being the same situation twice: "
            + "; ".join(f"{key} -> slots {indices}" for key, indices in list(repeats.items())[:4])
        )

    if {slot.slot_index for slot in slots} != set(range(total)):
        problems.append("ERROR slot indices are not a contiguous range; retries rely on them.")

    for slot in slots:
        if slot.case_type_intent == "divergence" and spec.divergence_hypotheses:
            if not slot.divergence_hypothesis_id:
                problems.append(
                    f"ERROR slot {slot.slot_index} is a divergence case with no "
                    f"divergence_hypothesis_id."
                )

    # Coverage floors are scale-dependent: the configured floor is per 100 families, so a
    # run smaller than that cannot be expected to reach every item.
    per_hundred = float(settings.get("hypothesis_coverage_floor", 1.0))
    floor_scale = total * per_hundred / 100.0 >= 1.0 and total >= 100
    unresolved = [t["id"] for t in spec.tradeoffs if t.get("unresolved")]
    covered_tradeoffs = {tid for slot in slots for tid in slot.tradeoff_ids}
    missing_unresolved = [tid for tid in unresolved if tid not in covered_tradeoffs]
    if missing_unresolved:
        severity = "ERROR" if floor_scale else "WARN"
        problems.append(
            f"{severity} {len(missing_unresolved)} unresolved tradeoff(s) get no family "
            f"at n={total}: {missing_unresolved}"
        )
    hypotheses = [str(h.get("id")) for h in spec.divergence_hypotheses if h.get("id")]
    covered_hypotheses = {slot.divergence_hypothesis_id for slot in slots if slot.divergence_hypothesis_id}
    missing_hypotheses = [h for h in hypotheses if h not in covered_hypotheses]
    wanted_per_hypothesis = max(1, round(total * per_hundred / 100.0))
    thin = sorted(
        hypothesis
        for hypothesis, count in Counter(
            slot.divergence_hypothesis_id for slot in slots if slot.divergence_hypothesis_id
        ).items()
        if count < wanted_per_hypothesis
    )
    if thin and floor_scale:
        problems.append(
            f"WARN {len(thin)} hypothes(es) get fewer than the configured floor of "
            f"{wanted_per_hypothesis} families per {total}: {thin[:6]}"
        )
    if missing_hypotheses:
        severity = "ERROR" if floor_scale else "WARN"
        problems.append(
            f"{severity} {len(missing_hypotheses)} divergence hypothes(es) get no family "
            f"at n={total}: {missing_hypotheses[:6]}"
        )
    return problems
