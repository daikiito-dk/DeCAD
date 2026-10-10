"""Access to the bundled OD-BOM JSON Schema."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from pathlib import Path

from decad.errors import SchemaError

SCHEMA_VERSION = "0.1.0"


def load_schema(path: str | Path | None = None) -> dict:
    """Load the OD-BOM schema, optionally from an explicit file."""
    if path is not None:
        try:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SchemaError(f"cannot load schema from {path}: {exc}") from exc
    return _bundled_schema()


@lru_cache(maxsize=1)
def _bundled_schema() -> dict:
    # Mirrors the canonical layout: schemas/vX.Y.Z/odbom.schema.json
    ref = (
        resources.files("decad") / "_data" / "schemas" / f"v{SCHEMA_VERSION}" / "odbom.schema.json"
    )
    try:
        with ref.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise SchemaError(f"cannot load bundled OD-BOM schema: {exc}") from exc
