"""The only place in the pipeline that makes HTTP calls to a model.

Handles per-endpoint concurrency, retry with backoff, the usage/cost ledger, and
lenient JSON extraction with one model-based repair attempt. The same client
talks to Fireworks and to a local OpenAI-compatible llama-server.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Iterable, Sequence

import httpx

from pipeline.config import ModelRole, RunConfig, load_fireworks_api_key, redact

logger = logging.getLogger("pipeline.model")

RETRY_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}
MAX_ATTEMPTS = 6


class ModelError(Exception):
    """A model call failed after retries, or returned unusable output."""


class LocalEndpointUnavailable(ModelError):
    """The local base-model server is not reachable. Raised with a clear next step."""


@dataclass
class ModelResponse:
    text: str
    reasoning: str
    usage: dict[str, Any]
    cost_usd: float | None
    model: str
    request_id: str
    latency_s: float
    role: str
    finish_reason: str = ""

    @property
    def truncated(self) -> bool:
        return self.finish_reason == "length"


@dataclass
class UsageTotals:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    cost_usd: float = 0.0
    unpriced_calls: int = 0
    by_model: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def cost_is_complete(self) -> bool:
        return self.unpriced_calls == 0


def price_call(
    pricing: dict[str, Any], model: str, prompt_tokens: int, completion_tokens: int
) -> float | None:
    """USD for one call from the pricing table, or None when the model has no price.

    Cached-input discounts are ignored: every prompt token is charged at the full
    input rate, so the number is an upper bound rather than a guess downward.
    """
    price = pricing.get(model) or pricing.get(model.split("/")[-1])
    if not isinstance(price, dict):
        return None
    input_price = price.get("input_per_1m_usd")
    output_price = price.get("output_per_1m_usd")
    if input_price is None or output_price is None:
        return None
    return (prompt_tokens * float(input_price) + completion_tokens * float(output_price)) / 1e6


def parse_json_loosely(text: str) -> Any:
    """Extract a JSON value from model output that may be fenced or padded with prose.

    Tries the whole string, then a fenced block, then the first balanced {...} or [...].
    Raises ValueError if nothing parses.
    """
    if text is None:
        raise ValueError("No text to parse as JSON.")
    candidates: list[str] = []
    stripped = text.strip()
    if stripped:
        candidates.append(stripped)
    for match in re.finditer(r"```(?:json|JSON)?\s*(.*?)```", text, re.DOTALL):
        candidates.append(match.group(1).strip())
    # Prefer whichever balanced block starts earliest, so a top-level array is not
    # mistaken for the first object inside it.
    blocks = []
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        block = _first_balanced_block(text, opener, closer)
        if block:
            blocks.append((start, block))
    candidates.extend(block for _, block in sorted(blocks))
    for candidate in candidates:
        if not candidate:
            continue
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            repaired = _strip_trailing_commas(candidate)
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                continue
    preview = text.strip()[:300]
    raise ValueError(f"No JSON value found in model output. First 300 chars: {preview!r}")


def _first_balanced_block(text: str, opener: str, closer: str) -> str | None:
    """Return the first balanced opener..closer block, ignoring braces inside strings."""
    start = text.find(opener)
    if start == -1:
        return None
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def _strip_trailing_commas(text: str) -> str:
    return re.sub(r",(\s*[}\]])", r"\1", text)


class ModelClient:
    """Async client over one or more OpenAI-compatible endpoints."""

    def __init__(
        self,
        roles: dict[str, ModelRole],
        pricing: dict[str, Any] | None = None,
        usage_path: Path | None = None,
        api_key: str | None = None,
        stage: str = "",
    ) -> None:
        self.roles = roles
        self.pricing = pricing or {}
        self.usage_path = usage_path
        self.stage = stage
        self._api_key = api_key
        self._semaphores: dict[str, asyncio.Semaphore] = {}
        self._cooldown_until: dict[str, float] = {}
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=15.0))
        self.totals = UsageTotals()

    @classmethod
    def from_config(cls, config: RunConfig, usage_path: Path | None, stage: str = "") -> "ModelClient":
        needs_key = any(
            role.api_key_source == "fireworks" for role in config.roles.values() if role.enabled
        )
        api_key = load_fireworks_api_key() if needs_key else None
        return cls(config.roles, config.pricing, usage_path, api_key, stage)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "ModelClient":
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    # -- request plumbing -------------------------------------------------

    def _headers(self, role: ModelRole) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if role.api_key_source == "fireworks":
            if not self._api_key:
                raise ModelError(
                    f"Role '{role.name}' needs the Fireworks key but none was loaded."
                )
            headers["Authorization"] = f"Bearer {self._api_key}"
        elif role.api_key_source.startswith("env:"):
            import os

            name = role.api_key_source.split(":", 1)[1]
            value = os.environ.get(name)
            if not value:
                raise ModelError(f"Role '{role.name}' needs environment variable {name}.")
            headers["Authorization"] = f"Bearer {value}"
        return headers

    def _semaphore(self, role: ModelRole) -> asyncio.Semaphore:
        key = role.endpoint_key
        if key not in self._semaphores:
            self._semaphores[key] = asyncio.Semaphore(max(1, role.max_concurrency))
        return self._semaphores[key]

    def _safe(self, text: str) -> str:
        """Never let a secret reach a log line or an exception message."""
        return redact(text, [self._api_key or ""])

    async def _post(self, role: ModelRole, url: str, payload: dict[str, Any]) -> tuple[dict[str, Any], float]:
        """POST with retries. Holds the semaphore for the whole retry sequence."""
        semaphore = self._semaphore(role)
        last_error: str = ""
        async with semaphore:
            for attempt in range(1, MAX_ATTEMPTS + 1):
                cooldown = self._cooldown_until.get(role.endpoint_key, 0.0) - time.monotonic()
                if cooldown > 0:
                    # After a 429 every holder of this endpoint's semaphore waits,
                    # which lowers effective concurrency without a token bucket.
                    await asyncio.sleep(min(cooldown, 30.0))
                started = time.monotonic()
                try:
                    response = await self._client.post(
                        url,
                        headers=self._headers(role),
                        json=payload,
                        timeout=role.timeout_s,
                    )
                except httpx.ConnectError as error:
                    if _is_local(role.base_url):
                        raise LocalEndpointUnavailable(
                            f"Cannot reach the local model server at {role.base_url} "
                            f"(role '{role.name}'). Start llama-server, or run this stage "
                            f"with the role disabled."
                        ) from None
                    last_error = f"connect error: {self._safe(str(error))}"
                except (httpx.TimeoutException, httpx.RemoteProtocolError) as error:
                    last_error = f"{type(error).__name__}: {self._safe(str(error))}"
                else:
                    latency = time.monotonic() - started
                    if response.status_code == 200:
                        return response.json(), latency
                    body = self._safe(response.text[:400])
                    last_error = f"HTTP {response.status_code}: {body}"
                    if response.status_code == 429:
                        self._cooldown_until[role.endpoint_key] = time.monotonic() + min(
                            60.0, 2.0 * (2 ** (attempt - 1))
                        )
                    if response.status_code not in RETRY_STATUS:
                        raise ModelError(
                            f"{role.name} ({role.model}) call failed. {last_error}"
                        )
                if attempt == MAX_ATTEMPTS:
                    break
                delay = min(45.0, 1.5 * (2 ** (attempt - 1))) * (0.6 + 0.8 * random.random())
                logger.warning(
                    "%s attempt %d/%d failed (%s); retrying in %.1fs",
                    role.name,
                    attempt,
                    MAX_ATTEMPTS,
                    last_error[:160],
                    delay,
                )
                await asyncio.sleep(delay)
        raise ModelError(
            f"{role.name} ({role.model}) failed after {MAX_ATTEMPTS} attempts. Last error: {last_error}"
        )

    # -- public API -------------------------------------------------------

    async def complete(
        self,
        role: ModelRole | str,
        messages: Sequence[dict[str, str]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
        stage: str | None = None,
        record_id: str = "",
    ) -> ModelResponse:
        role = self._resolve(role)
        payload: dict[str, Any] = {
            "model": role.model,
            "messages": list(messages),
            "temperature": role.temperature if temperature is None else temperature,
            # Reasoning models spend part of this budget on reasoning_content,
            # so callers must leave headroom above the wanted answer length.
            "max_tokens": role.max_tokens if max_tokens is None else max_tokens,
        }
        if json_mode and role.supports_json_mode:
            payload["response_format"] = {"type": "json_object"}
        payload.update(role.extra_body)

        url = role.base_url.rstrip("/") + "/chat/completions"
        data, latency = await self._post(role, url, payload)
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        text = (message.get("content") or "").strip()
        reasoning = (message.get("reasoning_content") or "").strip()
        usage = data.get("usage") or {}
        result = ModelResponse(
            text=text,
            reasoning=reasoning,
            usage=usage,
            cost_usd=self._cost(role.model, usage),
            model=role.model,
            request_id=str(data.get("id", "")),
            latency_s=latency,
            role=role.name,
            finish_reason=str(choice.get("finish_reason") or ""),
        )
        self._record_usage(result, stage or self.stage, record_id)
        if not text and result.truncated:
            raise ModelError(
                f"{role.name} ({role.model}) returned only reasoning and hit the "
                f"max_tokens limit ({payload['max_tokens']}). Raise max_tokens for this role. "
                f"request_id={result.request_id}"
            )
        return result

    async def complete_json(
        self,
        role: ModelRole | str,
        messages: Sequence[dict[str, str]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stage: str | None = None,
        record_id: str = "",
    ) -> tuple[Any, ModelResponse]:
        """Ask for JSON, parse leniently, and make one model-based repair attempt."""
        role = self._resolve(role)
        response = await self.complete(
            role,
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
            stage=stage,
            record_id=record_id,
        )
        try:
            return parse_json_loosely(response.text), response
        except ValueError as first_error:
            repair_messages = list(messages) + [
                {"role": "assistant", "content": response.text[:4000]},
                {
                    "role": "user",
                    "content": (
                        "That was not valid JSON. Reply again with the same content as a "
                        "single JSON value and nothing else: no prose, no code fence."
                    ),
                },
            ]
            repaired = await self.complete(
                role,
                repair_messages,
                temperature=0.0,
                max_tokens=max_tokens,
                json_mode=True,
                stage=stage,
                record_id=record_id,
            )
            try:
                return parse_json_loosely(repaired.text), repaired
            except ValueError as second_error:
                raise ModelError(
                    f"{role.name} ({role.model}) did not return JSON after a repair retry. "
                    f"request_ids={response.request_id},{repaired.request_id}. "
                    f"First failure: {first_error}. Second: {second_error}"
                ) from None

    async def embed(
        self,
        texts: Sequence[str],
        role: ModelRole | str = "embeddings",
        *,
        batch_size: int = 16,
        stage: str | None = None,
    ) -> list[list[float]]:
        """Embed texts in batches. Returns one vector per input, in order."""
        role = self._resolve(role)
        url = role.base_url.rstrip("/") + "/embeddings"
        vectors: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = [t if t.strip() else "empty" for t in texts[start : start + batch_size]]
            data, latency = await self._post(role, url, {"model": role.model, "input": batch})
            rows = sorted(data.get("data", []), key=lambda row: row.get("index", 0))
            if len(rows) != len(batch):
                raise ModelError(
                    f"Embedding endpoint returned {len(rows)} vectors for {len(batch)} inputs."
                )
            vectors.extend([row["embedding"] for row in rows])
            usage = data.get("usage") or {}
            self._record_usage(
                ModelResponse(
                    text="",
                    reasoning="",
                    usage=usage,
                    cost_usd=self._cost(role.model, usage),
                    model=role.model,
                    request_id=str(data.get("id", "")),
                    latency_s=latency,
                    role=role.name,
                ),
                stage or self.stage,
                f"embed_batch_{start}",
            )
        return vectors

    def _resolve(self, role: ModelRole | str) -> ModelRole:
        if isinstance(role, ModelRole):
            return role
        if role not in self.roles:
            raise ModelError(f"No model role '{role}' in this config. Have: {sorted(self.roles)}")
        return self.roles[role]

    # -- usage ledger -----------------------------------------------------

    def _cost(self, model: str, usage: dict[str, Any]) -> float | None:
        """USD for one call, or None when the model has no verified price."""
        return price_call(
            self.pricing,
            model,
            usage.get("prompt_tokens", 0) or 0,
            usage.get("completion_tokens", 0) or 0,
        )

    def _record_usage(self, response: ModelResponse, stage: str, record_id: str) -> None:
        usage = response.usage or {}
        details = usage.get("completion_tokens_details") or {}
        reasoning_tokens = int(details.get("reasoning_tokens") or 0)
        entry = {
            "stage": stage,
            "role": response.role,
            "model": response.model,
            "record_id": record_id,
            "request_id": response.request_id,
            "prompt_tokens": int(usage.get("prompt_tokens") or 0),
            "completion_tokens": int(usage.get("completion_tokens") or 0),
            "reasoning_tokens": reasoning_tokens,
            "cost_usd": response.cost_usd,
            "latency_s": round(response.latency_s, 3),
            "finish_reason": response.finish_reason,
        }
        self.totals.calls += 1
        self.totals.prompt_tokens += entry["prompt_tokens"]
        self.totals.completion_tokens += entry["completion_tokens"]
        self.totals.reasoning_tokens += reasoning_tokens
        if response.cost_usd is None:
            self.totals.unpriced_calls += 1
        else:
            self.totals.cost_usd += response.cost_usd
        per_model = self.totals.by_model.setdefault(
            response.model,
            {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0, "priced": True},
        )
        per_model["calls"] += 1
        per_model["prompt_tokens"] += entry["prompt_tokens"]
        per_model["completion_tokens"] += entry["completion_tokens"]
        if response.cost_usd is None:
            per_model["priced"] = False
        else:
            per_model["cost_usd"] += response.cost_usd
        if self.usage_path is not None:
            self.usage_path.parent.mkdir(parents=True, exist_ok=True)
            with self.usage_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry) + "\n")


def _is_local(base_url: str) -> bool:
    return "127.0.0.1" in base_url or "localhost" in base_url or "0.0.0.0" in base_url


async def gather_bounded(coroutines: Iterable[Awaitable[Any]], *, return_exceptions: bool = True) -> list[Any]:
    """Run coroutines together. Per-endpoint concurrency is enforced by ModelClient."""
    return await asyncio.gather(*coroutines, return_exceptions=return_exceptions)


def summarise_usage(usage_path: Path, pricing: dict[str, Any] | None = None) -> dict[str, Any]:
    """Roll up runs/.../usage.jsonl for the run report and the manifest.

    Cost is written into the ledger at call time. When `pricing` is supplied, entries
    whose cost was null (the model had no verified price when the call was made) are
    recosted from the current table, so a run made before the prices were known can
    still be costed. Entries the table still cannot price stay unknown.
    """
    totals: dict[str, Any] = {
        "calls": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "reasoning_tokens": 0,
        "cost_usd": 0.0,
        "cost_known": True,
        "priced_calls": 0,
        "unpriced_models": [],
        "by_stage": {},
        "by_model": {},
    }
    if not usage_path.exists():
        totals["cost_known"] = False
        return totals
    unpriced: set[str] = set()
    for line in usage_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        totals["calls"] += 1
        for key in ("prompt_tokens", "completion_tokens", "reasoning_tokens"):
            totals[key] += entry.get(key, 0) or 0
        cost = entry.get("cost_usd")
        if cost is None and pricing:
            cost = price_call(
                pricing,
                entry.get("model", ""),
                entry.get("prompt_tokens", 0) or 0,
                entry.get("completion_tokens", 0) or 0,
            )
        if cost is None:
            totals["cost_known"] = False
            unpriced.add(entry.get("model", "?"))
        else:
            totals["cost_usd"] += cost
            totals["priced_calls"] += 1
        for bucket, name in (("by_stage", entry.get("stage", "")), ("by_model", entry.get("model", ""))):
            slot = totals[bucket].setdefault(
                name, {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0, "cost_known": True}
            )
            slot["calls"] += 1
            slot["prompt_tokens"] += entry.get("prompt_tokens", 0) or 0
            slot["completion_tokens"] += entry.get("completion_tokens", 0) or 0
            if cost is None:
                slot["cost_known"] = False
            else:
                slot["cost_usd"] += cost
    totals["unpriced_models"] = sorted(unpriced)
    return totals


def format_cost(total: dict[str, Any]) -> str:
    """Never present a guessed cost: one unpriced model makes the whole total 'unknown'."""
    if total.get("cost_known"):
        return f"${total.get('cost_usd', 0.0):.4f}"
    missing = total.get("unpriced_models") or []
    detail = f" No price in configs/pricing.yaml for: {', '.join(missing)}." if missing else ""
    if total.get("priced_calls"):
        return f"unknown (at least ${total.get('cost_usd', 0.0):.4f}).{detail}"
    return f"unknown.{detail}"
