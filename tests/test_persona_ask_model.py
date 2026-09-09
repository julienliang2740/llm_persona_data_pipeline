"""The bridge that lets the skill arm delegate one pass to a non-Claude model.

No network: these pin the argument handling and the role guard, which is the part carrying a
design decision rather than plumbing.
"""

from __future__ import annotations

import sys

import pytest

from tests.conftest import REPO_ROOT

GENERALIZER = REPO_ROOT / "persona_generalizer"


@pytest.fixture(scope="module")
def ask_model():
    if str(GENERALIZER) not in sys.path:
        sys.path.insert(0, str(GENERALIZER))
    import ask_model as module

    return module


def test_the_generator_role_is_refused_by_default(ask_model, capsys):
    """A check by the model that will later generate the rows measures nothing.

    In the pilot config `generator` is the same model the pipeline generates with, so allowing it
    as a second opinion would quietly produce self-agreement and call it corroboration.
    """
    assert ask_model.main(["--role", "generator", "--prompt", "hello"]) == 2
    assert "second-opinion set" in capsys.readouterr().err


def test_an_explicit_override_is_available(ask_model, monkeypatch):
    """The guard is a default, not a prohibition: a deliberate experiment can still run."""
    captured = {}

    async def fake_ask(prompt, **kwargs):
        captured.update(kwargs, prompt=prompt)
        return "ok", None

    monkeypatch.setattr(ask_model, "ask", fake_ask)
    assert ask_model.main(["--role", "generator", "--allow-any-role", "--prompt", "hi"]) == 0
    assert captured["role"] == "generator"


def test_an_empty_prompt_is_refused(ask_model, capsys):
    assert ask_model.main(["--role", "reviewer", "--prompt", "   "]) == 2
    assert "empty prompt" in capsys.readouterr().err


def test_second_opinion_roles_exclude_the_generator(ask_model):
    assert "generator" not in ask_model.SECOND_OPINION_ROLES
    assert set(ask_model.SECOND_OPINION_ROLES) == {"reviewer", "reviewer_second", "judge"}


def test_the_prompt_can_come_from_a_file(ask_model, tmp_path, monkeypatch):
    captured = {}

    async def fake_ask(prompt, **kwargs):
        captured["prompt"] = prompt
        return "ok", None

    monkeypatch.setattr(ask_model, "ask", fake_ask)
    path = tmp_path / "p.md"
    path.write_text("review these passages\n", encoding="utf-8")
    assert ask_model.main(["--role", "reviewer", "--prompt-file", str(path)]) == 0
    assert captured["prompt"] == "review these passages"
