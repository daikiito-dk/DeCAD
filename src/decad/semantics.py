"""Semantic checks that go beyond what the JSON Schema can express.

These rules turn a schema-valid document into a *consistent* one: every id
reference resolves, the constraint graph is a DAG, and the execution plan
removes things in an order the graph actually allows.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from decad.errors import Issue, Severity
from decad.graph import CyclicGraphError, predecessors, removal_order

_UNIT_TOLERANCE = 1e-3

_ACTION_EXPECTED_TYPES = {
    "unfasten": {"fastener"},
    "cut_adhesive": {"bonding"},
    "pick_and_lift": {"structural_part", "sub_assembly"},
}


def check_semantics(doc: Mapping[str, Any]) -> list[Issue]:
    """Run all semantic checks; return a list of issues (possibly empty)."""
    issues: list[Issue] = []
    issues.extend(_check_nodes(doc))
    issues.extend(_check_edges(doc))
    issues.extend(_check_plan(doc))
    return issues


def _check_nodes(doc: Mapping[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    seen: set[str] = set()
    for index, node in enumerate(doc["nodes"]):
        if node["id"] in seen:
            issues.append(
                Issue(
                    "duplicate-node-id",
                    f"Duplicate node id '{node['id']}'.",
                    f"$.nodes[{index}]",
                )
            )
        seen.add(node["id"])
    return issues


def _check_edges(doc: Mapping[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    edges = doc["graph_edges"]
    nodes = {node["id"]: node for node in doc["nodes"]}

    for index, edge in enumerate(edges.get("fasteners", [])):
        base = f"$.graph_edges.fasteners[{index}]"
        _require_node(issues, nodes, f"{base}.fastener_id", edge["fastener_id"], "fastener")
        for pos, retained in enumerate(edge["retains"]):
            _require_node(issues, nodes, f"{base}.retains[{pos}]", retained)
        _require_node(issues, nodes, f"{base}.anchored_to", edge["anchored_to"])

    for index, edge in enumerate(edges.get("bonds", [])):
        base = f"$.graph_edges.bonds[{index}]"
        _require_node(issues, nodes, f"{base}.bond_id", edge["bond_id"], "bonding")
        for pos, joined in enumerate(edge["joins"]):
            _require_node(issues, nodes, f"{base}.joins[{pos}]", joined)
        if edge["joins"][0] == edge["joins"][1]:
            issues.append(
                Issue("self-bond", "A bond must join two distinct nodes.", f"{base}.joins")
            )

    for index, edge in enumerate(edges.get("interferences", [])):
        base = f"$.graph_edges.interferences[{index}]"
        _require_node(issues, nodes, f"{base}.blocker", edge["blocker"])
        _require_node(issues, nodes, f"{base}.blocked_node", edge["blocked_node"])
        if edge["blocker"] == edge["blocked_node"]:
            issues.append(Issue("self-interference", "A node cannot block its own removal.", base))
        for pos, vec in enumerate(edge["blocked_vectors"]):
            issues.extend(
                _check_direction(vec, f"{base}.blocked_vectors[{pos}]", "blocked_vectors")
            )

    try:
        removal_order(doc)
    except CyclicGraphError as exc:
        issues.append(
            Issue(
                "removal-cycle",
                f"The constraint graph is not a DAG (cycle involves: {', '.join(exc.nodes)}).",
                "$.graph_edges",
            )
        )
    return issues


def _check_plan(doc: Mapping[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    plan = doc["disassembly_execution_plan"]
    nodes = {node["id"] for node in doc["nodes"]}
    node_types = {node["id"]: node["type"] for node in doc["nodes"]}

    seen_steps: set[int] = set()
    for index, step in enumerate(plan):
        base = f"$.disassembly_execution_plan[{index}]"
        if step["step_id"] in seen_steps:
            issues.append(
                Issue(
                    "duplicate-step-id",
                    f"Duplicate step_id {step['step_id']}.",
                    f"{base}.step_id",
                )
            )
        seen_steps.add(step["step_id"])
        expected_types = _ACTION_EXPECTED_TYPES.get(step["action"])
        for pos, target in enumerate(step["target_nodes"]):
            if target not in nodes:
                issues.append(
                    Issue(
                        "unknown-node-ref",
                        f"'{target}' does not match any node id.",
                        f"{base}.target_nodes[{pos}]",
                    )
                )
            elif expected_types is not None and node_types[target] not in expected_types:
                issues.append(
                    Issue(
                        "action-target-mismatch",
                        f"Action '{step['action']}' expects "
                        f"{'/'.join(sorted(expected_types))} nodes, "
                        f"but '{target}' has type '{node_types[target]}'.",
                        f"{base}.target_nodes[{pos}]",
                        Severity.WARNING,
                    )
                )
        if "trajectory_vector" in step:
            issues.extend(
                _check_direction(
                    step["trajectory_vector"], f"{base}.trajectory_vector", "trajectory_vector"
                )
            )

    issues.extend(_check_precedences(doc))
    issues.extend(_check_plan_order(doc))
    return issues


def _check_precedences(doc: Mapping[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    plan = doc["disassembly_execution_plan"]
    position = {step["step_id"]: index for index, step in enumerate(plan)}
    for index, edge in enumerate(doc["graph_edges"].get("precedences", [])):
        base = f"$.graph_edges.precedences[{index}]"
        known = True
        for key in ("before_step_id", "after_step_id"):
            if edge[key] not in position:
                known = False
                issues.append(
                    Issue(
                        "unknown-step-ref",
                        f"{key} {edge[key]} does not match any step_id in the execution plan.",
                        f"{base}.{key}",
                    )
                )
        if not known:
            continue
        if edge["before_step_id"] == edge["after_step_id"]:
            issues.append(Issue("self-precedence", "A step cannot precede itself.", base))
        elif position[edge["before_step_id"]] > position[edge["after_step_id"]]:
            issues.append(
                Issue(
                    "precedence-violation",
                    f"Step {edge['before_step_id']} must run before step "
                    f"{edge['after_step_id']}, but the plan lists them in the opposite order.",
                    base,
                )
            )
    return issues


def _check_plan_order(doc: Mapping[str, Any]) -> list[Issue]:
    """Simulate the plan: every removal must be unblocked when it happens."""
    issues: list[Issue] = []
    preds = predecessors(doc)
    removed: set[str] = set()
    for index, step in enumerate(doc["disassembly_execution_plan"]):
        for target in step["target_nodes"]:
            pending = preds.get(target, set()) - removed
            if pending:
                issues.append(
                    Issue(
                        "plan-order-violation",
                        f"Step {step['step_id']} removes '{target}' while "
                        f"{', '.join(sorted(pending))} still block or retain it.",
                        f"$.disassembly_execution_plan[{index}].target_nodes",
                    )
                )
        removed.update(step["target_nodes"])
    return issues


def _check_direction(vec: list[float], path: str, field: str) -> list[Issue]:
    length = math.sqrt(sum(component * component for component in vec))
    if length == 0.0:
        return [Issue("zero-vector", f"{field} must be a non-zero vector.", path)]
    if abs(length - 1.0) > _UNIT_TOLERANCE:
        return [
            Issue(
                "non-unit-vector",
                f"{field} has length {length:.4f}; direction vectors should be normalized to 1.",
                path,
                Severity.WARNING,
            )
        ]
    return []


def _require_node(
    issues: list[Issue],
    nodes: dict[str, Mapping[str, Any]],
    path: str,
    node_id: str,
    expected_type: str | None = None,
) -> None:
    node = nodes.get(node_id)
    if node is None:
        issues.append(Issue("unknown-node-ref", f"'{node_id}' does not match any node id.", path))
    elif expected_type is not None and node["type"] != expected_type:
        issues.append(
            Issue(
                "wrong-node-type",
                f"'{node_id}' has node type '{node['type']}', expected '{expected_type}'.",
                path,
            )
        )
