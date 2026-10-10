"""Schema and semantic validation for OD-BOM documents."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from decad.errors import Issue, Severity
from decad.schema import load_schema
from decad.semantics import check_semantics


@dataclass
class ValidationResult:
    """Outcome of validating one document."""

    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.severity is Severity.WARNING]

    @property
    def valid(self) -> bool:
        return not self.errors

    def __bool__(self) -> bool:
        return self.valid


def validate(
    data: Mapping[str, Any],
    schema_path: str | Path | None = None,
) -> ValidationResult:
    """Validate a parsed OD-BOM document: schema first, then semantics."""
    validator = Draft202012Validator(load_schema(schema_path))
    schema_issues = [
        Issue(
            code="schema-violation",
            path=error.json_path,
            message=error.message,
        )
        for error in sorted(validator.iter_errors(data), key=_error_sort_key)
    ]
    if schema_issues:
        # Semantic checks assume the schema shape; skip them on malformed input.
        return ValidationResult(schema_issues)
    return ValidationResult(check_semantics(data))


def validate_path(
    path: str | Path,
    schema_path: str | Path | None = None,
) -> ValidationResult:
    """Validate the OD-BOM document stored at ``path``."""
    file_path = Path(path)
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return ValidationResult(
            [Issue("file-not-found", f"No such file: {file_path}", str(file_path))]
        )
    except json.JSONDecodeError as exc:
        return ValidationResult([Issue("json-parse-error", f"Invalid JSON: {exc}", str(file_path))])
    return validate(data, schema_path)


def _error_sort_key(error: Any) -> list[tuple[int, str]]:
    # jsonschema paths mix strings (object keys) and ints (array indices),
    # which cannot be compared directly; tag them so sorting never fails.
    return [
        (0, f"{part:06d}") if isinstance(part, int) else (1, str(part))
        for part in error.absolute_path
    ]
