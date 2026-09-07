"""Lenient JSON extraction from model output."""

from __future__ import annotations

import pytest

from pipeline.model import parse_json_loosely


def test_plain_json():
    assert parse_json_loosely('{"a": 1}') == {"a": 1}


def test_fenced_json():
    assert parse_json_loosely('```json\n{"a": 1}\n```') == {"a": 1}


def test_fenced_without_language_tag():
    assert parse_json_loosely('```\n{"a": [1, 2]}\n```') == {"a": [1, 2]}


def test_prose_before_and_after():
    text = 'Sure, here you go:\n{"verdict": "accept"}\nLet me know if you need more.'
    assert parse_json_loosely(text) == {"verdict": "accept"}


def test_top_level_array():
    assert parse_json_loosely('Here:\n[{"a": 1}, {"a": 2}]') == [{"a": 1}, {"a": 2}]


def test_braces_inside_strings_do_not_break_balancing():
    text = 'note:\n{"answer": "use the {placeholder} form", "n": 1}\ndone'
    assert parse_json_loosely(text) == {"answer": "use the {placeholder} form", "n": 1}


def test_escaped_quote_inside_a_string():
    assert parse_json_loosely('{"a": "she said \\"no\\""}') == {"a": 'she said "no"'}


def test_trailing_comma_is_repaired():
    assert parse_json_loosely('{"a": 1, "b": [2, 3,],}') == {"a": 1, "b": [2, 3]}


def test_nested_objects_survive():
    text = 'x {"scores": {"fidelity": 4, "cue_leakage": false}, "issues": []} y'
    assert parse_json_loosely(text)["scores"]["fidelity"] == 4


def test_no_json_raises_with_a_preview():
    with pytest.raises(ValueError) as error:
        parse_json_loosely("I am afraid I cannot comply with that request.")
    assert "No JSON value found" in str(error.value)
    assert "I am afraid" in str(error.value)


def test_none_raises():
    with pytest.raises(ValueError):
        parse_json_loosely(None)  # type: ignore[arg-type]


def test_extract_list_prefers_the_expected_key():
    from pipeline.model import extract_list

    assert extract_list({"families": [1, 2], "note": "x"}, "families", "family") == [1, 2]


def test_extract_list_accepts_the_singular_key_the_generator_sometimes_uses():
    """Observed in a real run: the generator returned {"family": [...]}, silently losing a batch."""
    from pipeline.model import extract_list

    assert extract_list({"family": [1, 2]}, "families", "family") == [1, 2]


def test_extract_list_falls_back_to_the_only_list_value():
    from pipeline.model import extract_list

    assert extract_list({"scenarios": [1]}, "families") == [1]


def test_extract_list_takes_a_bare_list():
    from pipeline.model import extract_list

    assert extract_list([1, 2], "families") == [1, 2]


def test_extract_list_gives_up_when_two_lists_are_ambiguous():
    from pipeline.model import extract_list

    assert extract_list({"a": [1], "b": [2]}, "families") == []


def test_extract_field_prefers_then_falls_back():
    from pipeline.model import extract_field

    assert extract_field({"text": "a", "note": "b"}, "text") == "a"
    assert extract_field({"rewritten": "a"}, "text") == "a"
    assert extract_field({"a": "x", "b": "y"}, "text") == ""
    assert extract_field("plain", "text") == "plain"
