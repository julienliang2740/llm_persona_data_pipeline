"""B1 reviewer rubric and B2 three-way divergence. Offline: canned judge payloads."""

from __future__ import annotations

import pytest

from pipeline.records import BaselineAnswer, Response, Review
from pipeline.target import render_open_questions, render_signature_moves
from pipeline.review import _review_from_payload, missing_score_keys


def payload(**overrides):
    base = {
        "judgment_evidence_quote": "Tell her before she signs, not after.",
        "judgment_move": "acts while the other person can still change course",
        "scores": {
            "fidelity": 5,
            "judgment_not_terminology": 5,
            "scenario_quality": 4,
            "cue_leakage": False,
            "confident_on_unresolved": False,
            "formulaic_shape": False,
            "prompt_stipulates_move": False,
            "quoted_source_text": False,
            "archaic_register": False,
        },
        "signature_moves_present": ["names_the_act_first"],
        "notes": ["Modern safeguarding law would also require a report."],
        "issues": [],
        "verdict": "accept",
        "rationale": "Good.",
    }
    base.update(overrides)
    return base


def a_response():
    return Response("resp_1", "pr_1", "deliberation", "answer")


# -- B1: the evidence gate ---------------------------------------------------


def test_an_empty_evidence_quote_caps_the_judgment_score(real_specs):
    """judgment_not_terminology was 5 on 80 of 83 round-1 reviews."""
    review = _review_from_payload(payload(judgment_evidence_quote=""), a_response(), "m")
    assert review.scores["judgment_not_terminology"] == 3
    assert review.scores["fidelity"] == 5  # only the one score is capped


def test_a_present_quote_leaves_the_score_alone():
    review = _review_from_payload(payload(), a_response(), "m")
    assert review.scores["judgment_not_terminology"] == 5
    assert review.judgment_evidence_quote.startswith("Tell her")
    assert review.judgment_move


def test_a_whitespace_only_quote_counts_as_empty():
    review = _review_from_payload(payload(judgment_evidence_quote="   "), a_response(), "m")
    assert review.scores["judgment_not_terminology"] == 3


def test_notes_are_captured_and_kept_off_the_scores():
    review = _review_from_payload(payload(), a_response(), "m")
    assert review.notes and "safeguarding" in review.notes[0]
    assert "notes" not in review.scores


def test_signature_moves_are_recorded():
    review = _review_from_payload(payload(), a_response(), "m")
    assert review.signature_moves_present == ["names_the_act_first"]


def test_the_new_boolean_flags_round_trip():
    review = _review_from_payload(
        payload(scores=dict(payload()["scores"], formulaic_shape=True, prompt_stipulates_move=True)),
        a_response(),
        "m",
    )
    assert review.scores["formulaic_shape"] is True
    assert review.scores["prompt_stipulates_move"] is True


def test_missing_score_keys_are_detected():
    """A missing boolean reads as false, silently clearing a defect flag."""
    incomplete = payload()
    del incomplete["scores"]["formulaic_shape"]
    del incomplete["scores"]["archaic_register"]
    assert sorted(missing_score_keys(incomplete)) == ["archaic_register", "formulaic_shape"]


def test_a_complete_payload_reports_no_missing_keys():
    assert missing_score_keys(payload()) == []


def test_missing_scores_object_reports_every_key():
    assert len(missing_score_keys({"verdict": "accept"})) == 9


# -- B1: open questions have a resolved part ---------------------------------


def test_open_questions_separate_the_settled_part_from_the_open_one(real_specs):
    """Round 1 rejected answers for stating the spec's own lean on an unresolved tradeoff."""
    text = render_open_questions(real_specs["catholic"])
    assert "SETTLED, be decisive about this:" in text
    assert "OPEN, do not settle this:" in text


def test_open_questions_include_mark_ambiguous_choices(real_specs):
    for spec in real_specs.values():
        ambiguous = [
            c for c in spec.unresolved_choices
            if str(c.get("generation_policy", "")).strip() == "mark_ambiguous"
        ]
        if not ambiguous:
            continue
        text = render_open_questions(spec)
        assert str(ambiguous[0]["id"]) in text


def test_a_target_with_nothing_open_says_so(toy_spec):
    from dataclasses import replace

    flat = replace(toy_spec, tradeoffs=[], unresolved_choices=[])
    assert "marks nothing as open" in render_open_questions(flat)


def test_signature_moves_render_when_the_spec_has_them(real_specs):
    for target_id, spec in real_specs.items():
        if spec.signature_moves:
            rendered = render_signature_moves(spec)
            assert rendered.strip(), target_id
            break
    else:
        pytest.skip("no spec defines signature_moves yet")


def test_signature_moves_render_empty_when_absent(toy_spec):
    assert render_signature_moves(toy_spec) == ""


def test_allowed_terms_are_exposed_when_present(real_specs):
    assert any(spec.allowed_terms for spec in real_specs.values())


# -- B2: truncation and the value gate ---------------------------------------


def test_a_truncated_baseline_is_detected_by_finish_reason():
    """18 of 34 round-1 baselines were cut off and judged as if complete."""
    answer = BaselineAnswer("p", "m", "Ultimately, the decision to reveal your brother's", finish_reason="length")
    assert answer.truncated


def test_an_answer_without_terminal_punctuation_is_treated_as_truncated():
    assert BaselineAnswer("p", "m", "Consider reporting if", finish_reason="stop").truncated


def test_a_complete_answer_is_not_truncated():
    assert not BaselineAnswer("p", "m", "Tell her today.", finish_reason="stop").truncated


def test_a_quoted_answer_ending_counts_as_complete():
    assert not BaselineAnswer("p", "m", 'Say "I cannot do that."', finish_reason="stop").truncated


def test_the_judge_prompt_demands_actions_before_comparison():
    from prompts.review import DIVERGENCE_JUDGE_PROMPT

    assert "Do this before you compare anything" in DIVERGENCE_JUDGE_PROMPT
    for key in ("closer_to", "value_named", "divergence_source", "hypothesis_id"):
        assert key in DIVERGENCE_JUDGE_PROMPT


def test_the_judge_prompt_forces_diverges_false_without_a_named_value():
    from prompts.review import DIVERGENCE_JUDGE_PROMPT

    assert "empty `value_named` means" in DIVERGENCE_JUDGE_PROMPT
    assert '"capability"' in DIVERGENCE_JUDGE_PROMPT


def test_the_strong_generic_prompt_never_mentions_a_target():
    from prompts.review import STRONG_GENERIC_SYSTEM_PROMPT

    lowered = STRONG_GENERIC_SYSTEM_PROMPT.lower()
    for word in ("tradition", "specification", "target", "principle"):
        assert word not in lowered
