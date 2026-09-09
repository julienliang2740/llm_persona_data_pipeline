"""The scope tripwire: a cheap stop, and honest about being only that.

`scope.py` carries the argument for why this axis exists at all. These tests pin the two
properties that matter operationally: trivial spelling variants still match, and the drafter
stops before it spends anything.
"""

from __future__ import annotations

import sys

import pytest

from tests.conftest import REPO_ROOT

GENERALIZER = REPO_ROOT / "persona_generalizer"


@pytest.fixture(scope="module")
def scope():
    if str(GENERALIZER) not in sys.path:
        sys.path.insert(0, str(GENERALIZER))
    import scope as module

    return module


@pytest.mark.parametrize(
    "subject",
    ["Ada Quill", "ada quill", "ADA  QUILL!", "Ãda Quill", "Quill, Ada", "Ada M. Quill (1801-1870)"],
)
def test_spelling_variants_still_match(scope, subject, monkeypatch):
    """Normalisation is the only thing standing between the tripwire and a trivial evasion.

    Exercised against a synthetic entry rather than a real one, so the test pins the matching
    behaviour rather than the contents of the list. The cases that matter are the ones that broke
    it: an inverted "surname, forename" as a catalogue writes it, accents, stray punctuation, and
    extra words around the name.
    """
    monkeypatch.setattr(scope, "TRIPWIRE", (("ada quill", "synthetic entry for this test"),))
    assert scope.tripwire_match(subject) is not None


def test_an_unrelated_subject_sharing_one_token_does_not_match(scope, monkeypatch):
    """All tokens must be present, or a shared surname would trip the gate on the wrong person."""
    monkeypatch.setattr(scope, "TRIPWIRE", (("ada quill", "synthetic entry for this test"),))
    assert scope.tripwire_match("Beatrix Quill") is None
    assert scope.tripwire_match("Ada Lovelace") is None


@pytest.mark.parametrize(
    "subject",
    ["Lyndon B. Johnson", "Basil II", "Michael Psellos", "Julian", "Anna Komnene"],
)
def test_in_scope_subjects_do_not_match(scope, subject):
    assert scope.tripwire_match(subject) is None


def test_every_tripwire_entry_carries_a_reason(scope):
    """A list of names with no reasons is an editorial judgement nobody can review."""
    for needle, why in scope.TRIPWIRE:
        assert needle == needle.lower() and len(why.split()) >= 4, needle


def test_the_refusal_message_says_it_is_not_a_filter(scope):
    """The limits have to travel with the refusal, or the list gets mistaken for a policy."""
    needle, why = scope.TRIPWIRE[0]
    message = scope.refusal_message("A Subject", needle, why)
    assert "not a filter" in message and "scope_check" in message
