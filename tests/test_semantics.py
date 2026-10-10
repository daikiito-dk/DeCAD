"""Semantic rule coverage: each rule fires on a targeted mutation."""

from __future__ import annotations

import copy

from decad.validation import validate


def codes(doc: dict) -> list[str]:
    return [issue.code for issue in validate(doc).issues]


def test_valid_battery_example_is_clean(battery_example: dict) -> None:
    result = validate(battery_example)
    assert result.valid
    assert result.issues == []


def test_duplicate_node_id(battery_example: dict) -> None:
    doc = copy.deepcopy(battery_example)
    doc["nodes"][1]["id"] = doc["nodes"][0]["id"]
    assert "duplicate-node-id" in codes(doc)


def test_unknown_retained_node(battery_example: dict) -> None:
    doc = copy.deepcopy(battery_example)
    doc["graph_edges"]["fasteners"][0]["retains"].append("node_ghost")
    assert "unknown-node-ref" in codes(doc)


def test_fastener_edge_must_reference_a_fastener(battery_example: dict) -> None:
    doc = copy.deepcopy(battery_example)
    doc["graph_edges"]["fasteners"][0]["fastener_id"] = "node_top_cover"
    assert "wrong-node-type" in codes(doc)


def test_self_interference(battery_example: dict) -> None:
    doc = copy.deepcopy(battery_example)
    edge = doc["graph_edges"]["interferences"][0]
    edge["blocked_node"] = edge["blocker"]
    assert "self-interference" in codes(doc)


def test_removal_cycle(battery_example: dict) -> None:
    doc = copy.deepcopy(battery_example)
    doc["graph_edges"]["interferences"].append(
        {
            "blocker": "node_cell_array_01",
            "blocked_node": "node_m6_screw_01",
            "blocked_vectors": [[0.0, 0.0, 1.0]],
        }
    )
    assert "removal-cycle" in codes(doc)


def test_plan_order_violation(battery_example: dict) -> None:
    doc = copy.deepcopy(battery_example)
    plan = doc["disassembly_execution_plan"]
    plan[0], plan[1] = plan[1], plan[0]
    assert "plan-order-violation" in codes(doc)


def test_zero_trajectory_vector_is_an_error(battery_example: dict) -> None:
    doc = copy.deepcopy(battery_example)
    doc["disassembly_execution_plan"][0]["trajectory_vector"] = [0.0, 0.0, 0.0]
    result = validate(doc)
    assert "zero-vector" in [issue.code for issue in result.errors]


def test_non_unit_blocked_vector_is_a_warning(battery_example: dict) -> None:
    doc = copy.deepcopy(battery_example)
    doc["graph_edges"]["interferences"][0]["blocked_vectors"] = [[0.0, 0.0, 2.0]]
    result = validate(doc)
    assert result.valid
    assert "non-unit-vector" in [issue.code for issue in result.warnings]


def test_precedence_violation(smartphone_example: dict) -> None:
    doc = copy.deepcopy(smartphone_example)
    edge = doc["graph_edges"]["precedences"][0]
    edge["before_step_id"], edge["after_step_id"] = (
        edge["after_step_id"],
        edge["before_step_id"],
    )
    assert "precedence-violation" in codes(doc)


def test_unknown_step_reference(smartphone_example: dict) -> None:
    doc = copy.deepcopy(smartphone_example)
    doc["graph_edges"]["precedences"][0]["before_step_id"] = 99
    assert "unknown-step-ref" in codes(doc)


def test_self_bond(smartphone_example: dict) -> None:
    doc = copy.deepcopy(smartphone_example)
    doc["graph_edges"]["bonds"][0]["joins"] = ["node_display", "node_display"]
    assert "self-bond" in codes(doc)


def test_action_target_mismatch_is_a_warning(smartphone_example: dict) -> None:
    doc = copy.deepcopy(smartphone_example)
    doc["disassembly_execution_plan"][0]["action"] = "pick_and_lift"
    result = validate(doc)
    assert "action-target-mismatch" in [issue.code for issue in result.warnings]


def test_schema_violation_short_circuits(battery_example: dict) -> None:
    doc = copy.deepcopy(battery_example)
    doc["nodes"][0]["type"] = "warp_core"
    result = validate(doc)
    assert not result.valid
    assert "schema-violation" in [issue.code for issue in result.errors]
