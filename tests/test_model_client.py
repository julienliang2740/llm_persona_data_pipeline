"""ModelClient behaviour that does not need the network: usage ledger, cost, retries."""

from __future__ import annotations

import json

import pytest

from pipeline.config import ModelRole
from pipeline.model import (
    MAX_REASONING_RETRY_TOKENS,
    ModelClient,
    ModelError,
    format_cost,
    price_call,
    summarise_usage,
)

PRICING = {
    "big-model": {"input_per_1m_usd": 2.0, "output_per_1m_usd": 6.0},
    "free-model": {"input_per_1m_usd": 0.0, "output_per_1m_usd": 0.0},
    "unpriced-model": {"input_per_1m_usd": None, "output_per_1m_usd": None},
}


def test_price_call_uses_input_and_output_rates():
    assert price_call(PRICING, "big-model", 1_000_000, 1_000_000) == pytest.approx(8.0)


def test_price_call_matches_on_the_bare_model_name():
    assert price_call(PRICING, "accounts/x/models/big-model", 1_000_000, 0) == pytest.approx(2.0)


def test_price_call_returns_none_for_an_unknown_or_null_price():
    assert price_call(PRICING, "never-heard-of-it", 100, 100) is None
    assert price_call(PRICING, "unpriced-model", 100, 100) is None


def write_usage(path, entries):
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")


def test_summarise_recosts_entries_priced_after_the_run(tmp_path):
    """The ledger records cost at call time; a price filled in later must still apply."""
    path = tmp_path / "usage.jsonl"
    write_usage(
        path,
        [
            {"stage": "generate", "model": "big-model", "prompt_tokens": 1_000_000,
             "completion_tokens": 0, "cost_usd": None},
        ],
    )
    without = summarise_usage(path)
    assert without["cost_known"] is False
    with_prices = summarise_usage(path, PRICING)
    assert with_prices["cost_known"] is True
    assert with_prices["cost_usd"] == pytest.approx(2.0)


def test_one_unpriced_model_makes_the_whole_total_unknown(tmp_path):
    path = tmp_path / "usage.jsonl"
    write_usage(
        path,
        [
            {"stage": "a", "model": "big-model", "prompt_tokens": 1000, "completion_tokens": 0,
             "cost_usd": 0.002},
            {"stage": "b", "model": "never-heard-of-it", "prompt_tokens": 1000,
             "completion_tokens": 0, "cost_usd": None},
        ],
    )
    totals = summarise_usage(path, PRICING)
    assert totals["cost_known"] is False
    assert totals["unpriced_models"] == ["never-heard-of-it"]
    display = format_cost(totals)
    assert display.startswith("unknown (at least $")
    assert "never-heard-of-it" in display


def test_format_cost_shows_a_number_only_when_everything_is_priced():
    assert format_cost({"cost_known": True, "cost_usd": 1.5}) == "$1.5000"
    assert format_cost({"cost_known": False, "priced_calls": 0}) == "unknown."


def test_a_free_local_model_is_priced_not_unknown(tmp_path):
    path = tmp_path / "usage.jsonl"
    write_usage(
        path,
        [{"stage": "baseline", "model": "free-model", "prompt_tokens": 500,
          "completion_tokens": 500, "cost_usd": None}],
    )
    totals = summarise_usage(path, PRICING)
    assert totals["cost_known"] is True and totals["cost_usd"] == 0.0


def test_usage_ledger_accumulates_by_stage_and_model(tmp_path):
    path = tmp_path / "usage.jsonl"
    write_usage(
        path,
        [
            {"stage": "generate", "model": "big-model", "prompt_tokens": 10,
             "completion_tokens": 20, "reasoning_tokens": 15, "cost_usd": 0.1},
            {"stage": "validate", "model": "big-model", "prompt_tokens": 5,
             "completion_tokens": 5, "reasoning_tokens": 2, "cost_usd": 0.05},
        ],
    )
    totals = summarise_usage(path)
    assert totals["calls"] == 2
    assert totals["reasoning_tokens"] == 17
    assert totals["by_stage"]["generate"]["calls"] == 1
    assert totals["by_model"]["big-model"]["calls"] == 2


def test_missing_usage_file_reports_unknown(tmp_path):
    totals = summarise_usage(tmp_path / "nothing.jsonl")
    assert totals["calls"] == 0 and totals["cost_known"] is False


def test_semaphore_is_shared_per_endpoint_not_per_role():
    """Two roles on the same model must not each get full concurrency."""
    role_a = ModelRole(name="reviewer", model="m", max_concurrency=3)
    role_b = ModelRole(name="judge", model="m", max_concurrency=3)
    client = ModelClient({"reviewer": role_a, "judge": role_b})
    assert client._semaphore(role_a) is client._semaphore(role_b)


def test_a_different_model_gets_its_own_semaphore():
    role_a = ModelRole(name="generator", model="m1")
    role_b = ModelRole(name="reviewer", model="m2")
    client = ModelClient({"generator": role_a, "reviewer": role_b})
    assert client._semaphore(role_a) is not client._semaphore(role_b)


def test_resolving_an_unknown_role_lists_the_known_ones():
    client = ModelClient({"generator": ModelRole(name="generator", model="m")})
    with pytest.raises(ModelError) as error:
        client._resolve("nope")
    assert "generator" in str(error.value)


def test_the_reasoning_retry_ceiling_is_above_the_configured_budgets():
    """The auto-retry doubles max_tokens once; the cap must leave room to do that."""
    import yaml

    config = yaml.safe_load(open("configs/pilot.yaml", encoding="utf-8"))
    for name, role in config["models"].items():
        budget = role.get("max_tokens", 0)
        if budget:
            assert budget <= MAX_REASONING_RETRY_TOKENS, name
