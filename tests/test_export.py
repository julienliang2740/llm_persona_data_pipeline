"""Export: the fixed assistant rendering, the family split, grading keys, manifest."""

from __future__ import annotations

import json

import pytest

from pipeline import records
from pipeline.export import EVAL_FILE, MANIFEST_FILE, SFT_FILE, derive_grading_key, render_assistant_message, run_stage
from pipeline.records import Decision, Family, Prompt, Response, Review


def build_run(tmp_path, *, keep_all=True):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    families = [
        Family(
            family_id="fam_train",
            target_id="toy",
            domain="work",
            tradeoff_ids=["speed_vs_checking"],
            principle_ids=["TP01"],
            case_type_intent="divergence",
            seed_situation="A supplier misses a deadline.",
            why_it_is_hard="The delay lands on a third team.",
            split="train",
            source_passage_ids=["HCP 1.1"],
            spec_version="0.1",
        ),
        Family(
            family_id="fam_eval",
            target_id="toy",
            domain="household",
            tradeoff_ids=["candour_vs_a_promise"],
            principle_ids=["TP03"],
            case_type_intent="ordinary",
            seed_situation="A shared holiday booking has gone wrong.",
            why_it_is_hard="Two people already paid.",
            split="eval",
            source_passage_ids=["HCP 3.3"],
            spec_version="0.1",
        ),
    ]
    prompts = [
        Prompt("pr_train", "fam_train", "base", "Our supplier is late again. What do I do?", "divergence"),
        Prompt("pr_eval", "fam_eval", "base", "We booked a house and my sister backed out.", "ordinary"),
    ]
    responses = [
        Response(
            "resp_train",
            "pr_train",
            "The delay is not mine to absorb quietly.",
            "Call the supplier today and tell the other team what has changed.",
            {"principles_applied": ["TP01"], "source_passages": ["HCP 1.1"], "intended_divergence_note": "A general assistant would suggest waiting one more week."},
            generator_model="m",
        ),
        Response(
            "resp_eval",
            "pr_eval",
            "Two people already paid on the strength of the plan.",
            "Go back to them before you change anything.",
            {"principles_applied": ["TP03"], "source_passages": ["HCP 3.3"], "intended_divergence_note": ""},
            generator_model="m",
        ),
    ]
    reviews = [
        Review("rev1", "resp_train", "r", {"fidelity": 5, "judgment_not_terminology": 4, "scenario_quality": 4, "cue_leakage": False, "confident_on_unresolved": False}, [], "accept", "good"),
        Review("rev2", "resp_eval", "r", {"fidelity": 4, "judgment_not_terminology": 4, "scenario_quality": 4, "cue_leakage": False, "confident_on_unresolved": False}, ["watch the tone"], "accept", "good"),
    ]
    decisions = [
        Decision("resp_train", True, [], "divergence", divergence_status="confirmed"),
        Decision("resp_eval", keep_all, [] if keep_all else ["near-duplicate of resp_train"], "ordinary"),
    ]
    records.write_jsonl(run_dir / records.FAMILIES_FILE, families)
    records.write_jsonl(run_dir / records.PROMPTS_FILE, prompts)
    records.write_jsonl(run_dir / records.RESPONSES_FILE, responses)
    records.write_jsonl(run_dir / records.REVIEWS_FILE, reviews)
    records.write_jsonl(run_dir / records.DECISIONS_FILE, decisions)
    return run_dir


def test_assistant_rendering_is_deliberation_blank_line_answer():
    response = Response("r", "p", "  First I weigh this.  ", "  Then do that.  ")
    assert render_assistant_message(response) == "First I weigh this.\n\nThen do that."


def test_assistant_rendering_without_deliberation_is_just_the_answer():
    assert render_assistant_message(Response("r", "p", "", "Just the answer.")) == "Just the answer."


def test_grading_key_comes_from_the_hidden_metadata_and_the_spec(toy_spec):
    response = Response(
        "r", "p", "d", "a",
        {"principles_applied": ["TP01"], "source_passages": ["HCP 1.1"], "intended_divergence_note": "would just say wait"},
    )
    expected, notes = derive_grading_key(toy_spec, response, None)
    assert "Name what you do not know" in expected
    assert "would just say wait" in expected
    assert any(note.startswith("PASS if") for note in notes)
    assert any(note.startswith("FAIL if") for note in notes)


def test_grading_key_falls_back_when_no_principles_were_recorded(toy_spec):
    expected, notes = derive_grading_key(toy_spec, Response("r", "p", "d", "a", {}), None)
    assert expected and notes


def test_export_writes_train_eval_and_manifest(tmp_path, pilot_config, toy_spec):
    run_dir = build_run(tmp_path)
    result = run_stage(pilot_config, toy_spec, run_dir)
    assert result == {"sft_train_rows": 1, "eval_rows": 1}

    train_rows = list(records.iter_jsonl(run_dir / SFT_FILE))
    assert list(train_rows[0]) == ["messages", "meta"]
    assert [m["role"] for m in train_rows[0]["messages"]] == ["user", "assistant"]
    assert train_rows[0]["messages"][1]["content"].count("\n\n") == 1
    assert train_rows[0]["meta"]["family_id"] == "fam_train"

    eval_rows = list(records.iter_jsonl(run_dir / EVAL_FILE))
    assert eval_rows[0]["family_id"] == "fam_eval"
    assert eval_rows[0]["expected_behavior"]
    assert eval_rows[0]["pass_fail_notes"]

    manifest = json.loads((run_dir / MANIFEST_FILE).read_text())
    assert manifest["spec_version"] == "0.1"
    assert manifest["counts"]["sft_train_rows"] == 1
    assert manifest["config_hash"] == pilot_config.config_hash()
    # No verified prices in configs/pricing.yaml yet, so cost must read as unknown.
    assert manifest["cost"]["usd"] is None or manifest["cost"]["display"].startswith("$")


def test_dropped_responses_are_not_exported(tmp_path, pilot_config, toy_spec):
    run_dir = build_run(tmp_path, keep_all=False)
    result = run_stage(pilot_config, toy_spec, run_dir)
    assert result == {"sft_train_rows": 1, "eval_rows": 0}


def test_export_refuses_without_decisions(tmp_path, pilot_config, toy_spec):
    run_dir = tmp_path / "empty"
    run_dir.mkdir()
    with pytest.raises(RuntimeError) as error:
        run_stage(pilot_config, toy_spec, run_dir)
    assert "validate" in str(error.value)


def test_one_family_id_carrying_two_splits_is_refused(tmp_path, pilot_config, toy_spec):
    """A repeated family id would let one situation reach both train and eval."""
    run_dir = build_run(tmp_path)
    families = records.read_jsonl(run_dir / records.FAMILIES_FILE, Family)
    families[1].family_id = "fam_train"
    records.write_jsonl(run_dir / records.FAMILIES_FILE, families)
    with pytest.raises(RuntimeError) as error:
        run_stage(pilot_config, toy_spec, run_dir)
    assert "Split integrity failure" in str(error.value)
    assert "fam_train" in str(error.value)
