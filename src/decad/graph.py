"""Constraint-graph construction and removal-order computation."""

from __future__ import annotations

import heapq
from collections import defaultdict
from collections.abc import Mapping
from typing import Any

from decad.errors import OdbomError


class CyclicGraphError(OdbomError):
    """The constraint graph contains a cycle, so no removal order exists."""

    def __init__(self, nodes: list[str]) -> None:
        self.nodes = nodes
        super().__init__(f"constraint graph has a cycle involving: {', '.join(nodes)}")


def predecessors(doc: Mapping[str, Any]) -> dict[str, set[str]]:
    """Map each node id to the node ids that must be removed before it.

    The mapping is derived from three edge kinds:

    * fastener edges: a fastener must come out before anything it retains;
    * bond edges: a bond must be released before either joined node can go;
    * interference edges: a blocker must come out before the node it blocks.
    """
    ids = {node["id"] for node in doc["nodes"]}
    preds: dict[str, set[str]] = {node_id: set() for node_id in ids}

    def add(before: str, after: str) -> None:
        if before in ids and after in ids and before != after:
            preds[after].add(before)

    edges = doc.get("graph_edges", {})
    for edge in edges.get("fasteners", []):
        for retained in edge["retains"]:
            add(edge["fastener_id"], retained)
    for edge in edges.get("bonds", []):
        for joined in edge["joins"]:
            add(edge["bond_id"], joined)
    for edge in edges.get("interferences", []):
        add(edge["blocker"], edge["blocked_node"])
    return preds


def removal_order(doc: Mapping[str, Any]) -> list[str]:
    """Return a deterministic topological removal order for the document.

    Raises ``CyclicGraphError`` if the constraint graph is not a DAG.
    """
    preds = predecessors(doc)
    remaining = {node_id: set(deps) for node_id, deps in preds.items()}
    successors: dict[str, set[str]] = defaultdict(set)
    for after, befores in preds.items():
        for before in befores:
            successors[before].add(after)

    ready = [node_id for node_id, deps in remaining.items() if not deps]
    heapq.heapify(ready)
    order: list[str] = []
    while ready:
        node_id = heapq.heappop(ready)
        order.append(node_id)
        for succ in successors.get(node_id, ()):
            deps = remaining[succ]
            deps.discard(node_id)
            if not deps:
                heapq.heappush(ready, succ)

    if len(order) != len(remaining):
        stuck = sorted(set(remaining) - set(order))
        raise CyclicGraphError(stuck)
    return order
