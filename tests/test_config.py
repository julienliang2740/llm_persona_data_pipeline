"""Config loading and, most importantly, that the API key never escapes into a message."""

from __future__ import annotations

import pytest

from pipeline.config import ConfigError, ModelRole, load_config, load_fireworks_api_key, redact
from pipeline.model import ModelClient, ModelError

FAKE_KEY = "fw_3ZrTESTKEYdoNotLog0123456789abcdef"


def test_missing_key_file_names_the_path_not_the_key(tmp_path, monkeypatch):
    monkeypatch.delenv("FIREWORKS_API_KEY", raising=False)
    with pytest.raises(ConfigError) as error:
        load_fireworks_api_key(tmp_path)
    assert "fireworks_api_key.txt" in str(error.value)


def test_key_is_read_and_stripped(tmp_path):
    (tmp_path / "fireworks_api_key.txt").write_text(f"  {FAKE_KEY}\n", encoding="utf-8")
    assert load_fireworks_api_key(tmp_path) == FAKE_KEY


def test_empty_key_file_is_an_error(tmp_path):
    (tmp_path / "fireworks_api_key.txt").write_text("\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_fireworks_api_key(tmp_path)


def test_redact_removes_the_secret():
    assert FAKE_KEY not in redact(f"Authorization: Bearer {FAKE_KEY}", [FAKE_KEY])


def test_error_paths_never_contain_the_key():
    """Every exception message the client can raise must be free of the key."""
    role = ModelRole(name="generator", model="m", api_key_source="fireworks")
    client = ModelClient({"generator": role}, api_key=FAKE_KEY)

    messages: list[str] = []
    # A header built with the key, then an error raised through the same code path.
    headers = client._headers(role)
    assert FAKE_KEY in headers["Authorization"]  # the key is used, but only in the header

    with pytest.raises(ModelError) as error:
        client._resolve("no_such_role")
    messages.append(str(error.value))

    no_key_client = ModelClient({"generator": role}, api_key=None)
    with pytest.raises(ModelError) as error:
        no_key_client._headers(role)
    messages.append(str(error.value))

    # The redaction the client applies to every server body and transport error.
    messages.append(client._safe(f"HTTP 401: bad key {FAKE_KEY} rejected"))

    for message in messages:
        assert FAKE_KEY not in message
    assert "<redacted>" in messages[-1]


def test_pilot_config_has_the_expected_roles(pilot_config):
    assert {"generator", "reviewer", "judge", "embeddings", "base"} <= set(pilot_config.roles)
    assert pilot_config.role("base").base_url.startswith("http://127.0.0.1")
    assert pilot_config.config_hash() == pilot_config.config_hash()


def test_unknown_role_key_is_rejected(tmp_path):
    config_file = tmp_path / "bad.yaml"
    config_file.write_text(
        "models:\n  generator:\n    model: m\n    typo_field: 1\n", encoding="utf-8"
    )
    with pytest.raises(ConfigError) as error:
        load_config(config_file, repo_root=tmp_path)
    assert "typo_field" in str(error.value)
