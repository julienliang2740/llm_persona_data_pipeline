"""The judge is blind to position, and a generic that says the same thing is not divergence.

Round 2 always put the candidate in slot A and 23 of 26 verdicts came back preferring it;
separately, the critic rejected 5 of 23 `value` verdicts because the no-specification reply
already made the same claim in its own words.
"""

from __future__ import annotations

import random
from collections import Counter

import pytest

from pipeline.divergence import verdict_from_payload


def labels(prompt_id: str) -> dict[str, str]:
    """Reproduce the shuffle divergence.py performs for one prompt id."""
    replies = [("candidate", "x"), ("generic", "y"), ("weak", "z")]
    random.Random(prompt_id).shuffle(replies)
    return {kind: "ABC"[index] for index, (kind, _text) in enumerate(replies)}


def a_payload(**overrides):
    base = {
        "actions": {"a": "action a", "b": "action b", "c": "action c"},
        "pairwise": {"test_vs_generic": True, "test_vs_weak": True, "generic_vs_weak": False},
        "closer_to": "neither",
        "value_named": "Her ability to change course is what matters.",
        "generic_echo": "",
        "generic_makes_same_claim": False,
        "divergence_source": "value",
        "diverges": True,
        "kind": "action",
        "hypothesis_id": "h1",
        "explanation": "differs",
    }
    base.update(overrides)
    return base


# -- the shuffle --------------------------------------------------------------


def test_the_candidate_does_not_always_get_the_same_label():
    seen = Counter(labels(f"pr_{i}")["candidate"] for i in range(300))
    assert set(seen) == {"A", "B", "C"}
    for label in "ABC":
        assert seen[label] > 50, seen


def test_all_three_labels_are_used_exactly_once():
    for i in range(50):
        assigned = labels(f"pr_{i}")
        assert sorted(assigned.values()) == ["A", "B", "C"]
        assert set(assigned) == {"candidate", "generic", "weak"}


def test_the_shuffle_is_reproducible_for_one_prompt():
    assert labels("pr_abc") == labels("pr_abc")


# -- mapping back -------------------------------------------------------------


def test_actions_are_mapped_back_to_the_right_reply():
    label_of = {"candidate": "C", "generic": "A", "weak": "B"}
    verdict = verdict_from_payload(a_payload(), "pr_1", "judge", label_of, "h1")
    assert verdict.candidate_action == "action c"
    assert verdict.generic_action == "action a"
    assert verdict.base_action == "action b"


def test_the_label_order_is_recorded_for_audit():
    label_of = {"candidate": "C", "generic": "A", "weak": "B"}
    verdict = verdict_from_payload(a_payload(), "pr_1", "judge", label_of, "h1")
    assert verdict.presented_first == "C"
    assert verdict.label_order == "A=generic, B=weak, C=candidate"


def test_pairwise_keys_map_onto_the_record_fields():
    label_of = {"candidate": "A", "generic": "B", "weak": "C"}
    verdict = verdict_from_payload(
        a_payload(pairwise={"test_vs_generic": False, "test_vs_weak": True, "generic_vs_weak": True}),
        "pr_1", "judge", label_of, "h1",
    )
    assert verdict.diverges_vs_generic is False
    assert verdict.diverges_vs_base is True
    assert verdict.generic_differs_from_base is True


def test_mapping_holds_for_every_possible_shuffle():
    import itertools

    for order in itertools.permutations(["candidate", "generic", "weak"]):
        label_of = {kind: "ABC"[i] for i, kind in enumerate(order)}
        verdict = verdict_from_payload(a_payload(), "pr_1", "judge", label_of, "h1")
        assert verdict.candidate_action == f"action {label_of['candidate'].lower()}"
        assert verdict.generic_action == f"action {label_of['generic'].lower()}"
        assert verdict.base_action == f"action {label_of['weak'].lower()}"


# -- the forced-capability rule -----------------------------------------------


def test_a_generic_making_the_same_claim_forces_capability():
    """This flips the five value verdicts the critic rejected by hand."""
    verdict = verdict_from_payload(
        a_payload(
            generic_makes_same_claim=True,
            generic_echo="That's not a policy breach in any meaningful moral sense.",
            divergence_source="value",
            diverges=True,
        ),
        "pr_5557214012", "judge", labels("pr_5557214012"), "h1",
    )
    assert verdict.divergence_source == "capability"
    assert verdict.diverges is False
    assert verdict.generic_echo.startswith("That's not a policy breach")


def test_the_two_gate_rule_survives():
    empty_value = verdict_from_payload(a_payload(value_named=""), "p", "j", labels("p"), "h")
    assert empty_value.diverges is False
    wrong_source = verdict_from_payload(
        a_payload(divergence_source="capability"), "p", "j", labels("p"), "h"
    )
    assert wrong_source.diverges is False


def test_a_genuine_value_difference_still_counts():
    verdict = verdict_from_payload(a_payload(), "p", "j", labels("p"), "h")
    assert verdict.diverges is True and verdict.divergence_source == "value"


def test_an_unrecognised_source_falls_back_to_none():
    verdict = verdict_from_payload(a_payload(divergence_source="vibes"), "p", "j", labels("p"), "h")
    assert verdict.divergence_source == "none" and verdict.diverges is False


def test_closer_to_rejects_the_old_flattering_value():
    """"candidate" is no longer offered; the judge answers generic, weak or neither."""
    verdict = verdict_from_payload(a_payload(closer_to="candidate"), "p", "j", labels("p"), "h")
    assert verdict.closer_to == ""
    for value in ("generic", "weak", "neither"):
        assert verdict_from_payload(a_payload(closer_to=value), "p", "j", labels("p"), "h").closer_to == value


def test_the_judge_prompt_is_written_without_positional_cues():
    from prompts.review import DIVERGENCE_JUDGE_PROMPT

    assert "{{candidate_label}}" in DIVERGENCE_JUDGE_PROMPT
    assert "{{generic_label}}" in DIVERGENCE_JUDGE_PROMPT
    assert "Do not read anything into the ordering" in DIVERGENCE_JUDGE_PROMPT
    assert "generic_echo" in DIVERGENCE_JUDGE_PROMPT
    assert "generic_makes_same_claim" in DIVERGENCE_JUDGE_PROMPT


# -- the strong-generic control ------------------------------------------------


@pytest.mark.parametrize(
    "config_name", ["configs/pilot.yaml", "configs/full.yaml", "configs/pilot_low_effort.yaml"]
)
def test_the_control_differs_from_the_generator_only_in_the_spec(config_name):
    from pipeline.baseline import strong_generic_role
    from pipeline.config import load_config

    config = load_config(config_name)
    generator = config.role("generator")
    control = strong_generic_role(config)
    assert control.model == generator.model
    assert control.max_tokens == generator.max_tokens
    assert control.extra_body == generator.extra_body
    assert control.temperature == generator.temperature


def test_the_control_falls_back_to_the_generator_when_unconfigured(pilot_config):
    import copy

    from pipeline.baseline import strong_generic_role

    config = copy.deepcopy(pilot_config)
    config.roles.pop("strong_generic")
    config.raw["models"].pop("strong_generic", None)
    control = strong_generic_role(config)
    assert control.model == config.role("generator").model
    assert control.name == "strong_generic"


def test_the_control_prompt_matches_length_by_instruction_not_by_budget():
    from prompts.review import STRONG_GENERIC_SYSTEM_PROMPT

    assert "250 to 400 words" in STRONG_GENERIC_SYSTEM_PROMPT
    lowered = STRONG_GENERIC_SYSTEM_PROMPT.lower()
    for word in ("tradition", "specification", "target", "principle"):
        assert word not in lowered


# -- the conservative family rule ---------------------------------------------


def family_rates(sources_by_family):
    """Run _family_divergence_rates over a synthetic set of decisions."""
    from pipeline.divergence import _family_divergence_rates
    from pipeline.records import Decision, Prompt, Response

    decisions, responses, prompts = [], [], {}
    for family_id, sources in sources_by_family.items():
        for index, source in enumerate(sources):
            response_id = f"{family_id}_r{index}"
            prompt_id = f"{family_id}_p{index}"
            status = "unverified" if source is None else "confirmed"
            decisions.append(
                Decision(response_id, True, [], "divergence",
                         divergence_status=status, divergence_source=source or "")
            )
            responses.append(Response(response_id, prompt_id, "d", "a"))
            prompts[prompt_id] = Prompt(prompt_id, family_id, "base", "text", "divergence")
    return _family_divergence_rates(decisions, responses, prompts, [])


def test_a_family_counts_as_value_only_when_every_prompt_is():
    """The old rule was a max over two renderings of the same situation."""
    rates = family_rates({
        "fam_both": ["value", "value"],
        "fam_one": ["value", "capability"],
        "fam_none": ["capability", "capability"],
    })
    assert rates["divergence_families_intended"] == 3
    assert rates["divergence_families_value"] == 1
    assert rates["divergence_value_rate_by_family"] == round(1 / 3, 3)


def test_the_any_prompt_rate_is_reported_as_a_secondary_line():
    rates = family_rates({
        "fam_both": ["value", "value"],
        "fam_one": ["value", "capability"],
        "fam_none": ["capability", "capability"],
    })
    assert rates["divergence_families_value_any_prompt"] == 2
    assert rates["divergence_value_rate_any_prompt"] == round(2 / 3, 3)
    assert rates["divergence_value_rate_any_prompt"] > rates["divergence_value_rate_by_family"]


def test_an_unverified_prompt_neither_confirms_nor_breaks_its_family():
    rates = family_rates({"fam_a": ["value", None], "fam_b": ["capability", None]})
    assert rates["divergence_families_value"] == 1
    assert rates["divergence_families_judged"] == 2


def test_a_family_with_nothing_judged_is_intended_but_not_value():
    rates = family_rates({"fam_a": [None, None]})
    assert rates["divergence_families_intended"] == 1
    assert rates["divergence_families_judged"] == 0
    assert rates["divergence_families_value"] == 0


def test_a_single_prompt_family_still_works():
    rates = family_rates({"fam_a": ["value"], "fam_b": ["none"]})
    assert rates["divergence_families_value"] == 1
    assert rates["divergence_value_rate_by_family"] == 0.5


def test_no_intended_families_gives_a_zero_rate():
    assert family_rates({})["divergence_value_rate_by_family"] == 0.0
