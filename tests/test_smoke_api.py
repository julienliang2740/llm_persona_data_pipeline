"""Real API calls, one per model role. Tiny on purpose: the account is rate-limited.

Run with:  .venv/bin/pytest tests/test_smoke_api.py -m smoke -q
Skipped automatically when fireworks_api_key.txt is absent.
"""

from __future__ import annotations

import pytest

from pipeline.config import REPO_ROOT, load_config
from pipeline.model import ModelClient
from pipeline.similarity import cosine

pytestmark = [
    pytest.mark.smoke,
    pytest.mark.skipif(
        not (REPO_ROOT / "fireworks_api_key.txt").exists(),
        reason="no fireworks_api_key.txt in the repo root",
    ),
    pytest.mark.asyncio,
]


@pytest.fixture
def config():
    return load_config("configs/pilot.yaml")


async def test_generator_answers_and_reports_usage(config):
    async with ModelClient.from_config(config, None, "smoke") as client:
        response = await client.complete(
            config.role("generator"),
            [{"role": "user", "content": "Reply with the single word: ok"}],
            temperature=0.0,
            max_tokens=600,  # reasoning tokens are drawn from this budget
        )
    assert "ok" in response.text.lower()
    assert response.usage["prompt_tokens"] > 0
    assert response.model == config.role("generator").model
    # Reasoning is kept apart from the answer and never treated as the answer.
    assert response.reasoning != response.text


async def test_reviewer_returns_parseable_json(config):
    async with ModelClient.from_config(config, None, "smoke") as client:
        payload, response = await client.complete_json(
            config.role("reviewer"),
            [
                {
                    "role": "user",
                    "content": 'Reply with JSON exactly: {"verdict": "accept", "score": 4}',
                }
            ],
            temperature=0.0,
            max_tokens=600,
        )
    assert payload["verdict"] == "accept"
    assert response.request_id


async def test_embeddings_endpoint_and_cosine(config):
    async with ModelClient.from_config(config, None, "smoke") as client:
        vectors = await client.embed(
            [
                "my manager keeps moving the deadline without telling the warehouse",
                "my manager keeps changing the delivery date and never tells the warehouse",
                "the recipe calls for two teaspoons of ground cinnamon",
            ],
            config.role("embeddings"),
        )
    assert len(vectors) == 3
    assert len(vectors[0]) > 100
    near = cosine(vectors[0], vectors[1])
    far = cosine(vectors[0], vectors[2])
    assert near > far
    assert near > 0.6


async def test_cost_follows_the_pricing_table(config):
    """A priced model yields a number; an unpriced one yields None, never a guess."""
    async with ModelClient.from_config(config, None, "smoke") as client:
        response = await client.complete(
            config.role("generator"),
            [{"role": "user", "content": "Reply with the single word: ok"}],
            temperature=0.0,
            max_tokens=600,
        )
    price = config.pricing.get(config.role("generator").model, {})
    if price.get("input_per_1m_usd") is None:
        assert response.cost_usd is None
    else:
        assert response.cost_usd is not None
