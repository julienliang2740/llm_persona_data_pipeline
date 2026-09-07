"""The run report and the before/after table. All offline.

Coverage-plan tests live in tests/test_plan_invariants.py and
tests/test_generate_planning.py.
"""

from __future__ import annotations

from collections import Counter

from pipeline import records
from pipeline.evaluate import before_after_table
from pipeline.records import write_jsonl
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
