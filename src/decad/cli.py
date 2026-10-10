"""Command-line interface for working with OD-BOM documents."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from decad import __version__
from decad.document import load
from decad.errors import OdbomError
from decad.validation import validate_path


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except OdbomError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="decad",
        description=(
            "DeCAD: validate and inspect OD-BOM (Open Disassembly & Reverse BOM) documents."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser(
        "validate", help="Validate a document against the schema and semantic rules."
    )
    p.add_argument("file", type=Path, help="path to an .odbom JSON document")
    p.add_argument(
        "--schema",
        type=Path,
        help="validate against this schema instead of the bundled one",
    )
    p.add_argument(
        "--json", dest="as_json", action="store_true", help="emit machine-readable results"
    )
    p.set_defaults(func=_cmd_validate)

    p = sub.add_parser("summary", help="Print an overview of a document.")
    p.add_argument("file", type=Path)
    p.add_argument(
        "--json", dest="as_json", action="store_true", help="emit machine-readable results"
    )
    p.set_defaults(func=_cmd_summary)

    p = sub.add_parser(
        "order", help="Print a feasible removal order derived from the constraint graph."
    )
    p.add_argument("file", type=Path)
    p.add_argument(
        "--json", dest="as_json", action="store_true", help="emit machine-readable results"
    )
    p.set_defaults(func=_cmd_order)

    p = sub.add_parser("dot", help="Emit a Graphviz DOT rendering of the constraint graph.")
    p.add_argument("file", type=Path)
    p.set_defaults(func=_cmd_dot)
    return parser


def _cmd_validate(args: argparse.Namespace) -> int:
    result = validate_path(args.file, schema_path=args.schema)
    if args.as_json:
        print(
            json.dumps(
                {
                    "file": str(args.file),
                    "valid": result.valid,
                    "issues": [issue.to_dict() for issue in result.issues],
                },
                indent=2,
            )
        )
    elif result.valid:
        print(f"OK: {args.file} is a valid OD-BOM document.")
        for warning in result.warnings:
            print(f"warning: {warning}")
    else:
        for error in result.errors:
            print(f"error: {error}", file=sys.stderr)
        for warning in result.warnings:
            print(f"warning: {warning}", file=sys.stderr)
    return 0 if result.valid else 1


def _cmd_summary(args: argparse.Namespace) -> int:
    doc = load(args.file)
    summary = doc.summary()
    if args.as_json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0
    product = summary["product"]
    print(f"Product:        {product['name']} ({product['id']})")
    print(f"OD-BOM version: {summary['odbom_version']}")
    breakdown = ", ".join(
        f"{kind}: {count}" for kind, count in sorted(summary["nodes"]["by_type"].items())
    )
    print(f"Nodes:          {summary['nodes']['total']}" + (f" ({breakdown})" if breakdown else ""))
    if summary["hazardous_nodes"]:
        print(f"Hazardous:      {'; '.join(summary['hazardous_nodes'])}")
    edge_bits = ", ".join(f"{kind}: {count}" for kind, count in summary["edges"].items())
    print(f"Edges:          {edge_bits}")
    print(f"Plan steps:     {summary['execution_steps']}")
    print("Removal order:  " + " -> ".join(summary["removal_order"]))
    return 0


def _cmd_order(args: argparse.Namespace) -> int:
    doc = load(args.file)
    order = doc.removal_order()
    if args.as_json:
        print(json.dumps(order, indent=2))
        return 0
    labels = {node["id"]: node["label"] for node in doc.nodes}
    for node_id in order:
        print(f"{node_id}\t{labels[node_id]}")
    return 0


def _cmd_dot(args: argparse.Namespace) -> int:
    doc = load(args.file)
    sys.stdout.write(doc.to_dot())
    return 0
