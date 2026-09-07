"""Record IO: dataclasses round-trip through JSONL and unknown keys are tolerated."""

from __future__ import annotations

import pytest

from pipeline import records
from pipeline.records import Decision, Family, Prompt, Response, read_jsonl, short_id, write_jsonl


def make_family(**overrides) -> Family:
    values = dict(
        family_id="fam_1",
        target_id="toy",
        domain="work",
        tradeoff_ids=["speed_vs_checking"],
        principle_ids=["TP01"],
        case_type_intent="divergence",
        seed_situation="A supplier misses a deadline.",
        why_it_is_hard="The delay lands on a third team.",
        split="train",
        source_passage_ids=["HCP 1.1"],
        generator_model="m",
        spec_version="0.1",
    )
    values.update(overrides)
    return Family(**values)


def test_round_trip(tmp_path):
    path = tmp_path / "families.jsonl"
    originals = [make_family(), make_family(family_id="fam_2", split="eval")]
    assert write_jsonl(path, originals) == 2
    loaded = read_jsonl(path, Family)
    assert loaded == originals


def test_unknown_columns_are_dropped_so_old_runs_still_load(tmp_path):
    path = tmp_path / "prompts.jsonl"
    path.write_text(
        '{"prompt_id":"p1","family_id":"f1","variant":"base","text":"hi",'
        '"case_type":"ordinary","field_from_a_future_version":42}\n',
        encoding="utf-8",
    )
    prompts = read_jsonl(path, Prompt)
    assert prompts[0].prompt_id == "p1"


def test_malformed_line_names_the_file_and_line(tmp_path):
    path = tmp_path / "responses.jsonl"
    path.write_text('{"a": 1}\nnot json\n', encoding="utf-8")
    with pytest.raises(ValueError) as error:
        read_jsonl(path, Response)
    assert "responses.jsonl:2" in str(error.value)


def test_missing_file_reads_as_empty(tmp_path):
    assert read_jsonl(tmp_path / "nothing.jsonl", Decision) == []


def test_short_id_is_deterministic_and_prefixed():
    first = short_id("fam", "toy", "work", "A supplier misses a deadline.")
    second = short_id("fam", "toy", "work", "A supplier misses a deadline.")
    other = short_id("fam", "toy", "work", "Something else entirely.")
    assert first == second and first != other
    assert first.startswith("fam_")


def test_append_then_read(tmp_path):
    path = tmp_path / "usage.jsonl"
    records.append_jsonl(path, {"a": 1})
    records.append_jsonl(path, {"a": 2})
    assert [row["a"] for row in records.iter_jsonl(path)] == [1, 2]
