"""Plan invariants on the four real specs.

Each of these encodes a round-1 failure that reached the artifacts. They run over every
committed target, because three of the four failures showed up in only some traditions.
"""

from __future__ import annotations

from collections import Counter

import pytest

from pipeline.plan import (
    PlanError,
    check_plan,
    counterfactual_groups,
    plan_families,
    plan_units,
)
from tests.conftest import PLAN_SETTINGS

SIZES = (8, 32, 240)


def plans(real_specs, sizes=SIZES, **overrides):
    settings = dict(PLAN_SETTINGS, **overrides)
    for target_id, spec in sorted(real_specs.items()):
        for size in sizes:
            yield target_id, spec, size, plan_families(spec, settings, size)


# -- A1: split and pairing by construction -----------------------------------


def test_eval_fraction_is_exact_within_one_family(real_specs):
    """Round 1 drew 37.5% eval against a configured 25% in every run."""
    for target_id, _spec, size, slots in plans(real_specs):
        eval_count = sum(1 for slot in slots if slot.split == "eval")
        wanted = max(1, round(size * PLAN_SETTINGS["eval_family_fraction"]))
        assert abs(eval_count - wanted) <= 1, f"{target_id} n={size}: {eval_count} vs {wanted}"


def test_a_bad_eval_fraction_is_a_plan_error(real_specs, monkeypatch):
    """The check is a hard error, not a warning: a wrong split invalidates the run."""
    import pipeline.plan as plan_module

    spec = real_specs["catholic"]
    monkeypatch.setattr(plan_module, "assign_splits", lambda slots, settings: None)
    with pytest.raises(PlanError) as error:
        plan_families(spec, PLAN_SETTINGS, 32)
    assert "eval split" in str(error.value)


def test_counterfactual_groups_land_whole_on_one_side(real_specs):
    for target_id, _spec, size, slots in plans(real_specs):
        for label, members in counterfactual_groups(slots).items():
            splits = {slots[index].split for index in members}
            assert len(splits) == 1, f"{target_id} n={size} group {label} straddles {splits}"


def test_counterfactual_groups_have_exactly_two_members_in_one_domain(real_specs):
    for target_id, _spec, size, slots in plans(real_specs):
        for label, members in counterfactual_groups(slots).items():
            assert len(members) == 2, f"{target_id} n={size} group {label}"
            assert len({slots[i].domain for i in members}) == 1


def test_both_members_of_a_pair_share_everything_but_the_varied_fact(real_specs):
    for target_id, _spec, size, slots in plans(real_specs):
        for members in counterfactual_groups(slots).values():
            first, second = (slots[i] for i in members)
            assert first.tradeoff_ids == second.tradeoff_ids, target_id
            assert first.case_type_intent == second.case_type_intent
            assert first.divergence_hypothesis_id == second.divergence_hypothesis_id
            assert first.mode == second.mode


def test_at_least_half_the_groups_are_in_train(real_specs):
    """Round 1 put both surviving groups wholly in eval, so training never saw a contrast."""
    for target_id, _spec, size, slots in plans(real_specs, sizes=(32, 240)):
        groups = counterfactual_groups(slots)
        in_train = sum(1 for members in groups.values() if slots[members[0]].split == "train")
        assert in_train >= len(groups) // 2, f"{target_id} n={size}: {in_train}/{len(groups)}"


def test_slot_indices_are_a_contiguous_range(real_specs):
    """Retries address slots by index, so the indices must be complete and unique."""
    for _target_id, _spec, size, slots in plans(real_specs):
        assert [slot.slot_index for slot in slots] == list(range(size))


def test_units_partition_the_slots(real_specs):
    for _target_id, _spec, size, slots in plans(real_specs):
        covered = [index for unit in plan_units(slots) for index in unit]
        assert sorted(covered) == list(range(size))


def test_the_plan_is_deterministic(real_specs):
    spec = real_specs["confucian"]
    first = plan_families(spec, PLAN_SETTINGS, 32)
    second = plan_families(spec, PLAN_SETTINGS, 32)
    signature = lambda slots: [
        (s.slot_index, s.domain, tuple(s.tradeoff_ids), s.case_type_intent, s.split,
         s.counterfactual_group, s.divergence_hypothesis_id) for s in slots
    ]
    assert signature(first) == signature(second)


def test_zero_families_is_refused(real_specs):
    with pytest.raises(PlanError):
        plan_families(real_specs["catholic"], PLAN_SETTINGS, 0)


# -- A2: coverage floors ------------------------------------------------------


def test_every_unresolved_tradeoff_is_covered_at_scale(real_specs):
    """Two of four targets covered zero unresolved tradeoffs in round 1."""
    for target_id, spec, size, slots in plans(real_specs, sizes=(240,)):
        unresolved = {t["id"] for t in spec.tradeoffs if t.get("unresolved")}
        covered = {tid for slot in slots for tid in slot.tradeoff_ids}
        assert unresolved <= covered, f"{target_id}: missing {sorted(unresolved - covered)}"


def test_every_divergence_hypothesis_is_covered_at_scale(real_specs):
    for target_id, spec, size, slots in plans(real_specs, sizes=(240,)):
        hypotheses = {str(h["id"]) for h in spec.divergence_hypotheses if h.get("id")}
        covered = {slot.divergence_hypothesis_id for slot in slots}
        assert hypotheses <= covered, f"{target_id}: missing {sorted(hypotheses - covered)}"


def test_coverage_only_improves_with_size(real_specs):
    """Pairing used to overwrite tradeoffs, so n=32 covered fewer than n=8."""
    for target_id, spec, _size, _slots in plans(real_specs, sizes=(8,)):
        counts = []
        for size in SIZES:
            slots = plan_families(spec, PLAN_SETTINGS, size)
            counts.append(len({tid for slot in slots for tid in slot.tradeoff_ids}))
        assert counts == sorted(counts), f"{target_id}: distinct tradeoffs by size {counts}"


def test_every_divergence_slot_names_a_hypothesis(real_specs):
    for target_id, spec, size, slots in plans(real_specs):
        if not spec.divergence_hypotheses:
            continue
        for slot in slots:
            if slot.case_type_intent == "divergence":
                assert slot.divergence_hypothesis_id, f"{target_id} n={size} slot {slot.slot_index}"


def test_unresolved_tradeoff_fraction_moves_the_hedging_density(real_specs):
    spec = real_specs["theravada"]
    unresolved = {t["id"] for t in spec.tradeoffs if t.get("unresolved")}
    low = plan_families(spec, dict(PLAN_SETTINGS, unresolved_tradeoff_fraction=0.1), 240)
    high = plan_families(spec, dict(PLAN_SETTINGS, unresolved_tradeoff_fraction=0.5), 240)
    count = lambda slots: sum(1 for s in slots if set(s.tradeoff_ids) & unresolved)
    assert count(high) > count(low)


def test_mark_ambiguous_choices_are_attached_at_scale(real_specs):
    for target_id, spec, _size, slots in plans(real_specs, sizes=(240,)):
        wanted = {
            str(c["id"]) for c in spec.unresolved_choices
            if str(c.get("generation_policy", "")).strip() == "mark_ambiguous"
        }
        if not wanted:
            continue
        covered = {slot.unresolved_choice_id for slot in slots if slot.unresolved_choice_id}
        assert covered, f"{target_id}: no mark_ambiguous choice reached any slot"


def test_check_plan_reports_uncovered_floors_as_warnings_below_scale(real_specs):
    spec = real_specs["theravada"]
    slots = plan_families(spec, PLAN_SETTINGS, 8)
    problems = check_plan(spec, slots, PLAN_SETTINGS)
    assert problems and all(p.startswith("WARN") for p in problems)


def test_divergence_fraction_is_respected(real_specs):
    for target_id, _spec, size, slots in plans(real_specs):
        divergence = sum(1 for slot in slots if slot.case_type_intent == "divergence")
        wanted = round(size * PLAN_SETTINGS["divergence_fraction"])
        # Counted in families, so a pair contributing two does not skew the total.
        assert divergence == wanted, f"{target_id} n={size}: {divergence} vs {wanted}"
