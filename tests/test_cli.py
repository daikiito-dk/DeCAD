"""CLI behavior via direct main() calls."""

from __future__ import annotations

import copy
import json

from decad.cli import main


def test_validate_valid_document(battery_path, capsys) -> None:
    assert main(["validate", str(battery_path)]) == 0
    assert "valid OD-BOM document" in capsys.readouterr().out


def test_validate_json_output(battery_path, capsys) -> None:
    assert main(["validate", str(battery_path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is True
    assert payload["issues"] == []


def test_validate_invalid_document(battery_example: dict, tmp_path, capsys) -> None:
    doc = copy.deepcopy(battery_example)
    doc["nodes"][1]["id"] = doc["nodes"][0]["id"]
    path = tmp_path / "broken.odbom.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    assert main(["validate", str(path)]) == 1
    assert "duplicate-node-id" in capsys.readouterr().err


def test_validate_missing_file(tmp_path) -> None:
    assert main(["validate", str(tmp_path / "nope.json")]) == 1


def test_order_command(battery_path, capsys) -> None:
    assert main(["order", str(battery_path)]) == 0
    out = capsys.readouterr().out
    assert out.splitlines()[0].split("\t")[0] == "node_m6_screw_01"
    assert out.splitlines()[-1].split("\t")[0] == "node_cell_array_01"


def test_summary_command_json(smartphone_path, capsys) -> None:
    assert main(["summary", str(smartphone_path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["nodes"]["by_type"]["bonding"] == 2
    assert payload["nodes"]["by_type"]["fastener"] == 1
    assert payload["execution_steps"] == 5
    assert payload["edges"]["precedences"] == 1


def test_dot_command(smartphone_path, capsys) -> None:
    assert main(["dot", str(smartphone_path)]) == 0
    assert capsys.readouterr().out.startswith("digraph odbom {")
