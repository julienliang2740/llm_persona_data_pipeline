"""Coverage planning, the run report, and the before/after table. All offline."""

from __future__ import annotations

from collections import Counter

from pipeline.evaluate import before_after_table
from pipeline.generate import plan_families
from pipeline.records import write_jsonl
from pipeline.report import build_report
from tests.test_export import build_run

SETTINGS = {
    "divergence_fraction": 0.4,
    "eval_family_fraction": 0.25,
    "reserved_family_fraction": 0.0,
}


def test_plan_allocates_every_family_and_respects_weights(toy_spec):
    slots = plan_families(toy_spec, SETTINGS, 20)
    assert len(slots) == 20
    by_domain = Counter(slot.domain for slot in slots)
    # The toy target weights work and household 0.5 / 0.5.
    assert by_domain["work"] == 10 and by_domain["household"] == 10


def test_plan_hits_the_requested_divergence_and_eval_shares(toy_spec):
    slots = plan_families(toy_spec, SETTINGS, 20)
    assert sum(1 for s in slots if s.case_type_intent == "divergence") == 8
    assert sum(1 for s in slots if s.split == "eval") == 5


def test_plan_spreads_eval_over_domains(toy_spec):
    slots = plan_families(toy_spec, SETTINGS, 20)
    eval_domains = {slot.domain for slot in slots if slot.split == "eval"}
    assert eval_domains == {"work", "household"}


def test_plan_covers_every_tradeoff_when_there_is_room(toy_spec):
    slots = plan_families(toy_spec, SETTINGS, 20)
    covered = {tid for slot in slots for tid in slot.tradeoff_ids}
    assert covered == {"speed_vs_checking", "candour_vs_a_promise"}


def test_plan_is_deterministic(toy_spec):
    first = plan_families(toy_spec, SETTINGS, 13)
    second = plan_families(toy_spec, SETTINGS, 13)
    assert [(s.domain, s.case_type_intent, s.split) for s in first] == [
        (s.domain, s.case_type_intent, s.split) for s in second
    ]


def test_tiny_plans_still_produce_one_eval_family(toy_spec):
    slots = plan_families(toy_spec, SETTINGS, 2)
    assert len(slots) == 2
    assert sum(1 for s in slots if s.split == "eval") == 1


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
    rows = [
        {"prompt_id": "p1", "family_id": "f1", "case_type": "divergence", "variant": "base", "model": "base", "pass": False, "rationale": ""},
        {"prompt_id": "p2", "family_id": "f2", "case_type": "ordinary", "variant": "base", "model": "base", "pass": True, "rationale": ""},
    ]
    write_jsonl(before, rows)
    write_jsonl(
        after,
        [
            dict(rows[0], model="tuned", **{"pass": True}),
            dict(rows[1], model="tuned", **{"pass": False, "rationale": "lost the point"}),
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
    write_jsonl(before, [{"prompt_id": "p1", "case_type": "ordinary", "pass": True}])
    write_jsonl(after, [{"prompt_id": "p9", "case_type": "ordinary", "pass": True}])
    assert "No prompts in common" in before_after_table(before, after)
