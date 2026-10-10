"""Shared pytest fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def examples_dir(repo_root: Path) -> Path:
    return repo_root / "examples"


@pytest.fixture(scope="session")
def battery_path(examples_dir: Path) -> Path:
    return examples_dir / "ev_battery_pack.odbom.json"


@pytest.fixture(scope="session")
def smartphone_path(examples_dir: Path) -> Path:
    return examples_dir / "smartphone.odbom.json"


@pytest.fixture()
def battery_example(battery_path: Path) -> dict:
    return json.loads(battery_path.read_text(encoding="utf-8"))


@pytest.fixture()
def smartphone_example(smartphone_path: Path) -> dict:
    return json.loads(smartphone_path.read_text(encoding="utf-8"))
