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


# -- A3: structural diversity -------------------------------------------------


def test_asker_stance_matches_the_planned_mix(real_specs):
    """Round 1 recorded stance as free text and got one dominant value per axis."""
    from pipeline.records import ASKER_STANCE_MIX

    for target_id, _spec, size, slots in plans(real_specs, sizes=(240,)):
        counts = Counter(slot.asker_stance for slot in slots)
        assert set(counts) == set(ASKER_STANCE_MIX), target_id
        for stance, share in ASKER_STANCE_MIX.items():
            actual = counts[stance] / size
            assert abs(actual - share) < 0.05, f"{target_id} {stance}: {actual:.3f} vs {share}"


def test_every_slot_carries_the_closed_enum_features(real_specs):
    from pipeline.records import HARM_SEVERITY, PUBLIC_OR_PRIVATE, ROLE_TYPE, URGENCY

    for target_id, _spec, size, slots in plans(real_specs):
        for slot in slots:
            assert slot.role_type in ROLE_TYPE, target_id
            assert slot.harm_severity in HARM_SEVERITY
            assert slot.urgency in URGENCY
            assert slot.public_or_private in PUBLIC_OR_PRIVATE
            assert slot.asker_stance


def test_all_severities_and_urgencies_appear(real_specs):
    """A run of nothing but minor private matters is the failure this prevents."""
    from pipeline.records import HARM_SEVERITY, URGENCY

    for target_id, _spec, size, slots in plans(real_specs, sizes=(32, 240)):
        assert set(s.harm_severity for s in slots) == set(HARM_SEVERITY), target_id
        assert set(s.urgency for s in slots) == set(URGENCY), target_id


def test_structural_keys_are_unique_within_a_domain_at_pilot_size(real_specs):
    """Four round-1 pairs were the same situation twice inside one domain."""
    for target_id, _spec, size, slots in plans(real_specs, sizes=(8, 32)):
        keys = Counter(
            slot.structural_key for slot in slots if not slot.counterfactual_group
        )
        repeats = {key: n for key, n in keys.items() if n > 1}
        assert not repeats, f"{target_id} n={size}: {repeats}"


def test_a_contrastive_pair_varies_severity_and_holds_the_setting(real_specs):
    for target_id, _spec, size, slots in plans(real_specs, sizes=(32,)):
        for members in counterfactual_groups(slots).values():
            first, second = (slots[i] for i in members)
            assert first.institution == second.institution, target_id
            assert first.role_type == second.role_type
            assert first.asker_stance == second.asker_stance
            assert first.harm_severity != second.harm_severity


def test_institutions_are_sampled_not_repeated_at_pilot_size(real_specs):
    from pipeline.institutions import INSTITUTIONS

    for target_id, _spec, size, slots in plans(real_specs, sizes=(8, 32)):
        distinct = {slot.institution for slot in slots}
        pairs = len(counterfactual_groups(slots))
        assert len(distinct) >= size - pairs - 1, f"{target_id} n={size}: {len(distinct)}"
        assert distinct <= set(INSTITUTIONS)


def test_the_institution_list_is_large_and_unique():
    from pipeline.institutions import INSTITUTIONS, INSTITUTIONS_BY_SECTOR, SECTOR_OF

    assert len(INSTITUTIONS) >= 40
    assert len(set(INSTITUTIONS)) == len(INSTITUTIONS)
    assert len(INSTITUTIONS_BY_SECTOR) >= 6
    assert all(SECTOR_OF[name] for name in INSTITUTIONS)


def test_the_proportional_cycle_interleaves_rather_than_blocking():
    """A truncated run must still hold the mixture, so the labels cannot come in blocks."""
    from pipeline.plan import _proportional_cycle

    out = _proportional_cycle({"a": 0.5, "b": 0.5}, 10)
    assert out.count("a") == 5 and out.count("b") == 5
    assert out[:4] != ["a", "a", "a", "a"]


def test_the_proportional_cycle_handles_small_counts():
    from pipeline.plan import _proportional_cycle

    assert _proportional_cycle({"a": 0.9, "b": 0.1}, 1) == ["a"]
    assert _proportional_cycle({"a": 0.5, "b": 0.5}, 0) == []


# -- A6/A7/B5 ------------------------------------------------------------------


def test_every_reframing_variant_has_its_own_instruction():
    """fiction and roleplay were collapsing into the same 'write a scene' request."""
    from pipeline.records import VARIANTS
    from prompts.generation import REFRAMING_VARIANT_INSTRUCTIONS

    assert set(REFRAMING_VARIANT_INSTRUCTIONS) == set(VARIANTS) - {"base"}
    instructions = list(REFRAMING_VARIANT_INSTRUCTIONS.values())
    assert len(set(instructions)) == len(instructions)
    assert "NOT asking the assistant to write the scene" in REFRAMING_VARIANT_INSTRUCTIONS["fiction"]
    assert "take a role inside the scene" in REFRAMING_VARIANT_INSTRUCTIONS["roleplay"]


def test_the_reframing_prompt_demands_a_full_rewrite():
    from prompts.generation import REFRAMING_PROMPT

    assert "Change every noun" in REFRAMING_PROMPT
    assert "{{stance}}" in REFRAMING_PROMPT


def test_allowed_terms_reach_the_generator_positively(real_specs):
    from pipeline.target import render_cue_policy

    for target_id, spec in real_specs.items():
        if not spec.allowed_terms:
            continue
        rendered = render_cue_policy(spec)
        assert "NOT cues" in rendered, target_id
        assert spec.allowed_terms[0] in rendered


def test_allowed_and_soft_terms_may_overlap_but_not_with_forbidden(real_specs):
    """The Catholic spec deliberately lists five words as both allowed and soft."""
    for target_id, spec in real_specs.items():
        forbidden = {t.lower() for t in spec.forbidden_terms}
        assert not {t.lower() for t in spec.allowed_terms} & forbidden, target_id
        assert not {t.lower() for t in spec.soft_terms} & forbidden, target_id


def test_a_term_in_both_allowed_and_forbidden_is_a_spec_error(real_specs, tmp_path):
    import yaml

    from pipeline.target import validate_spec

    raw = yaml.safe_load(open("targets/catholic/spec.yaml", encoding="utf-8"))
    raw["cue_policy"]["allowed_terms"] = list(raw["cue_policy"]["forbidden_terms"])[:1]
    problems = validate_spec(raw, real_specs["catholic"].key_passages, tmp_path / "spec.yaml")
    assert any("overlaps forbidden_terms" in problem for problem in problems)


def test_strict_specs_requires_avoid_keywords(real_specs, tmp_path):
    import yaml

    from pipeline.target import validate_spec

    raw = yaml.safe_load(open("targets/catholic/spec.yaml", encoding="utf-8"))
    for choice in raw.get("unresolved_choices") or []:
        if str(choice.get("generation_policy", "")).strip() == "avoid":
            choice.pop("avoid_keywords", None)
    passages = real_specs["catholic"].key_passages
    assert not any(
        "avoid_keywords" in p for p in validate_spec(raw, passages, tmp_path / "s.yaml", strict=False)
    )
    strict = validate_spec(raw, passages, tmp_path / "s.yaml", strict=True)
    assert any("avoid_keywords" in problem for problem in strict)


def test_avoided_topics_reach_the_reviewer(real_specs):
    from pipeline.target import render_for_reviewer

    for target_id, spec in real_specs.items():
        if not spec.avoided_topics():
            continue
        assert "does not build scenarios about" in render_for_reviewer(spec), target_id


def test_reviewer_render_honours_the_selected_layers(real_specs):
    from pipeline.target import render_for_reviewer

    spec = real_specs["confucian"]
    layered = [p for p in spec.principles if p.get("layer")]
    if not layered:
        pytest.skip("confucian has no layered principles")
    core_only = render_for_reviewer(spec, ["core"])
    non_core = [p for p in layered if p.get("layer") != "core"]
    if non_core:
        assert non_core[0]["id"] not in core_only


def test_the_stipulation_guard_quotes_the_hypothesis_and_demands_a_self_check(real_specs):
    """Four of sixteen Protestant prompts got through the earlier, generic wording."""
    from prompts import render
    from prompts.generation import STIPULATION_GUARD

    hypothesis = "the target refuses to lie where a generic assistant would soften"
    guard = render(STIPULATION_GUARD, hypothesis=hypothesis)
    assert hypothesis in guard
    assert "SELF-CHECK" in guard
    assert "sentence by sentence" in guard
    assert "rule out its opposite" in guard


def test_the_guard_is_only_rendered_for_divergence_families(real_specs):
    """An ordinary family has no move to stipulate, so the guard would be noise."""
    import inspect

    from pipeline import generate

    source = inspect.getsource(generate.generate_prompts)
    assert 'family.case_type_intent == "divergence"' in source
