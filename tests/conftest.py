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


REAL_TARGETS = ("catholic", "confucian", "protestant", "theravada")


@pytest.fixture(scope="session")
def real_specs():
    """The four reviewed targets. Plan invariants must hold on all of them, not just the toy."""
    from pipeline.target import load_target

    specs = {}
    for target_id in REAL_TARGETS:
        path = REPO_ROOT / "targets" / target_id
        if (path / "spec.yaml").exists():
            specs[target_id] = load_target(REPO_ROOT / "targets", target_id)
    if not specs:
        pytest.skip("no real targets committed yet")
    return specs


PLAN_SETTINGS = {
    "divergence_fraction": 0.4,
    "eval_family_fraction": 0.25,
    "reserved_family_fraction": 0.0,
    "counterfactual_fraction": 0.3,
    "explicit_fraction": 0.0,
    "unresolved_tradeoff_fraction": 0.25,
}


def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: makes a real API call; skipped without a key")
