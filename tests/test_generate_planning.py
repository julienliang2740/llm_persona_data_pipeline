"""Coverage planning for counterfactual groups, explicit mode and layers. No network."""

from __future__ import annotations

from collections import Counter

import pytest

from pipeline.plan import (
    FamilySlot,
    align_counterfactual_groups,
    avoided_topic_hit,
    pair_counterfactual_slots,
    plan_families,
    selected_layers,
)
from pipeline.records import Family

SETTINGS = {
    "divergence_fraction": 0.4,
    "eval_family_fraction": 0.2,
    "reserved_family_fraction": 0.0,
    "counterfactual_fraction": 0.4,
    "explicit_fraction": 0.1,
}


def make_family(family_id, split, group=None, reason=""):
    return Family(
        family_id=family_id,
        target_id="toy",
        domain="work",
        tradeoff_ids=[],
        principle_ids=[],
        case_type_intent="ordinary",
        seed_situation="s",
        why_it_is_hard="w",
        split=split,
        counterfactual_group_id=group,
        reserved_reason=reason,
    )


def test_counterfactual_slots_are_planned_as_complete_pairs(toy_spec):
    slots = plan_families(toy_spec, SETTINGS, 20)
    groups = Counter(s.counterfactual_group for s in slots if s.counterfactual_group)
    assert groups and set(groups.values()) == {2}
    assert sum(groups.values()) == 8


def test_both_members_of_a_pair_share_a_domain_and_a_tradeoff(toy_spec):
    """A pair is one situation with one fact changed, so it cannot span domains."""
    slots = plan_families(toy_spec, SETTINGS, 20)
    by_group: dict[str, list] = {}
    for slot in slots:
        if slot.counterfactual_group:
            by_group.setdefault(slot.counterfactual_group, []).append(slot)
    for members in by_group.values():
        assert len({m.domain for m in members}) == 1
        assert members[0].tradeoff_ids == members[1].tradeoff_ids


def test_a_domain_too_small_to_host_a_pair_produces_none(toy_spec):
    """Two domains, one family each: there is no room for a contrast."""
    slots = plan_families(toy_spec, SETTINGS, 2)
    assert all(s.counterfactual_group is None for s in slots)


def test_explicit_slots_are_planned(toy_spec):
    slots = plan_families(toy_spec, SETTINGS, 20)
    assert sum(1 for s in slots if s.mode == "explicit") == 2


def test_explicit_fraction_zero_produces_no_explicit_slots(toy_spec):
    slots = plan_families(toy_spec, dict(SETTINGS, explicit_fraction=0.0), 20)
    assert all(s.mode == "neutral" for s in slots)


def test_only_complete_pairs_survive_into_a_batch():
    """A group whose partner landed in another batch has nothing to contrast with."""
    batch = [
        FamilySlot(0, "work", [], "ordinary", "train", counterfactual_group="g1"),
        FamilySlot(1, "work", [], "ordinary", "train", counterfactual_group="g1"),
        FamilySlot(2, "work", [], "ordinary", "train", counterfactual_group="g2"),
        FamilySlot(3, "work", [], "ordinary", "train"),
    ]
    assert pair_counterfactual_slots(batch) == {0: "g1", 1: "g1"}


def test_no_counterfactual_slots_means_no_pairs():
    assert pair_counterfactual_slots([FamilySlot(0, "work", [], "ordinary", "train")]) == {}


def test_batching_never_splits_a_plan_time_pair(toy_spec):
    """Batch size is forced even, so adjacent paired slots stay in one generator call."""
    slots = plan_families(toy_spec, SETTINGS, 20)
    per_call = 4
    batch_size = max(2, per_call - (per_call % 2))
    by_domain: dict[str, list] = {}
    for slot in slots:
        by_domain.setdefault(slot.domain, []).append(slot)
    intact = 0
    for domain_slots in by_domain.values():
        ordered = sorted(domain_slots, key=lambda s: (s.counterfactual_group or "~", s.index))
        for start in range(0, len(ordered), batch_size):
            batch = ordered[start : start + batch_size]
            intact += len(pair_counterfactual_slots(batch)) // 2
    total_pairs = len({s.counterfactual_group for s in slots if s.counterfactual_group})
    assert intact == total_pairs


def test_a_counterfactual_group_is_forced_onto_one_side_of_the_split():
    families = [
        make_family("a", "train", "cf_1"),
        make_family("b", "eval", "cf_1"),
        make_family("c", "train", None),
    ]
    align_counterfactual_groups(families)
    assert [f.split for f in families] == ["eval", "eval", "train"]


def test_a_reserved_member_pulls_its_whole_group_into_reserved():
    families = [
        make_family("a", "train", "cf_1"),
        make_family("b", "reserved", "cf_1", reason="avoided-topic keyword: probate"),
    ]
    align_counterfactual_groups(families)
    assert [f.split for f in families] == ["reserved", "reserved"]
    assert "probate" in families[0].reserved_reason


def test_split_group_id_falls_back_to_the_family_id():
    assert make_family("a", "train").split_group_id == "a"
    assert make_family("a", "train", "cf_1").split_group_id == "cf_1"


def test_avoided_topic_screen_is_word_bounded():
    assert avoided_topic_hit("a dispute over the estate", ["estate"]) == "estate"
    assert avoided_topic_hit("a real estate agent called", ["probate"]) == ""
    assert avoided_topic_hit("anything at all", []) == ""


def testselected_layers_uses_the_spec_default(toy_spec, pilot_config):
    assert selected_layers(toy_spec, pilot_config) == ["core"]


def test_config_target_layers_overrides_the_spec(toy_spec, pilot_config):
    import copy

    config = copy.deepcopy(pilot_config)
    config.raw["generation"]["target_layers"] = ["core", "speculative"]
    assert selected_layers(toy_spec, config) == ["core", "speculative"]


def test_an_unknown_layer_name_is_a_clear_error(toy_spec, pilot_config):
    import copy

    config = copy.deepcopy(pilot_config)
    config.raw["generation"]["target_layers"] = ["nonexistent"]
    with pytest.raises(ValueError) as error:
        selected_layers(toy_spec, config)
    assert "nonexistent" in str(error.value)
    assert "core" in str(error.value)


def test_explicit_instructions_name_the_actual_target(toy_spec):
    """Told only 'you may name the tradition', a generator invents one. Observed in a run."""
    from prompts import render
    from prompts.generation import EXPLICIT_MODE_PROMPT_INSTRUCTIONS
    from pipeline.generate import mode_instructions

    prompt_side = render(EXPLICIT_MODE_PROMPT_INSTRUCTIONS, target_name=toy_spec.name)
    response_side = mode_instructions("explicit", "a, b", toy_spec.name)
    assert toy_spec.name in prompt_side
    assert toy_spec.name in response_side
    assert "no other" in prompt_side


def test_neutral_instructions_carry_the_forbidden_terms_not_the_name(toy_spec):
    from pipeline.generate import mode_instructions

    neutral = mode_instructions("neutral", "Careful Practice, HCP", toy_spec.name)
    assert "Careful Practice" in neutral
    assert toy_spec.name not in neutral
