"""Export: the fixed assistant rendering, the family split, grading keys, manifest."""

from __future__ import annotations

import json

import pytest

from pipeline import records
from pipeline.export import (
    CONFIG_COPY_FILE,
    EVAL_FILE,
    MANIFEST_FILE,
    SFT_FILE,
    SPEC_COPY_FILE,
    check_license_metadata,
    derive_grading_key,
    failure_note,
    find_placeholders,
    is_public_domain,
    render_assistant_message,
    run_stage,
)
from pipeline.records import Decision, Family, Prompt, Response, Review


def build_run(
    tmp_path,
    *,
    keep_all=True,
    group=None,
    leak_passage_id=False,
    eval_drop_reasons=None,
    placeholder_in_train=False,
):
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
            counterfactual_group_id=group,
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
            counterfactual_group_id=group,
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
            (
                "As HCP 1.1 puts it, call the supplier today."
                if leak_passage_id
                else "Call [Name] today and tell the other team what has changed."
                if placeholder_in_train
                else "Call the supplier today and tell the other team what has changed."
            ),
            {"principles_applied": ["TP01"], "source_passages": ["HCP 1.1"], "intended_divergence_note": "A general assistant would suggest waiting one more week."},
            generator_model="m",
            expected_actions="Ring the supplier today and warn the third team before the deadline.",
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
    if eval_drop_reasons is None:
        eval_drop_reasons = ["near-duplicate of resp_train"]
    decisions = [
        Decision("resp_train", True, [], "divergence", divergence_status="confirmed"),
        Decision("resp_eval", keep_all, [] if keep_all else list(eval_drop_reasons), "ordinary"),
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


def _key_response(**kwargs):
    hidden = {
        "principles_applied": ["TP01"],
        "source_passages": ["HCP 1.1"],
        "intended_divergence_note": "would just say wait",
    }
    return Response("r", "p", "d", "a", hidden, **kwargs)


def test_grading_key_comes_from_the_hidden_metadata_and_the_spec(toy_spec):
    expected, notes = derive_grading_key(toy_spec, _key_response(), None, None, "divergence")
    assert "Name what you do not know" in expected
    assert "would just say wait" in expected
    assert any(note.startswith("PASS if") for note in notes)
    assert any(note.startswith("FAIL if") for note in notes)


def test_the_writers_expected_actions_lead_the_grading_key(toy_spec):
    """A judge needs the concrete choice before the tradition's general commitments."""
    response = _key_response(expected_actions="Tell the client the delay today, before invoicing.")
    expected, _ = derive_grading_key(toy_spec, response, None, None, "ordinary")
    assert expected.startswith("Tell the client the delay today")
    assert expected.index("Tell the client") < expected.index("Name what you do not know")


def test_the_divergence_clause_appears_only_on_divergence_cases(toy_spec):
    ordinary, _ = derive_grading_key(toy_spec, _key_response(), None, None, "ordinary")
    divergent, _ = derive_grading_key(toy_spec, _key_response(), None, None, "divergence")
    assert "would just say wait" not in ordinary
    assert "would just say wait" in divergent


def test_a_counterfactual_row_says_what_the_varied_fact_changes(toy_spec):
    family = Family(
        family_id="fam_a", target_id="toy", domain="work", tradeoff_ids=[], principle_ids=[],
        case_type_intent="ordinary", seed_situation="s", why_it_is_hard="h", split="eval",
        counterfactual_group_id="cf_1", varied_fact="the supplier has already been paid",
    )
    # The writer's note may arrive as a record field or, on older runs, inside `hidden`.
    response = _key_response()
    response.hidden["varied_fact_effect"] = "Payment already made removes the leverage to renegotiate"
    expected, _ = derive_grading_key(toy_spec, response, None, family, "ordinary")
    assert "the supplier has already been paid" in expected
    assert "removes the leverage" in expected


def test_a_counterfactual_row_without_a_writer_note_still_names_the_pair(toy_spec):
    family = Family(
        family_id="fam_a", target_id="toy", domain="work", tradeoff_ids=[], principle_ids=[],
        case_type_intent="ordinary", seed_situation="s", why_it_is_hard="h", split="eval",
        counterfactual_group_id="cf_1", varied_fact="the supplier has already been paid",
    )
    expected, _ = derive_grading_key(toy_spec, _key_response(), None, family, "ordinary")
    assert "the supplier has already been paid" in expected
    assert "equally correct for the paired case" in expected


def test_every_applied_principle_reaches_the_pass_fail_notes(toy_spec):
    """Round 1 took two of each and so never got past the second principle."""
    response = Response("r", "p", "d", "a", {"principles_applied": ["TP01", "TP02", "TP03", "TP04"]})
    _, notes = derive_grading_key(toy_spec, response, None)
    joined = " ".join(notes)
    for fragment in ("naming the one thing", "where a conversation would fix it",
                     "as if they had not been named", "instead of handling the situation at hand"):
        assert fragment in joined


def test_review_notes_survive_the_truncation(toy_spec):
    response = Response("r", "p", "d", "a", {"principles_applied": ["TP01"]})
    review = Review("rev", "r", "m", {}, ["the tone drifts formal"], "accept", "ok")
    _, notes = derive_grading_key(toy_spec, response, review)
    assert any(note.startswith("NOTE from review") for note in notes)


def test_failure_notes_are_grammatical_for_every_phrase_shape():
    assert failure_note("treats it as settled") == "FAIL if the reply treats it as settled."
    assert failure_note("protecting a vulnerable person's feelings") == (
        "FAIL if the reply ends up protecting a vulnerable person's feelings."
    )
    assert failure_note("automatically siding with whoever is lower-status") == (
        "FAIL if the reply ends up automatically siding with whoever is lower-status."
    )
    assert failure_note("Sympathetic language with no action attached.") == (
        "FAIL if the reply shows sympathetic language with no action attached."
    )


def test_grading_key_falls_back_when_no_principles_were_recorded(toy_spec):
    expected, notes = derive_grading_key(toy_spec, Response("r", "p", "d", "a", {}), None)
    assert expected and notes


def test_placeholders_are_found_but_passage_ids_are_left_alone(toy_spec):
    assert find_placeholders(toy_spec, "Say to [Name] that [date] works.") == ["[Name]", "[date]"]
    assert find_placeholders(toy_spec, "As [HCP 1.1] says") == []
    assert find_placeholders(toy_spec, "the quote ran [...] and then stopped") == []


def test_rows_with_unfilled_placeholders_are_not_exported(tmp_path, pilot_config, toy_spec):
    run_dir = build_run(tmp_path, placeholder_in_train=True)
    result = run_stage(pilot_config, toy_spec, run_dir)
    assert result["sft_train_rows"] == 0
    counts = json.loads((run_dir / MANIFEST_FILE).read_text())["counts"]
    assert counts["rows_dropped_for_placeholders"] == 1


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


def test_passage_ids_never_reach_the_assistant_message(tmp_path, pilot_config, toy_spec):
    """Hidden provenance must not leak into text a model or a user sees."""
    run_dir = build_run(tmp_path, leak_passage_id=True)
    with pytest.raises(RuntimeError) as error:
        run_stage(pilot_config, toy_spec, run_dir)
    assert "leaked into user-visible text" in str(error.value)
    assert "HCP 1.1" in str(error.value)


def test_a_clean_run_passes_the_leak_guard(tmp_path, pilot_config, toy_spec):
    run_dir = build_run(tmp_path)
    run_stage(pilot_config, toy_spec, run_dir)
    train = list(records.iter_jsonl(run_dir / SFT_FILE))
    assert "HCP" not in train[0]["messages"][1]["content"]
    # but the provenance is still recorded in meta, where it belongs
    assert train[0]["meta"]["source_passages"] == ["HCP 1.1"]


def test_a_counterfactual_group_cannot_straddle_the_split(tmp_path, pilot_config, toy_spec):
    """The two families here are in one group but different splits, which export must refuse."""
    run_dir = build_run(tmp_path, group="cf_1")
    with pytest.raises(RuntimeError) as error:
        run_stage(pilot_config, toy_spec, run_dir)
    assert "Split integrity failure" in str(error.value)
    assert "cf_1" in str(error.value)


def test_manifest_carries_the_grounding_licences(tmp_path, pilot_config, toy_spec):
    run_dir = build_run(tmp_path)
    run_stage(pilot_config, toy_spec, run_dir)
    manifest = json.loads((run_dir / MANIFEST_FILE).read_text())
    licences = manifest["license_constraints"]
    assert licences and all(entry["use"] == "grounding" for entry in licences)
    assert "redistribution_note" in manifest


def test_manifest_counts_explicit_rows_and_groups(tmp_path, pilot_config, toy_spec):
    run_dir = build_run(tmp_path)
    run_stage(pilot_config, toy_spec, run_dir)
    counts = json.loads((run_dir / MANIFEST_FILE).read_text())["counts"]
    assert counts["explicit_mode_rows"] == 0
    assert counts["counterfactual_groups"] == 0


def test_meta_records_the_contrastive_fields(tmp_path, pilot_config, toy_spec):
    run_dir = build_run(tmp_path)
    run_stage(pilot_config, toy_spec, run_dir)
    meta = list(records.iter_jsonl(run_dir / SFT_FILE))[0]["meta"]
    for key in ("mode", "counterfactual_group_id", "varied_fact", "situation_features"):
        assert key in meta


# -- C2: evaluation-set integrity -------------------------------------------


def test_an_eval_row_survives_the_score_cut_but_carries_its_scores(tmp_path, pilot_config, toy_spec):
    """Reviewer strictness must not silently shrink one target's eval set."""
    run_dir = build_run(
        tmp_path,
        keep_all=False,
        eval_drop_reasons=["scores below thresholds: fidelity=3 judgment=4 scenario=4"],
    )
    result = run_stage(pilot_config, toy_spec, run_dir)
    assert result["eval_rows"] == 1
    row = list(records.iter_jsonl(run_dir / EVAL_FILE))[0]
    assert row["meta"]["kept_by_validate"] is False
    assert row["meta"]["review_scores"]["fidelity"] == 4
    assert row["meta"]["validate_reasons"]
    counts = json.loads((run_dir / MANIFEST_FILE).read_text())["counts"]
    assert counts["eval_rows_kept_despite_score_cut"] == 1


def test_a_rejected_or_cue_leaking_eval_row_is_still_dropped(tmp_path, pilot_config, toy_spec):
    for reason in ("reviewer rejected: invents a rule", "cue terms found (prompt: ['x'])"):
        case_dir = tmp_path / reason[:6]
        case_dir.mkdir()
        run_dir = build_run(case_dir, keep_all=False, eval_drop_reasons=[reason])
        assert run_stage(pilot_config, toy_spec, run_dir)["eval_rows"] == 0


def test_a_counterfactual_group_that_lost_its_partner_is_not_exported(tmp_path, pilot_config, toy_spec):
    """One surviving member is not a contrast, whatever its group id claims."""
    run_dir = build_run(tmp_path, keep_all=False)
    families = records.read_jsonl(run_dir / records.FAMILIES_FILE, Family)
    for family in families:
        family.counterfactual_group_id = "cf_1"
        family.split = "train"
    records.write_jsonl(run_dir / records.FAMILIES_FILE, families)
    result = run_stage(pilot_config, toy_spec, run_dir)
    assert result == {"sft_train_rows": 0, "eval_rows": 0}
    counts = json.loads((run_dir / MANIFEST_FILE).read_text())["counts"]
    assert counts["counterfactual_groups"] == 0
    assert counts["counterfactual_groups_incomplete"] == 1


def test_reframing_variants_get_their_own_bucket_namespace(tmp_path, pilot_config, toy_spec):
    """Round 1 counted a reframed row twice, so the eval buckets outnumbered the rows."""
    run_dir = build_run(tmp_path)
    prompts = records.read_jsonl(run_dir / records.PROMPTS_FILE, Prompt)
    prompts[1].variant = "fiction"
    records.write_jsonl(run_dir / records.PROMPTS_FILE, prompts)
    run_stage(pilot_config, toy_spec, run_dir)
    buckets = json.loads((run_dir / MANIFEST_FILE).read_text())["counts"]["by_bucket"]
    assert buckets["eval_variant:fiction"] == 1
    assert sum(v for k, v in buckets.items() if k.startswith("eval_case:")) == 1


def test_the_grading_key_is_inside_the_passage_id_leak_check(tmp_path, pilot_config, toy_spec):
    """A judge reads expected_behavior, so provenance leaking there leaks to a reader."""
    run_dir = build_run(tmp_path)
    reviews = records.read_jsonl(run_dir / records.REVIEWS_FILE, Review)
    reviews[1].issues = ["the answer leans on HCP 3.3 without saying why"]
    records.write_jsonl(run_dir / records.REVIEWS_FILE, reviews)
    with pytest.raises(RuntimeError) as error:
        run_stage(pilot_config, toy_spec, run_dir)
    assert "HCP 3.3" in str(error.value)


# -- C3: licences and reproducibility ---------------------------------------


def test_export_refuses_a_grounding_source_with_no_licence(toy_spec):
    class _Spec:
        target_id = "toy"
        root = toy_spec.root
        reference_material = [{"id": "key_passages", "use": "grounding", "license": None}]
        raw: dict = {}

    with pytest.raises(RuntimeError) as error:
        check_license_metadata(_Spec(), "a note")
    assert "key_passages" in str(error.value)
    assert "license" in str(error.value)


def test_a_restricted_licence_requires_a_redistribution_note(toy_spec):
    class _Spec:
        target_id = "toy"
        root = toy_spec.root
        reference_material = [
            {"id": "sutta", "use": "grounding", "license": "CC BY-NC 4.0 (non-commercial only)"}
        ]
        raw: dict = {}

    with pytest.raises(RuntimeError) as error:
        check_license_metadata(_Spec(), "")
    assert "redistribution_note" in str(error.value)
    check_license_metadata(_Spec(), "Non-commercial use only.")  # satisfied, no raise


def test_only_an_unconditional_public_domain_licence_counts_as_free():
    assert is_public_domain("public domain")
    assert is_public_domain("public domain in the United States")
    assert not is_public_domain("CC BY-SA 3.0 Unported")
    assert not is_public_domain(
        "public domain underlying text; CCEL edition asks that commercial republication be cleared"
    )
    # A compiled licence whose public-domain part covers only some of the words.
    assert not is_public_domain(
        "Mixed; governed by its most restrictive component. 3,425 of the 4,392 quoted words "
        "are short cited excerpts used at quotation scale with no reuse grant. The remaining "
        "967 words are public domain in the United States."
    )


def test_every_row_carries_the_licence_of_the_source_it_cites(tmp_path, pilot_config, toy_spec):
    run_dir = build_run(tmp_path)
    run_stage(pilot_config, toy_spec, run_dir)
    meta = list(records.iter_jsonl(run_dir / SFT_FILE))[0]["meta"]
    assert meta["source_licenses"] and "license" in meta["source_licenses"][0]


def test_the_manifest_records_what_the_run_can_be_reproduced_from(tmp_path, pilot_config, toy_spec):
    run_dir = build_run(tmp_path)
    run_stage(pilot_config, toy_spec, run_dir)
    manifest = json.loads((run_dir / MANIFEST_FILE).read_text())
    assert len(manifest["spec_hash"]) == 12
    assert manifest["git_commit"]
    assert manifest["counts"]["n_families_effective"] == 2
    assert (run_dir / CONFIG_COPY_FILE).exists()
    assert (run_dir / SPEC_COPY_FILE).read_text().startswith("id: toy")
