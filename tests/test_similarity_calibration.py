"""B3: similarity measured on situations only, with a per-run calibrated cut."""

from __future__ import annotations

import pytest

from pipeline.records import Family, Prompt
from pipeline.similarity import (
    all_pair_scores,
    calibrated_threshold,
    _comparison_text,
    _median,
    jaccard,
)


def a_family(seed="a warehouse supervisor finds a damaged pallet", split="train"):
    return Family(
        family_id="fam_1",
        target_id="t",
        domain="work",
        tradeoff_ids=[],
        principle_ids=[],
        case_type_intent="ordinary",
        seed_situation=seed,
        why_it_is_hard="hard",
        split=split,
    )


def test_comparison_text_uses_the_situation_not_the_answer():
    """Answers share register and wash out the scenario signal they are meant to carry."""
    prompt = Prompt("p", "fam_1", "base", "should I sign it off?", "ordinary")
    text = _comparison_text(prompt, a_family())
    assert "should I sign it off?" in text
    assert "damaged pallet" in text


def test_comparison_text_survives_a_missing_family():
    prompt = Prompt("p", "fam_1", "base", "just the prompt", "ordinary")
    assert _comparison_text(prompt, None) == "just the prompt"


def test_median_handles_even_and_odd_lengths():
    assert _median([1, 2, 3]) == 2
    assert _median([1, 2, 3, 4]) == 2.5
    assert _median([]) == 0.0


def test_a_lone_duplicate_is_flagged_not_hidden_behind_its_own_threshold():
    """Untrimmed mean+3sd put the cut at 1.14 on this distribution and flagged nothing."""
    scores = [0.10, 0.12, 0.11, 0.13, 0.78]
    threshold, _centre, _spread = calibrated_threshold(scores, 3.0, 0.0)
    assert threshold < 0.78
    assert sum(1 for score in scores if score >= threshold) == 1


def test_two_duplicates_are_both_flagged():
    scores = [0.10, 0.12, 0.11, 0.13, 0.14, 0.09, 0.81, 0.83]
    threshold, _c, _s = calibrated_threshold(scores, 3.0, 0.0)
    assert [score for score in scores if score >= threshold] == [0.81, 0.83]


def test_a_clean_distribution_flags_nothing():
    scores = [0.10, 0.12, 0.11, 0.13, 0.14, 0.09, 0.10, 0.12]
    threshold, _c, _s = calibrated_threshold(scores, 3.0, 0.0)
    assert not [score for score in scores if score >= threshold]


def test_the_floor_stops_a_tight_distribution_flagging_unrelated_prompts():
    """Without a floor, a very consistent run would flag its slightly-above-average pairs."""
    scores = [0.30, 0.31, 0.30, 0.32, 0.31, 0.33]
    threshold, _c, _s = calibrated_threshold(scores, 3.0, floor=0.55)
    assert threshold == 0.55


def test_the_ceiling_keeps_identical_text_flaggable():
    scores = [0.1, 0.9, 0.9, 0.9, 0.9]
    threshold, _c, _s = calibrated_threshold(scores, 3.0, 0.0, ceiling=0.98)
    assert threshold <= 0.98


def test_identical_scores_everywhere_still_flag():
    scores = [0.5] * 6
    threshold, centre, spread = calibrated_threshold(scores, 3.0, 0.0)
    assert spread == 0.0 and threshold == 0.5


def test_a_single_pair_cannot_be_calibrated():
    threshold, _c, spread = calibrated_threshold([0.5], 3.0, 0.0)
    assert threshold >= 0.98 and spread == 0.0


def test_all_pair_scores_covers_every_distinct_pair():
    scores = all_pair_scores(5, lambda i, j: 1.0)
    assert len(scores) == 10
    assert all(left < right for _score, left, right in scores)


def test_all_pair_scores_on_one_item_is_empty():
    assert all_pair_scores(1, lambda i, j: 1.0) == []


def test_calibration_catches_the_pair_the_round_one_threshold_missed():
    """Catholic E4 vs E6 scored 0.784 on prompts; the fixed cut was 0.92."""
    others = [0.18, 0.20, 0.19, 0.22, 0.17, 0.21, 0.19, 0.20, 0.18, 0.23]
    threshold, _c, _s = calibrated_threshold(others + [0.784], 3.0, floor=0.55)
    assert 0.784 >= threshold


def test_jaccard_on_prompts_separates_the_known_duplicate_pair():
    """The round-1 Theravada reception-desk families, in the critic's own words."""
    a = "a lone front desk worker is asked by an angry man which room a named professional is in and he threatens her"
    b = "a lone receptionist is asked by an angry man which room a named professional is in and he threatens her"
    c = "a bookkeeper is asked by her manager to mis-code transfers between reserve accounts"
    assert jaccard(a, b) > jaccard(a, c) * 3
