"""DeCAD — open toolkit for the OD-BOM (Open Disassembly & Reverse BOM) format.

DeCAD ships the reference schema, validator, and CLI for OD-BOM: an open,
machine-readable description of how a physical product comes apart.
"""

from decad.document import OdbomDocument, load, loads
from decad.errors import (
    InvalidDocumentError,
    Issue,
    OdbomError,
    SchemaError,
    Severity,
)
from decad.validation import ValidationResult, validate, validate_path

__version__ = "0.1.0"

__all__ = [
    "InvalidDocumentError",
    "Issue",
    "OdbomDocument",
    "OdbomError",
    "SchemaError",
    "Severity",
    "ValidationResult",
    "__version__",
    "load",
    "loads",
    "validate",
    "validate_path",
]
