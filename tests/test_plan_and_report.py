"""The run report and the before/after table. All offline.

Coverage-plan tests live in tests/test_plan_invariants.py and
tests/test_generate_planning.py.
"""

from __future__ import annotations

from collections import Counter

from pipeline import records
from pipeline.evaluate import before_after_table
from pipeline.records import Review, write_jsonl
from pipeline.report import build_report
from tests.test_export import build_run

SETTINGS = {
    "divergence_fraction": 0.4,
    "eval_family_fraction": 0.25,
    "reserved_family_fraction": 0.0,
}


def test_report_summarises_a_run(tmp_path, pilot_config, toy_spec):
    from pipeline.export import run_stage as export_stage

    run_dir = build_run(tmp_path)
    export_stage(pilot_config, toy_spec, run_dir)
    text = build_report(run_dir, "toy")
    assert "# Run report: toy" in text
    assert "## Accept / reject" in text
    assert "## Divergence from the baseline" in text
    assert "## Cost and usage" in text
    # No pricing is verified yet, so the cost line must say so rather than show a number.
    assert "unknown" in text
    assert "configs/pricing.yaml" not in text or "No price" in text
    assert "resp_train" in text


def test_report_lists_rejection_reasons(tmp_path, pilot_config, toy_spec):
    from pipeline.export import run_stage as export_stage

    run_dir = build_run(tmp_path, keep_all=False)
    export_stage(pilot_config, toy_spec, run_dir)
    text = build_report(run_dir, "toy")
    assert "near-duplicate of" in text
    assert "## Samples rejected" in text


def test_before_after_table(tmp_path):
    before = tmp_path / "eval_results_before.jsonl"
    after = tmp_path / "eval_results_after.jsonl"
    def row(prompt_id, case_type, passed, model="base", rationale=""):
        return {
            "prompt_id": prompt_id,
            "family_id": "f" + prompt_id,
            "case_type": case_type,
            "variant": "base",
            "model": model,
            "text": "an answer",
            "judge": {"pass": passed, "rationale": rationale},
        }

    write_jsonl(before, [row("p1", "divergence", False), row("p2", "ordinary", True)])
    write_jsonl(
        after,
        [
            row("p1", "divergence", True, "tuned"),
            row("p2", "ordinary", False, "tuned", "lost the point"),
        ],
    )
    table = before_after_table(before, after)
    assert "| divergence | 1 | 0 | 1 | +1 |" in table
    assert "| ordinary | 1 | 1 | 0 | -1 |" in table
    assert "Newly passing: 1" in table
    assert "regression `p2`" in table


def test_before_after_with_no_shared_prompts(tmp_path):
    before = tmp_path / "a.jsonl"
    after = tmp_path / "b.jsonl"
    write_jsonl(before, [{"prompt_id": "p1", "case_type": "ordinary", "judge": {"pass": True}}])
    write_jsonl(after, [{"prompt_id": "p9", "case_type": "ordinary", "judge": {"pass": True}}])
    assert "No prompts in common" in before_after_table(before, after)


def test_report_separates_action_and_reasons_divergence(tmp_path, pilot_config, toy_spec):
    """Divergence in the reasons alone counts fully and is reported on its own line."""
    from pipeline import records
    from pipeline.records import Decision

    run_dir = build_run(tmp_path)
    records.write_jsonl(
        run_dir / records.DECISIONS_FILE,
        [
            Decision("resp_train", True, [], "divergence",
                     divergence_status="confirmed", divergence_kind="reasons"),
            Decision("resp_eval", True, [], "divergence",
                     divergence_status="confirmed", divergence_kind="action"),
        ],
    )
    text = build_report(run_dir, "toy")
    assert "reasons alone counts as divergence" in text
    assert "| reasons only | 1 |" in text
    assert "| action (incl. both) | 1 |" in text


def test_report_shows_soft_cue_and_licensing_flags(tmp_path, pilot_config, toy_spec):
    from pipeline import records
    from pipeline.records import Decision, Review

    run_dir = build_run(tmp_path)
    records.write_jsonl(
        run_dir / records.DECISIONS_FILE,
        [Decision("resp_train", True, ["note: soft cue terms present: ['prudence']"],
                  "ordinary", soft_cue_hits=["prudence"])],
    )
    records.write_jsonl(
        run_dir / records.REVIEWS_FILE,
        [Review("rev1", "resp_train", "r",
                {"fidelity": 4, "judgment_not_terminology": 4, "scenario_quality": 4,
                 "cue_leakage": False, "confident_on_unresolved": False,
                 "quoted_source_text": True, "archaic_register": True},
                [], "accept", "ok")],
    )
    text = build_report(run_dir, "toy")
    assert "Soft cue terms (flagged, never a reason to drop): **1**" in text
    assert "prudence ×1" in text
    assert "quoted or echoed source wording: **1**" in text
    assert "archaic or translated-sounding register: **1**" in text


def test_report_lists_families_reserved_by_the_avoid_screen(tmp_path, pilot_config, toy_spec):
    from pipeline import records
    from pipeline.records import Family

    run_dir = build_run(tmp_path)
    families = records.read_jsonl(run_dir / records.FAMILIES_FILE, Family)
    families[0].split = "reserved"
    families[0].reserved_reason = "avoided-topic keyword in seed situation: probate"
    records.write_jsonl(run_dir / records.FAMILIES_FILE, families)
    text = build_report(run_dir, "toy")
    assert "reserved by the avoided-topic screen: **1**" in text
    assert "probate" in text


def test_before_after_breaks_the_change_down_by_prompt_variant(tmp_path):
    """A gain confined to `base` is a gain on the training situations, not the target."""
    before = tmp_path / "eval_results_before.jsonl"
    after = tmp_path / "eval_results_after.jsonl"

    def row(prompt_id, variant, passed):
        return {
            "prompt_id": prompt_id,
            "family_id": "f" + prompt_id,
            "case_type": "ordinary",
            "variant": variant,
            "model": "m",
            "text": "an answer",
            "judge": {"pass": passed},
        }

    write_jsonl(before, [row("p1", "base", False), row("p2", "fiction", False)])
    write_jsonl(after, [row("p1", "base", True), row("p2", "fiction", False)])
    table = before_after_table(before, after)
    assert "| base | 1 | 0 | 1 | +1 |" in table
    assert "| fiction | 1 | 0 | 0 | +0 |" in table


def test_report_names_reviews_that_scored_five_while_raising_a_flag(tmp_path, pilot_config, toy_spec):
    """A reply cannot be an exemplar of the target's judgment and also carry a template shape."""
    run_dir = build_run(tmp_path)
    reviews = records.read_jsonl(run_dir / records.REVIEWS_FILE, records.Review)
    reviews[0].scores["fidelity"] = 5
    reviews[0].scores["formulaic_shape"] = True
    records.write_jsonl(run_dir / records.REVIEWS_FILE, reviews)
    text = build_report(run_dir, "toy")
    assert "Reviews awarding a 5 while raising a defect flag: **1** of 2" in text
    assert "formulaic_shape+fidelity=5 \u00d71" in text


def test_report_says_so_when_the_rubric_was_applied_consistently(tmp_path, pilot_config, toy_spec):
    """build_run's reviews raise no flags, so the line has to read as a clean bill."""
    text = build_report(build_run(tmp_path), "toy")
    assert "**0** of 2" in text
    assert "rubric was applied consistently" in text


# -- second-reviewer agreement -------------------------------------------------


def a_review(response_id, verdict="accept", rationale="", model="primary-model", **scores):
    base = {"fidelity": 5, "judgment_not_terminology": 5, "scenario_quality": 5}
    base.update(scores)
    return Review(f"rev_{response_id}", response_id, model, base, [], verdict, rationale)


def fixture_pair():
    """Two reviewers over four responses, with the answer worked out by hand.

    primary scores every dimension 5. Second scores:
      fidelity                 [5, 4, 4, 4] -> mean 4.25, exact 1/4, within 1 4/4
      judgment_not_terminology [5, 4, 3, 3] -> mean 3.75, exact 1/4, within 1 2/4
      scenario_quality         [5, 5, 5, 5] -> mean 5.00, exact 4/4, within 1 4/4
    Verdicts agree on 3 of 4; the second reviewer rejects r3.
    """
    primary = [a_review(f"r{i}") for i in range(4)]
    second = [
        a_review("r0", model="second-model", fidelity=5, judgment_not_terminology=5),
        a_review("r1", model="second-model", fidelity=4, judgment_not_terminology=4),
        a_review("r2", model="second-model", fidelity=4, judgment_not_terminology=3),
        a_review("r3", verdict="reject", rationale="generic advice", model="second-model",
                 fidelity=4, judgment_not_terminology=3),
    ]
    return primary, second


def test_agreement_table_reports_means_and_match_counts():
    from pipeline.report import _second_reviewer_agreement

    text = "\n".join(_second_reviewer_agreement(*fixture_pair()))
    assert "| fidelity | 5.00 | 4.25 | 1/4 | 4/4 |" in text
    # within-1 is 2/4 here, not 4/4: two of the four differ by two points, which is
    # the case the "within 1" column exists to separate from near-agreement.
    assert "| judgment_not_terminology | 5.00 | 3.75 | 1/4 | 2/4 |" in text
    assert "| scenario_quality | 5.00 | 5.00 | 4/4 | 4/4 |" in text


def test_agreement_reports_verdicts_and_the_second_histogram():
    from pipeline.report import _second_reviewer_agreement

    text = "\n".join(_second_reviewer_agreement(*fixture_pair()))
    assert "Verdicts agree on **3/4**" in text
    assert "accept ×3" in text and "reject ×1" in text


def test_agreement_names_both_models_and_the_shared_count():
    from pipeline.report import _second_reviewer_agreement

    text = "\n".join(_second_reviewer_agreement(*fixture_pair()))
    assert "`primary-model` (primary) against `second-model` (second)" in text
    assert "over the 4 responses both scored" in text


def test_a_verdict_disagreement_is_listed_with_its_rationale():
    from pipeline.report import _second_reviewer_agreement

    text = "\n".join(_second_reviewer_agreement(*fixture_pair()))
    assert "`r3`: primary said accept, second said reject" in text
    assert "generic advice" in text


def test_no_second_reviewer_renders_nothing():
    from pipeline.report import _second_reviewer_agreement

    primary, _second = fixture_pair()
    assert _second_reviewer_agreement(primary, []) == []


def test_only_responses_both_reviewers_scored_are_compared():
    from pipeline.report import _second_reviewer_agreement

    primary, second = fixture_pair()
    text = "\n".join(_second_reviewer_agreement(primary, second[:2]))
    assert "over the 2 responses both scored" in text
    assert "| fidelity | 5.00 | 4.50 | 1/2 | 2/2 |" in text


def test_a_second_reviewer_covering_nothing_says_so():
    from pipeline.report import _second_reviewer_agreement

    primary, _second = fixture_pair()
    stranger = [a_review("unrelated", model="second-model")]
    text = "\n".join(_second_reviewer_agreement(primary, stranger))
    assert "nothing to compare" in text


def test_a_missing_score_does_not_crash_the_table():
    from pipeline.records import Review
    from pipeline.report import _second_reviewer_agreement

    primary = [a_review("r0")]
    second = [Review("rev", "r0", "second-model", {"fidelity": 4}, [], "accept", "")]
    text = "\n".join(_second_reviewer_agreement(primary, second))
    assert "| fidelity | 5.00 | 4.00 | 0/1 | 1/1 |" in text
    assert "| judgment_not_terminology | 5.00 | 0.00 | 0/1 | 0/1 |" in text


def test_the_report_includes_the_agreement_section_when_the_file_exists(
    tmp_path, pilot_config, toy_spec
):
    from pipeline import records
    from pipeline.export import run_stage as export_stage
    from pipeline.report import build_report

    run_dir = build_run(tmp_path)
    export_stage(pilot_config, toy_spec, run_dir)
    existing = records.read_jsonl(run_dir / records.REVIEWS_FILE, Review)
    second = [
        Review(f"s_{r.response_id}", r.response_id, "second-model",
               dict(r.scores, fidelity=3), [], "revise", "not specific enough")
        for r in existing
    ]
    records.write_jsonl(run_dir / records.REVIEWS_SECOND_FILE, second)
    text = build_report(run_dir, "toy")
    assert "## Second reviewer" in text
    assert "second-model" in text
    assert "Verdicts agree on **0/" in text


def test_the_report_omits_the_section_without_a_second_reviewer(
    tmp_path, pilot_config, toy_spec
):
    from pipeline.export import run_stage as export_stage
    from pipeline.report import build_report

    run_dir = build_run(tmp_path)
    export_stage(pilot_config, toy_spec, run_dir)
    assert "## Second reviewer" not in build_report(run_dir, "toy")
