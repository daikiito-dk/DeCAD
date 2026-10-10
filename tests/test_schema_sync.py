"""The packaged schema copy must stay identical to the canonical one."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_packaged_schema_matches_canonical(repo_root: Path) -> None:
    canonical = repo_root / "schemas" / "v0.1.0" / "odbom.schema.json"
    packaged = repo_root / "src" / "decad" / "_data" / "schemas" / "v0.1.0" / "odbom.schema.json"
    if not canonical.exists() or not packaged.exists():
        pytest.skip("schema copies not present (installed package?)")
    assert canonical.read_text(encoding="utf-8") == packaged.read_text(encoding="utf-8"), (
        "src/decad/_data/schemas is out of sync with schemas/ — "
        "copy the canonical schema over and re-run."
    )
