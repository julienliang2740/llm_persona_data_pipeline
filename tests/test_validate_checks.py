"""The pure validation checks: cue terms, near-duplicates, leakage, decisions."""

from __future__ import annotations

from pipeline.validate import (
    cosine,
    find_cue_hits,
    find_near_duplicates,
    jaccard,
    max_leakage,
    tokenize,
)

TERMS = ["Confucius", "ren", "the Analects", "junzi"]


def test_cue_hit_is_case_insensitive():
    assert find_cue_hits("What would CONFUCIUS say?", TERMS) == ["Confucius"]


def test_cue_hit_respects_word_boundaries():
    # "ren" must not fire inside "children", "current" or "parent".
    text = "My children are the current parents of a rented flat."
    assert find_cue_hits(text, TERMS) == []
    assert find_cue_hits("The idea of ren matters here.", TERMS) == ["ren"]


def test_multi_word_terms_match_as_phrases():
    assert find_cue_hits("I read the Analects last year.", TERMS) == ["the Analects"]
    assert find_cue_hits("the book of analects-adjacent essays", TERMS) == []


def test_several_hits_are_all_reported():
    hits = find_cue_hits("Confucius on ren, per the Analects.", TERMS)
    assert set(hits) == {"Confucius", "ren", "the Analects"}


def test_empty_and_blank_terms_are_ignored():
    assert find_cue_hits("anything", ["", "   "]) == []


def test_jaccard_bounds():
    assert jaccard("a b c", "a b c") == 1.0
    assert jaccard("a b c", "x y z") == 0.0
    assert 0 < jaccard("a b c d", "a b x y") < 1


def test_tokenize_lowercases_and_keeps_apostrophes():
    assert tokenize("Don't Panic, now.") == {"don't", "panic", "now"}


def test_cosine_of_identical_and_orthogonal_vectors():
    assert cosine([1.0, 0.0], [2.0, 0.0]) == 1.0
    assert cosine([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_near_duplicate_clustering_keeps_the_first_and_flags_later_copies():
    texts = [
        "my manager keeps changing the delivery date without telling the warehouse",
        "my manager keeps changing the delivery date and never tells the warehouse",
        "our neighbour has left the shared bins blocking the alley for a month",
    ]
    ids = ["r1", "r2", "r3"]
    duplicate_of, clusters = find_near_duplicates(
        ids, lambda i, j: jaccard(texts[i], texts[j]), threshold=0.6
    )
    assert duplicate_of == {"r2": "r1"}
    assert len(clusters) == 1
    assert clusters[0].representative_id == "r1"
    assert set(clusters[0].member_ids) == {"r1", "r2"}


def test_nothing_is_a_duplicate_below_the_threshold():
    texts = ["completely different one", "entirely unrelated other"]
    duplicate_of, clusters = find_near_duplicates(
        ["a", "b"], lambda i, j: jaccard(texts[i], texts[j]), threshold=0.9
    )
    assert duplicate_of == {} and clusters == []


def test_leakage_finds_the_closest_training_item():
    texts = [
        "eval: a junior nurse is asked to sign off on a colleague's late paperwork",
        "train: a junior nurse is asked to sign off a colleague's late paperwork today",
        "train: a builder disputes an invoice with a supplier",
    ]
    scores = max_leakage([0], [1, 2], lambda i, j: jaccard(texts[i], texts[j]))
    best_score, best_index = scores[0]
    assert best_index == 1
    assert best_score > 0.6


def test_leakage_is_zero_without_training_items():
    assert max_leakage([0], [], lambda i, j: 1.0) == {0: (0.0, None)}


def test_same_family_items_use_the_higher_within_family_threshold():
    """Prompts inside one family are meant to be close; only a verbatim repeat is a defect."""
    texts = [
        "my manager keeps changing the delivery date without telling the warehouse",
        "my manager keeps changing the delivery date and never tells the warehouse",
        "our neighbour has left the shared bins blocking the alley for a month",
    ]
    ids = ["r1", "r2", "r3"]
    families = ["fam_a", "fam_a", "fam_b"]
    duplicate_of, _ = find_near_duplicates(
        ids,
        lambda i, j: jaccard(texts[i], texts[j]),
        threshold=0.6,
        group_ids=families,
        within_group_threshold=0.99,
    )
    assert duplicate_of == {}


def test_a_verbatim_repeat_inside_a_family_is_still_caught():
    texts = ["exactly the same words here", "exactly the same words here"]
    duplicate_of, _ = find_near_duplicates(
        ["r1", "r2"],
        lambda i, j: jaccard(texts[i], texts[j]),
        threshold=0.6,
        group_ids=["fam_a", "fam_a"],
        within_group_threshold=0.99,
    )
    assert duplicate_of == {"r2": "r1"}


def test_cross_family_duplicates_are_still_caught_when_grouping_is_on():
    texts = [
        "my manager keeps changing the delivery date without telling the warehouse",
        "my manager keeps changing the delivery date and never tells the warehouse",
    ]
    duplicate_of, _ = find_near_duplicates(
        ["r1", "r2"],
        lambda i, j: jaccard(texts[i], texts[j]),
        threshold=0.6,
        group_ids=["fam_a", "fam_b"],
        within_group_threshold=0.99,
    )
    assert duplicate_of == {"r2": "r1"}


def test_without_a_within_group_threshold_same_family_pairs_are_skipped():
    texts = ["identical text", "identical text"]
    duplicate_of, _ = find_near_duplicates(
        ["r1", "r2"], lambda i, j: jaccard(texts[i], texts[j]), 0.5, group_ids=["f", "f"]
    )
    assert duplicate_of == {}


def test_counterfactual_group_members_are_never_deduped():
    """Two members of a contrastive pair are near-identical on purpose."""
    texts = [
        "my colleague took 200 pounds from petty cash and put it back the next day",
        "my colleague took 2000 pounds from petty cash and has not put it back",
    ]
    duplicate_of, clusters = find_near_duplicates(
        ["r1", "r2"],
        lambda i, j: 0.99,
        threshold=0.9,
        group_ids=["fam_a", "fam_b"],
        within_group_threshold=0.99,
        never_compare_ids=["cf_1", "cf_1"],
    )
    assert duplicate_of == {} and clusters == []


def test_items_in_different_counterfactual_groups_are_still_compared():
    duplicate_of, _ = find_near_duplicates(
        ["r1", "r2"],
        lambda i, j: 0.99,
        threshold=0.9,
        group_ids=["fam_a", "fam_b"],
        never_compare_ids=["cf_1", "cf_2"],
    )
    assert duplicate_of == {"r2": "r1"}


def test_an_item_with_no_group_is_compared_normally():
    duplicate_of, _ = find_near_duplicates(
        ["r1", "r2"],
        lambda i, j: 0.99,
        threshold=0.9,
        group_ids=["fam_a", "fam_b"],
        never_compare_ids=[None, None],
    )
    assert duplicate_of == {"r2": "r1"}
