"""Every shipped example must validate cleanly."""

from __future__ import annotations

from pathlib import Path

from decad import load
from decad.validation import validate_path


def test_every_example_is_valid(examples_dir: Path) -> None:
    example_files = sorted(examples_dir.glob("*.json"))
    assert len(example_files) >= 2
    for path in example_files:
        result = validate_path(path)
        assert result.valid, f"{path} should be valid, got: {[str(e) for e in result.errors]}"
        assert result.warnings == [], (
            f"{path} should be warning-free, got: {[str(w) for w in result.warnings]}"
        )
        assert load(path) is not None
