"""Error types and validation findings for OD-BOM documents."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from decad.validation import ValidationResult


class Severity(str, Enum):
    """How serious a validation finding is."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Issue:
    """A single validation finding."""

    code: str
    message: str
    path: str = "$"
    severity: Severity = Severity.ERROR

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "path": self.path,
            "message": self.message,
        }

    def __str__(self) -> str:
        return f"{self.path}: {self.message} [{self.code}]"


class OdbomError(Exception):
    """Base class for all DeCAD / OD-BOM errors."""


class SchemaError(OdbomError):
    """The OD-BOM JSON Schema itself could not be loaded or parsed."""


class InvalidDocumentError(OdbomError):
    """A document failed schema or semantic validation."""

    def __init__(self, result: ValidationResult) -> None:
        self.result = result
        lines = [f"  {issue}" for issue in result.errors]
        super().__init__("invalid OD-BOM document:\n" + "\n".join(lines))
