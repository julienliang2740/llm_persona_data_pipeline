"""The round-2 report tables: house style, coverage, closest pairs, three-way divergence."""

from __future__ import annotations

import json

from pipeline import records
from pipeline.records import Decision, DivergenceVerdict, Family, Prompt
from pipeline.report_style import (
    SIMILARITY_FILE,
    coverage_tables,
    cross_run_style_table,
    latest_sibling_runs,
    presence_shares,
    three_way_divergence,
    top_similarity_pairs,
)


def write_responses(run_dir, texts):
    run_dir.mkdir(parents=True, exist_ok=True)
    records.write_jsonl(
        run_dir / records.RESPONSES_FILE,
        [{"response_id": f"r{i}", "deliberation": "", "answer": text} for i, text in enumerate(texts)],
    )
    return run_dir


def a_family(family_id, **kwargs):
    defaults = dict(
        target_id="toy", domain="work", tradeoff_ids=[], principle_ids=[],
        case_type_intent="ordinary", seed_situation="s", why_it_is_hard="h", split="train",
    )
    defaults.update(kwargs)
    return Family(family_id=family_id, **defaults)


# -- house style -------------------------------------------------------------


def test_presence_counts_an_answer_once_however_often_it_repeats_a_phrase():
    shares = presence_shares(["the hard part is the hard part is", "nothing in common at all"])
    assert shares["the hard part is"] == 0.5


def test_the_style_table_shows_a_phrase_both_targets_lean_on(tmp_path):
    shared = "the hard part is not the rule but the relationship"
    first = write_responses(tmp_path / "a" / "run", [shared, shared, "an unrelated sentence here"])
    second = write_responses(tmp_path / "b" / "run", [shared, "another unrelated sentence here"])
    table = "\n".join(cross_run_style_table({"a": first, "b": second}))
    assert "| the hard part is | 2 |" in table
    assert "mean pairwise overlap" in table


def test_a_phrase_only_one_target_uses_is_marked_as_one_target(tmp_path):
    first = write_responses(tmp_path / "a" / "run", ["only this target says this phrase"] * 3)
    second = write_responses(tmp_path / "b" / "run", ["a completely different set of words"] * 3)
    table = "\n".join(cross_run_style_table({"a": first, "b": second}))
    assert "| only this target says | 1 |" in table


def test_the_latest_run_of_every_target_is_found(tmp_path):
    runs = tmp_path / "runs"
    write_responses(runs / "alpha" / "20260101-000000", ["old"])
    write_responses(runs / "alpha" / "20260202-000000", ["new"])
    write_responses(runs / "beta" / "20260101-000000", ["only"])
    (runs / "gamma" / "20260101-000000").mkdir(parents=True)  # no responses, so no run
    found = latest_sibling_runs(runs / "alpha" / "20260202-000000")
    assert found["alpha"].name == "20260202-000000"
    assert set(found) == {"alpha", "beta"}


# -- coverage ----------------------------------------------------------------


def test_coverage_names_the_unresolved_tradeoffs_that_were_never_exercised(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "spec.yaml").write_text(
        json.dumps(
            {
                "tradeoffs": [
                    {"id": "speed_vs_checking"},
                    {"id": "candour_vs_a_promise", "unresolved": True},
                    {"id": "mercy_vs_order", "unresolved": True},
                ],
                "divergence_hypotheses": [{"id": "h1"}, {"id": "h2"}],
            }
        ),
        encoding="utf-8",
    )
    families = [
        a_family("f1", tradeoff_ids=["speed_vs_checking"]),
        a_family("f2", tradeoff_ids=["candour_vs_a_promise"]),
    ]
    text = "\n".join(coverage_tables(run_dir, families, []))
    assert "candour_vs_a_promise (unresolved)" in text
    assert "2 of 3 spec tradeoffs reached" in text
    assert "`mercy_vs_order`" in text
    assert "`h1`, `h2`" in text  # neither hypothesis has a family


def test_coverage_flags_a_tradeoff_id_the_spec_does_not_define(tmp_path):
    """A corrupt id renders as no tradeoff at all in the response prompt, so it must show."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "spec.yaml").write_text(
        json.dumps({"tradeoffs": [{"id": "speed_vs_checking"}]}), encoding="utf-8"
    )
    families = [a_family("f1", tradeoff_ids=["f orgiveness_vs_protection"])]
    text = "\n".join(coverage_tables(run_dir, families, []))
    assert "does not define: `f orgiveness_vs_protection`" in text


def test_coverage_reports_asker_stance_and_the_eval_mix(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    records.write_jsonl(
        run_dir / "eval.jsonl",
        [{"case_type": "ordinary", "variant": "base"}, {"case_type": "ordinary", "variant": "fiction"}],
    )
    families = [
        a_family("f1", split="eval", case_type_intent="divergence", asker_stance="defensive"),
        a_family("f2", split="train", asker_stance="conflicted"),
    ]
    text = "\n".join(coverage_tables(run_dir, families, []))
    assert "| defensive | 1 |" in text
    assert "| divergence | 1 | 0 |" in text  # planned a divergence family, exported none
    assert "base ×1, fiction ×1" in text


# -- closest pairs and three-way divergence ----------------------------------


CALIBRATION = {"statistic": "median + 3 x robust_sd", "centre": 0.19, "spread": 0.04, "sigmas": 3}


def test_the_closest_pairs_table_is_read_from_the_similarity_file(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    records.write_jsonl(
        run_dir / SIMILARITY_FILE,
        [
            {"kind": "dedupe", "a_id": "pr_a", "b_id": "pr_b", "score": 0.784, "method": "jaccard",
             "flagged": True, "threshold": 0.31, "calibration": CALIBRATION},
            {"kind": "dedupe", "a_id": "pr_e", "b_id": "pr_f", "score": 0.21, "method": "jaccard",
             "flagged": False, "threshold": 0.31, "calibration": CALIBRATION},
            {"kind": "leakage", "a_id": "pr_c", "b_id": "pr_d", "score": 0.19, "method": "jaccard",
             "flagged": False, "threshold": 0.4, "calibration": CALIBRATION},
        ],
    )
    text = "\n".join(top_similarity_pairs(run_dir, []))
    assert "0.784" in text
    assert text.index("0.784") < text.index("0.210")  # ranked, highest first
    assert text.index("(dedupe)") < text.index("(leakage)")


def test_the_pairs_table_states_the_cut_the_way_validate_computed_it(tmp_path):
    """The statistic is read off the row, never assumed: it is not mean plus three sd."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    records.write_jsonl(
        run_dir / SIMILARITY_FILE,
        [{"kind": "dedupe", "a_id": "a", "b_id": "b", "score": 0.5, "method": "jaccard",
          "flagged": True, "threshold": 0.31, "calibration": CALIBRATION}],
    )
    text = "\n".join(top_similarity_pairs(run_dir, []))
    assert "median + 3 x robust_sd" in text
    assert "0.310" in text
    assert "centre 0.190, spread 0.040" in text


def test_without_the_similarity_file_the_report_says_what_is_missing(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    decisions = [Decision("r1", True, max_leakage=0.4)]
    text = "\n".join(top_similarity_pairs(run_dir, decisions))
    assert SIMILARITY_FILE in text
    assert "1 scored eval responses" in text


def test_a_verdict_predating_the_three_way_judge_reads_as_not_recorded():
    """Round-1 verdicts leave every three-way field at its default, which is not a finding."""
    verdicts = [DivergenceVerdict("p1", "m", True, "action", "because")]
    prompts = {"p1": Prompt("p1", "fam_1", "base", "t", "divergence")}
    text = "\n".join(three_way_divergence(verdicts, prompts))
    assert "| candidate vs 7B base | 1 | 100% |" in text
    assert "| candidate vs strong generic | not recorded | - |" in text
    assert "| strong generic vs 7B base | not recorded | - |" in text


def test_three_way_rates_are_counted_per_family_not_per_prompt():
    verdicts = [
        DivergenceVerdict("p1", "m", True, "action", "x", divergence_source="value"),
        DivergenceVerdict("p2", "m", True, "action", "x", divergence_source="value"),
        DivergenceVerdict("p3", "m", False, "none", "x", divergence_source="none"),
    ]
    prompts = {
        "p1": Prompt("p1", "fam_1", "base", "t", "divergence"),
        "p2": Prompt("p2", "fam_1", "fiction", "t", "divergence"),
        "p3": Prompt("p3", "fam_2", "base", "t", "divergence"),
    }
    text = "\n".join(three_way_divergence(verdicts, prompts))
    assert "2 families with a judged prompt" in text
    assert "| candidate vs 7B base | 1 | 50% |" in text
    assert "**1** (50%)" in text  # value-attributed


def test_closer_to_stands_in_for_a_missing_generic_flag():
    verdicts = [DivergenceVerdict("p1", "m", True, "action", "x", closer_to="generic")]
    prompts = {"p1": Prompt("p1", "fam_1", "base", "t", "divergence")}
    text = "\n".join(three_way_divergence(verdicts, prompts))
    assert "| candidate vs strong generic | 0 | 0% |" in text


def test_the_stance_table_shows_the_planned_mix_next_to_the_realised_one(tmp_path):
    """A run of nothing but conflicted askers is the failure mode the mix exists to catch."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    families = [a_family(f"f{i}", asker_stance="conflicted") for i in range(4)]
    text = "\n".join(coverage_tables(run_dir, families, []))
    assert "| conflicted | 4 | 100% | 40% |" in text
    assert "| transactional | 0 | 0% | 10% |" in text
