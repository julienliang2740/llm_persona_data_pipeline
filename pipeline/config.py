"""Run configuration, secret loading and run-directory resolution.

The Fireworks key is read from a gitignored file in the repo root. It is never
logged, never formatted into an exception, and never written to an artifact.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
KEY_FILENAME = "fireworks_api_key.txt"


class ConfigError(Exception):
    """Raised for a missing or malformed configuration or secret."""


def load_fireworks_api_key(repo_root: Path | None = None) -> str:
    """Read the Fireworks API key from the gitignored key file.

    Errors mention the path only. The key value never appears in any message.
    """
    root = repo_root or REPO_ROOT
    key_path = root / KEY_FILENAME
    if not key_path.exists():
        env_key = os.environ.get("FIREWORKS_API_KEY")
        if env_key:
            return env_key.strip()
        raise ConfigError(
            f"No API key: {key_path} not found and FIREWORKS_API_KEY is unset."
        )
    key = key_path.read_text(encoding="utf-8").strip()
    if not key:
        raise ConfigError(f"API key file {key_path} is empty.")
    return key


def redact(text: str, secrets: list[str]) -> str:
    """Replace any secret substring with a placeholder before the text is shown."""
    out = text
    for secret in secrets:
        if secret and len(secret) >= 8 and secret in out:
            out = out.replace(secret, "<redacted>")
    return out


@dataclass
class ModelRole:
    """One endpoint the pipeline can call: generator, reviewer, judge, base, embeddings."""

    name: str
    model: str
    base_url: str = "https://api.fireworks.ai/inference/v1"
    api_key_source: str = "fireworks"  # fireworks | none | env:VAR_NAME
    max_concurrency: int = 4
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout_s: float = 300.0
    supports_json_mode: bool = True
    enabled: bool = True
    extra_body: dict[str, Any] = field(default_factory=dict)

    @property
    def endpoint_key(self) -> str:
        return f"{self.base_url}::{self.model}"


@dataclass
class RunConfig:
    """Everything a stage needs: model roles, sizes, thresholds, paths."""

    path: Path
    raw: dict[str, Any]
    roles: dict[str, ModelRole]
    pricing: dict[str, Any]
    targets_dir: Path
    runs_dir: Path

    @property
    def generation(self) -> dict[str, Any]:
        return self.raw.get("generation", {})

    @property
    def validation(self) -> dict[str, Any]:
        return self.raw.get("validation", {})

    @property
    def evaluation(self) -> dict[str, Any]:
        return self.raw.get("evaluation", {})

    def role(self, name: str) -> ModelRole:
        if name not in self.roles:
            raise ConfigError(
                f"Config {self.path} has no model role '{name}'. "
                f"Defined roles: {sorted(self.roles)}"
            )
        return self.roles[name]

    def config_hash(self) -> str:
        """Short stable hash of the configuration, recorded in the manifest."""
        blob = json.dumps(self.raw, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()[:12]


def load_config(config_path: str | Path, repo_root: Path | None = None) -> RunConfig:
    root = repo_root or REPO_ROOT
    path = Path(config_path)
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    roles: dict[str, ModelRole] = {}
    for role_name, spec in (raw.get("models") or {}).items():
        if not isinstance(spec, dict):
            raise ConfigError(f"models.{role_name} in {path} must be a mapping.")
        if "model" not in spec:
            raise ConfigError(f"models.{role_name} in {path} is missing 'model'.")
        known = {f for f in ModelRole.__dataclass_fields__ if f != "name"}
        unknown = set(spec) - known
        if unknown:
            raise ConfigError(
                f"models.{role_name} in {path} has unknown keys: {sorted(unknown)}"
            )
        roles[role_name] = ModelRole(name=role_name, **spec)

    pricing_file = raw.get("pricing_file", "configs/pricing.yaml")
    pricing_path = Path(pricing_file)
    if not pricing_path.is_absolute():
        pricing_path = root / pricing_path
    pricing: dict[str, Any] = {}
    if pricing_path.exists():
        pricing = yaml.safe_load(pricing_path.read_text(encoding="utf-8")) or {}

    return RunConfig(
        path=path,
        raw=raw,
        roles=roles,
        pricing=pricing.get("models", {}) if isinstance(pricing, dict) else {},
        targets_dir=root / raw.get("targets_dir", "targets"),
        runs_dir=root / raw.get("runs_dir", "runs"),
    )


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def resolve_run_dir(config: RunConfig, target_id: str, run_id: str | None) -> Path:
    """Return runs/<target_id>/<run_id>, creating it. Without --run, reuse the latest."""
    target_runs = config.runs_dir / target_id
    if run_id is None:
        existing = sorted(p.name for p in target_runs.glob("*") if p.is_dir())
        run_id = existing[-1] if existing else new_run_id()
    run_dir = target_runs / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir
