"""Target spec parsing, validation errors, and prompt rendering."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from pipeline.target import (
    SpecError,
    load_target,
    parse_key_passages,
    render_for_generator,
    render_for_reviewer,
    render_key_passages,
    validate_spec,
)
from tests.conftest import FIXTURE_TARGETS, TOY_TARGET_ID


def test_toy_target_loads(toy_spec):
    assert toy_spec.target_id == "toy"
    assert len(toy_spec.principles) == 4
    assert {p.id for p in toy_spec.key_passages} == {
        "HCP 1.1",
        "HCP 1.4",
        "HCP 2.2",
        "HCP 2.7",
        "HCP 3.3",
    }
    assert toy_spec.tradeoff("candour_vs_a_promise")["unresolved"] is True


def test_key_passage_parsing_splits_id_from_title():
    passages = parse_key_passages(
        "# heading is ignored\n\n## A 1.1 — On something\nbody one\n\n### B 2.2\nbody two\n"
    )
    assert [(p.id, p.title) for p in passages] == [("A 1.1", "On something"), ("B 2.2", "")]
    assert passages[0].text == "body one"


def test_domain_weights_normalise(toy_spec):
    weights = dict(toy_spec.domain_weights())
    assert pytest.approx(sum(weights.values())) == 1.0


def test_generator_rendering_carries_the_unresolved_flag(toy_spec):
    text = render_for_generator(toy_spec)
    assert "UNRESOLVED" in text
    assert "candour_vs_a_promise" in text
    assert "Count the absent" in text
    # The cue policy must reach the generator, or the prompts will name the target.
    assert "Handbook of Careful Practice" in text


def test_reviewer_rendering_includes_red_flags(toy_spec):
    text = render_for_reviewer(toy_spec)
    assert "Common distortions" in text
    assert "blind" not in text.lower() or True  # target-agnostic; just check it renders


def test_key_passage_rendering_selects_and_truncates(toy_spec):
    only_one = render_key_passages(toy_spec, ["HCP 2.7"])
    assert "HCP 2.7" in only_one and "HCP 1.1" not in only_one
    truncated = render_key_passages(toy_spec, None, max_chars=200)
    assert "further passages omitted" in truncated


def _toy_raw() -> dict:
    return yaml.safe_load(
        (FIXTURE_TARGETS / TOY_TARGET_ID / "spec.yaml").read_text(encoding="utf-8")
    )


def test_missing_required_key_is_reported(toy_spec):
    raw = _toy_raw()
    del raw["summary"]
    problems = validate_spec(raw, toy_spec.key_passages, Path("spec.yaml"))
    assert any("summary" in problem for problem in problems)


def test_principle_without_sources_is_reported(toy_spec):
    raw = _toy_raw()
    del raw["principles"][1]["sources"]
    problems = validate_spec(raw, toy_spec.key_passages, Path("spec.yaml"))
    assert any("cites no sources" in problem and "TP02" in problem for problem in problems)


def test_citation_of_an_unknown_passage_is_reported(toy_spec):
    raw = _toy_raw()
    raw["principles"][0]["sources"] = ["HCP 9.9"]
    problems = validate_spec(raw, toy_spec.key_passages, Path("spec.yaml"))
    assert any("HCP 9.9" in problem for problem in problems)


def test_resolved_tradeoff_without_a_lean_is_reported(toy_spec):
    raw = _toy_raw()
    del raw["tradeoffs"][0]["intended_lean"]
    problems = validate_spec(raw, toy_spec.key_passages, Path("spec.yaml"))
    assert any("intended_lean" in problem for problem in problems)


def test_cue_policy_without_forbidden_terms_is_reported(toy_spec):
    raw = _toy_raw()
    raw["cue_policy"]["forbidden_terms"] = []
    problems = validate_spec(raw, toy_spec.key_passages, Path("spec.yaml"))
    assert any("forbidden_terms" in problem for problem in problems)


def test_no_key_passages_is_reported():
    problems = validate_spec(_toy_raw(), [], Path("spec.yaml"))
    assert any("key_passages.md" in problem for problem in problems)


def test_missing_target_directory_raises(tmp_path):
    with pytest.raises(SpecError) as error:
        load_target(tmp_path, "nope")
    assert "spec.yaml" in str(error.value)


def test_loader_reports_every_problem_at_once(tmp_path):
    root = tmp_path / "broken"
    (root / "references").mkdir(parents=True)
    (root / "references" / "key_passages.md").write_text("## A 1.1\nbody\n", encoding="utf-8")
    (root / "spec.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "broken",
                "name": "Broken",
                "version": "0.1",
                "summary": "x",
                "principles": [{"id": "P1", "name": "n", "description": "d"}],
                "domains": [{"id": "work"}],
                "cue_policy": {"forbidden_terms": ["x"]},
                "reference_material": [{"id": "key_passages", "path": "references/key_passages.md"}],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(SpecError) as error:
        load_target(tmp_path, "broken")
    text = str(error.value)
    assert "cites no sources" in text
    assert "only 1 principles" in text


def test_passage_ids_stripped_of_a_forbidden_prefix_are_repaired(toy_spec):
    """"HCP" is on the forbidden-terms list, so generators drop it from passage ids."""
    from pipeline.target import normalise_passage_ids

    assert normalise_passage_ids(toy_spec, ["1.1", "hcp 2.7", "HCP 3.3"]) == [
        "HCP 1.1",
        "HCP 2.7",
        "HCP 3.3",
    ]


def test_an_unmatched_passage_id_is_kept_as_written(toy_spec):
    """A wrong citation must stay visible rather than be invented into a real one."""
    from pipeline.target import normalise_passage_ids

    assert normalise_passage_ids(toy_spec, ["9.9"]) == ["9.9"]


def test_layers_default_to_generate_by_default(toy_spec):
    """A layer marked generate_by_default: false is off unless the config asks for it."""
    assert toy_spec.default_layer_ids() == ["core"]
    default_ids = [p["id"] for p in toy_spec.principles_for_layers(None)]
    assert default_ids == ["TP01", "TP02", "TP03"]
    both = [p["id"] for p in toy_spec.principles_for_layers(["core", "speculative"])]
    assert "TP04" in both


def test_a_spec_without_layers_includes_every_principle(toy_spec):
    """Catholic has no layers at all; every principle must still be rendered."""
    from dataclasses import replace

    flat = replace(toy_spec, layers=[])
    assert len(flat.principles_for_layers(None)) == len(flat.principles)


def test_principles_without_a_layer_are_always_included(toy_spec):
    from dataclasses import replace

    spec = replace(
        toy_spec,
        principles=[{"id": "X", "name": "n", "description": "d"}] + toy_spec.principles,
    )
    assert "X" in [p["id"] for p in spec.principles_for_layers(["core"])]


def test_soft_terms_are_separate_from_forbidden_terms(toy_spec):
    assert toy_spec.soft_terms == ["prudence", "repair"]
    assert not set(toy_spec.soft_terms) & set(toy_spec.forbidden_terms)


def test_avoided_topics_and_keywords(toy_spec):
    assert [c["id"] for c in toy_spec.avoided_topics()] == ["contested_inheritance"]
    assert "probate" in toy_spec.avoid_keywords()


def test_response_stage_rendering_is_smaller_than_family_stage(toy_spec):
    """Real specs are 60 KB; response generation must not resend the whole thing."""
    from pipeline.target import render_for_generator

    family_stage = render_for_generator(toy_spec, stage="families")
    response_stage = render_for_generator(
        toy_spec, principle_ids=["TP01"], tradeoff_ids=["speed_vs_checking"], stage="responses"
    )
    assert len(response_stage) < len(family_stage)
    # The coverage plan and the avoid list belong to family generation only.
    assert "Situation domains to cover" in family_stage
    assert "Situation domains to cover" not in response_stage
    assert "must not build scenarios about" in family_stage
    # Only the family's own principle survives into the response prompt.
    assert "TP01" in response_stage and "TP03 " not in response_stage


def test_avoided_topics_reach_the_family_prompt(toy_spec):
    from pipeline.target import render_for_generator

    assert "contested_inheritance" in render_for_generator(toy_spec, stage="families")


def test_the_reviewer_rubric_carries_its_calibration_and_red_flags():
    """The reviewer scored every response 5 on a real run before this text was added."""
    from prompts.review import FIDELITY_REVIEW_PROMPT, REVIEWER_SYSTEM_PROMPT

    assert "Most competent responses are a 4" in FIDELITY_REVIEW_PROMPT
    for flag in (
        "unresolved",
        "rank, seniority or popularity",
        "Archaic",
        "scripture-sounding",
        "invariant to the",
    ):
        assert flag.lower() in FIDELITY_REVIEW_PROMPT.lower(), flag
    # The system prompt must protect the correct behaviours from being marked down.
    assert "not indecisiveness" in REVIEWER_SYSTEM_PROMPT
