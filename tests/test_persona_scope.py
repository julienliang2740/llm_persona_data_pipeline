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
    ["Adolf Hitler", "adolf hitler", "ADOLF  HITLER!", "Ādolf Hitler", "Hitler, Adolf"],
)
def test_spelling_variants_still_match(scope, subject):
    """Normalisation is the only thing standing between the tripwire and a trivial evasion."""
    assert scope.tripwire_match(subject) is not None


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
    message = scope.refusal_message("Adolf Hitler", needle, why)
    assert "not a filter" in message and "scope_check" in message
