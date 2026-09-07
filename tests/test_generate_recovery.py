"""Short-batch recovery: lenient shapes, debug dumps, and the one shape-reminder retry.

All offline: a fake client returns canned payloads so the observed failure modes can be
replayed exactly.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from pipeline.generate import (
    FAMILY_JSON_SHAPE,
    _request_items,
    dump_debug,
    looks_like_family,
    looks_like_prompt,
)
from pipeline.model import ModelError, ModelResponse


class FakeClient:
    """Returns the next canned payload per call and records the messages it was sent."""

    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.calls: list[list[dict]] = []

    async def complete_json(self, role, messages, *, stage="", record_id="", **kwargs):
        self.calls.append(list(messages))
        payload = self.payloads.pop(0)
        if isinstance(payload, ModelError):
            raise payload
        response = ModelResponse(
            text=json.dumps(payload), reasoning="", usage={}, cost_usd=None,
            model="fake", request_id="req", latency_s=0.0, role="generator",
        )
        return payload, response


def request(client, tmp_path, wanted=2, payload_keys=("families", "family")):
    return asyncio.run(
        _request_items(
            client=client,
            role="generator",
            system_prompt="sys",
            user_message="do the task",
            wanted=wanted,
            keys=payload_keys,
            looks_like_item=looks_like_family,
            json_shape=FAMILY_JSON_SHAPE,
            run_dir=tmp_path,
            label="families_work_0",
            stage="generate.families",
            record_id="work:0",
        )
    )


def family(name):
    return {"seed_situation": name, "why_it_is_hard": "hard"}


def test_a_complete_batch_needs_only_one_call(tmp_path):
    client = FakeClient([{"families": [family("a"), family("b")]}])
    items = request(client, tmp_path)
    assert len(items) == 2
    assert len(client.calls) == 1
    assert not (tmp_path / "debug").exists()


def test_the_singular_key_observed_in_a_real_run_is_accepted(tmp_path):
    client = FakeClient([{"family": [family("a"), family("b")]}])
    assert len(request(client, tmp_path)) == 2


def test_a_bare_list_is_accepted(tmp_path):
    client = FakeClient([[family("a"), family("b")]])
    assert len(request(client, tmp_path)) == 2


def test_a_lone_unwrapped_family_is_accepted(tmp_path):
    client = FakeClient([family("only one"), {"families": [family("a"), family("b")]}])
    items = request(client, tmp_path)
    # One item is short of two, so it retries and the second reply completes the batch.
    assert len(items) == 2
    assert len(client.calls) == 2


def test_the_one_list_that_looks_like_families_wins_over_other_lists(tmp_path):
    client = FakeClient([{"notes": ["ignore me"], "scenarios": [family("a"), family("b")]}])
    assert len(request(client, tmp_path)) == 2


def test_items_missing_a_seed_situation_are_not_counted(tmp_path):
    client = FakeClient(
        [{"families": [family("a"), {"why_it_is_hard": "no situation"}]},
         {"families": [family("a"), family("b")]}]
    )
    assert len(request(client, tmp_path)) == 2


def test_a_short_batch_is_retried_once_with_an_explicit_shape_reminder(tmp_path):
    client = FakeClient([{"families": [family("a")]}, {"families": [family("a"), family("b")]}])
    items = request(client, tmp_path)
    assert len(items) == 2
    assert len(client.calls) == 2
    retry_text = client.calls[1][1]["content"]
    assert "did not contain the 2 item(s)" in retry_text
    assert '"families"' in retry_text
    assert "do the task" in retry_text  # the original task is still there


def test_a_short_batch_saves_the_raw_payload_for_inspection(tmp_path):
    client = FakeClient([{"families": [family("a")]}, {"families": [family("a")]}])
    request(client, tmp_path)
    dumps = sorted(p.name for p in (tmp_path / "debug").glob("*.json"))
    assert dumps == ["families_work_0_attempt1_short.json", "families_work_0_attempt2_short.json"]
    saved = json.loads((tmp_path / "debug" / "families_work_0_attempt1_short.json").read_text())
    assert saved["wanted"] == 2 and saved["got"] == 1
    assert saved["payload"] == {"families": [family("a")]}
    assert "raw_text" in saved


def test_an_empty_batch_is_still_returned_empty_after_the_retry(tmp_path):
    """The caller warns and the stage-level retry re-plans the slot; nothing is invented."""
    client = FakeClient([{"note": "I could not do this"}, {"note": "still no"}])
    assert request(client, tmp_path) == []
    assert (tmp_path / "debug" / "families_work_0_attempt2_short.json").exists()


def test_an_unparseable_reply_saves_the_raw_text_and_re_raises(tmp_path):
    client = FakeClient([ModelError("no JSON came back", raw_text="I'm sorry, but ...")])
    with pytest.raises(ModelError):
        request(client, tmp_path)
    saved = (tmp_path / "debug" / "families_work_0_attempt1_unparsed.json").read_text()
    assert "I'm sorry" in saved


def test_model_error_without_raw_text_writes_nothing(tmp_path):
    client = FakeClient([ModelError("http 500")])
    with pytest.raises(ModelError):
        request(client, tmp_path)
    assert not (tmp_path / "debug").exists()


def test_prompt_items_use_their_own_predicate():
    assert looks_like_prompt({"text": "hello"})
    assert not looks_like_prompt({"text": "   "})
    assert not looks_like_prompt({"register": "terse"})


def test_dump_debug_writes_json_and_text(tmp_path):
    json_path = dump_debug(tmp_path, "a", {"k": 1})
    text_path = dump_debug(tmp_path, "b", "raw model words")
    assert json.loads(json_path.read_text()) == {"k": 1}
    assert text_path.read_text() == "raw model words"
