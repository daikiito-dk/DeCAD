"""Typed access to a validated OD-BOM document."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from decad.errors import InvalidDocumentError
from decad.graph import removal_order
from decad.validation import validate


def load(path: str | Path) -> OdbomDocument:
    """Read and validate the document at ``path``.

    Raises ``InvalidDocumentError`` if the document does not validate.
    """
    return loads(json.loads(Path(path).read_text(encoding="utf-8")))


def loads(data: Mapping[str, Any]) -> OdbomDocument:
    """Validate ``data`` and wrap it in an ``OdbomDocument``.

    Raises ``InvalidDocumentError`` if the document does not validate.
    """
    result = validate(data)
    if not result.valid:
        raise InvalidDocumentError(result)
    return OdbomDocument(dict(data))


class OdbomDocument:
    """Convenience wrapper over a validated OD-BOM document."""

    _NODE_COLORS = {
        "structural_part": "lightblue",
        "fastener": "orange",
        "bonding": "violet",
        "sub_assembly": "yellow",
    }

    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    @property
    def metadata(self) -> dict[str, Any]:
        return self.data["metadata"]

    @property
    def nodes(self) -> list[dict[str, Any]]:
        return self.data["nodes"]

    @property
    def edges(self) -> dict[str, Any]:
        return self.data["graph_edges"]

    @property
    def steps(self) -> list[dict[str, Any]]:
        return self.data["disassembly_execution_plan"]

    def node(self, node_id: str) -> dict[str, Any]:
        for node in self.nodes:
            if node["id"] == node_id:
                return node
        raise KeyError(node_id)

    def removal_order(self) -> list[str]:
        """A feasible removal order derived from the constraint graph."""
        return removal_order(self.data)

    def summary(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        hazardous: list[str] = []
        for node in self.nodes:
            by_type[node["type"]] = by_type.get(node["type"], 0) + 1
            if node.get("material", {}).get("hazardous"):
                hazardous.append(node["label"])
        return {
            "product": {
                "id": self.metadata.get("product_id"),
                "name": self.metadata.get("name"),
            },
            "odbom_version": self.metadata.get("odbom_version"),
            "nodes": {"total": len(self.nodes), "by_type": by_type},
            "hazardous_nodes": hazardous,
            "edges": {
                "fasteners": len(self.edges.get("fasteners", [])),
                "bonds": len(self.edges.get("bonds", [])),
                "interferences": len(self.edges.get("interferences", [])),
                "precedences": len(self.edges.get("precedences", [])),
            },
            "execution_steps": len(self.steps),
            "removal_order": self.removal_order(),
        }

    def to_dot(self) -> str:
        """Render the constraint graph as Graphviz DOT."""
        lines = ["digraph odbom {", '  rankdir="LR";', "  node [style=filled];"]
        for node in self.nodes:
            label = node["label"].replace('"', '\\"')
            color = self._NODE_COLORS.get(node["type"], "grey")
            lines.append(f'  "{node["id"]}" [label="{label}", fillcolor="{color}"];')
        for edge in self.edges.get("fasteners", []):
            for retained in edge["retains"]:
                lines.append(
                    f'  "{edge["fastener_id"]}" -> "{retained}" '
                    f'[label="{edge["removal_method"]}", style=dashed];'
                )
        for edge in self.edges.get("bonds", []):
            for joined in edge["joins"]:
                lines.append(
                    f'  "{edge["bond_id"]}" -> "{joined}" '
                    f'[label="{edge["removal_method"]}", style=dotted];'
                )
        for edge in self.edges.get("interferences", []):
            lines.append(f'  "{edge["blocker"]}" -> "{edge["blocked_node"]}" [label="blocks"];')
        lines.append("}")
        return "\n".join(lines) + "\n"
