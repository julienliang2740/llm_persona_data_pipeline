"""Shared fixtures. Unit tests never touch the network."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FIXTURE_TARGETS = REPO_ROOT / "tests" / "fixtures" / "targets"
TOY_TARGET_ID = "toy"


@pytest.fixture(scope="session")
def toy_spec():
    from pipeline.target import load_target

    return load_target(FIXTURE_TARGETS, TOY_TARGET_ID)


@pytest.fixture(scope="session")
def pilot_config():
    from pipeline.config import load_config

    return load_config("configs/pilot.yaml")


def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: makes a real API call; skipped without a key")
