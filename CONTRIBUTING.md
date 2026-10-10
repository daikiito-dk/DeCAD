# Contributing to DeCAD

Thanks for helping build the open standard for how products come apart.

## Getting started

```bash
git clone https://github.com/daikiito-dk/DeCAD.git
cd DeCAD
make setup     # uv venv + pip install -e ".[dev]"
make check     # ruff lint + format check + pytest
```

Prefer plain pip? `python -m venv .venv && .venv/bin/pip install -e ".[dev]"` then use `.venv/bin/pytest` and `.venv/bin/ruff` directly. Python 3.10+ is required; `.python-version` pins 3.12 for local dev.

## Where things live

| Path | What it is |
| --- | --- |
| `schemas/vX.Y.Z/` | Canonical OD-BOM JSON Schemas (the standard itself) |
| `src/decad/_data/schemas/` | Packaged copy of the schema (must stay identical — enforced by `tests/test_schema_sync.py`) |
| `docs/specification.md` | The normative specification |
| `examples/` | Reference documents; every one must validate warning-free |
| `src/decad/` | Validator library and CLI |

## Changing the schema

1. Treat `schemas/v0.1.0/odbom.schema.json` as the single source of truth.
2. Copy it over `src/decad/_data/schemas/v0.1.0/odbom.schema.json` (or add a new versioned directory) — the sync test will fail otherwise.
3. Additive changes (new optional fields, new enum members) are fine for a **minor** bump; anything that invalidates existing documents requires a **major** bump and a new `schemas/vX.Y.Z/` directory. Never edit a released schema in place.
4. Update `docs/specification.md` and `CHANGELOG.md` in the same pull request.

## Adding an example

Examples are the format's public face. Keep them small, realistic, and warning-free; CI validates every `examples/*.json` with the CLI. Add a test only if the example demonstrates a rule not yet covered.

## Code style

`ruff` enforces style (100-column lines, import sorting). Run `make fmt` before committing. Write tests for new validator behavior — mutation tests against the shipped examples are the house style.

## Commits

Use short, imperative subjects, conventional-commit style where natural: `feat:`, `fix:`, `docs:`, `schema:`. Keep pull requests focused; schema changes and tool changes should not mix when avoidable.

## Security and safety

This project describes physical disassembly (batteries, hazardous materials, robotic tools). Report security issues privately via GitHub security advisories, not public issues. Keep hazard documentation (`hazardous`, `hazard_details`) accurate — downstream recyclers rely on it.
