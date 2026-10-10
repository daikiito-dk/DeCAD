"""Constraint graph behavior: orders, cycles, DOT rendering."""

from __future__ import annotations

import copy

import pytest

from decad.document import load
from decad.graph import CyclicGraphError, removal_order


def test_battery_removal_order(battery_example: dict) -> None:
    order = removal_order(battery_example)
    assert order == ["node_m6_screw_01", "node_top_cover", "node_cell_array_01"]


def test_smartphone_order_respects_dependencies(smartphone_example: dict) -> None:
    order = removal_order(smartphone_example)
    assert set(order) == {node["id"] for node in smartphone_example["nodes"]}
    assert order.index("node_pentalobe_screws") < order.index("node_display")
    assert order.index("node_display_adhesive") < order.index("node_display")
    assert order.index("node_display") < order.index("node_battery")


def test_cycle_raises(battery_example: dict) -> None:
    doc = copy.deepcopy(battery_example)
    doc["graph_edges"]["interferences"].append(
        {
            "blocker": "node_cell_array_01",
            "blocked_node": "node_m6_screw_01",
            "blocked_vectors": [[0.0, 0.0, 1.0]],
        }
    )
    with pytest.raises(CyclicGraphError) as excinfo:
        removal_order(doc)
    assert "node_m6_screw_01" in excinfo.value.nodes


def test_dot_output(battery_path) -> None:
    doc = load(battery_path)
    dot = doc.to_dot()
    assert dot.startswith("digraph odbom {")
    assert '"node_m6_screw_01" -> "node_top_cover"' in dot
    assert '"node_top_cover" -> "node_cell_array_01"' in dot
    assert dot.rstrip().endswith("}")
