# DeCAD

[![CI](https://github.com/daikiito-dk/DeCAD/actions/workflows/ci.yml/badge.svg)](https://github.com/daikiito-dk/DeCAD/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

**English** | [日本語](README.ja.md)

DeCAD is an open-source toolkit for reverse CAD and product disassembly. Its core is the **OD-BOM (Open Disassembly & Reverse BOM)** format: an open, machine-readable standard that captures how a physical product comes apart — what it contains, what holds it together, what blocks what, and how a robot can take it apart.

Traditional eBOM/mBOM formats describe how products are *built*. OD-BOM describes how they are *unbuilt*: reverse hierarchies, interference and precedence constraint graphs, tool and trajectory requirements per removal step, and end-of-life material classification for circular-economy valuation.

## The format in 30 seconds

```json
{
  "$schema": "https://open-disassembly.org/schemas/v0.1.0/odbom.schema.json",
  "metadata": { "odbom_version": "0.1.0", "product_id": "URN:PRODUCT:EV-BATTERY-PACK-2026", "name": "EV Battery Pack" },
  "nodes": [
    { "id": "node_top_cover", "type": "structural_part", "label": "Aluminum Top Housing Cover" },
    { "id": "node_m6_screw_01", "type": "fastener", "label": "M6 Torx Head Screw" },
    { "id": "node_cell_array_01", "type": "sub_assembly", "label": "Li-Ion Pouch Cell Array" }
  ],
  "graph_edges": {
    "fasteners": [
      { "fastener_id": "node_m6_screw_01", "retains": ["node_top_cover"], "anchored_to": "node_cell_array_01", "removal_method": "unscrew" }
    ],
    "interferences": [
      { "blocker": "node_top_cover", "blocked_node": "node_cell_array_01", "blocked_vectors": [[0.0, 0.0, 1.0]] }
    ]
  },
  "disassembly_execution_plan": [
    { "step_id": 1, "action": "unfasten", "target_nodes": ["node_m6_screw_01"] },
    { "step_id": 2, "action": "pick_and_lift", "target_nodes": ["node_top_cover"] }
  ]
}
```

Three things worth noticing:

1. **Nodes carry EoL classification** — recyclability category and hazard flags, ready for recovery-value math.
2. **Edges are constraints a planner can use** — the screws retain the cover; the cover blocks the cell array along +Z.
3. **The plan is checkable** — `decad validate` proves the steps are executable in the given order against the constraint graph.

## Install

Pre-release; install from a checkout (Python 3.10+, [uv](https://docs.astral.sh/uv/) recommended):

```bash
git clone https://github.com/daikiito-dk/DeCAD.git
cd DeCAD
make setup        # creates .venv and installs -e ".[dev]"
```

Plain pip works too: `python -m venv .venv && pip install -e .`

## CLI

```bash
$ decad validate examples/smartphone.odbom.json
OK: examples/smartphone.odbom.json is a valid OD-BOM document.

$ decad order examples/ev_battery_pack.odbom.json
node_m6_screw_01	M6 Torx Head Screw
node_top_cover	Aluminum Top Housing Cover
node_cell_array_01	Li-Ion Pouch Cell Array

$ decad summary examples/ev_battery_pack.odbom.json
Product:        Generic EV Battery Pack Module A (URN:PRODUCT:EV-BATTERY-PACK-2026)
OD-BOM version: 0.1.0
Nodes:          3 (fastener: 1, structural_part: 1, sub_assembly: 1)
Hazardous:      Li-Ion Pouch Cell Array
Edges:          fasteners: 1, bonds: 0, interferences: 1, precedences: 0
Plan steps:     2
Removal order:  node_m6_screw_01 -> node_top_cover -> node_cell_array_01

$ decad dot examples/smartphone.odbom.json | dot -Tsvg -o smartphone.svg
```

## Python API

```python
import decad

result = decad.validate_path("examples/ev_battery_pack.odbom.json")
assert result.valid
assert result.warnings == []

doc = decad.load("examples/ev_battery_pack.odbom.json")
doc.removal_order()  # ['node_m6_screw_01', 'node_top_cover', 'node_cell_array_01']
doc.summary()  # overview dict (nodes by type, hazards, edges, plan)
doc.to_dot()  # Graphviz DOT of the constraint graph
```

## Repository layout

```
DeCAD/
├── schemas/            # Versioned OD-BOM JSON Schemas (the standard itself)
│   └── v0.1.0/odbom.schema.json
├── examples/           # Reference .odbom documents
├── docs/specification.md
├── src/decad/          # Python validator library + CLI
└── tests/              # Schema, semantics, graph, CLI coverage
```

## Schema versioning & governance

- The schema is versioned with SemVer and published under `schemas/vX.Y.Z/`.
- Additive changes bump the minor version; breaking changes bump the major version.
- A test enforces that the packaged schema copy (`src/decad/_data/`) stays identical to the canonical one.
- Unknown `x-*` vendor extension keys are allowed everywhere and preserved by conforming tools.

## Roadmap

- **Phase 1 (this release):** OD-BOM v0.1.0 schema, specification, reference validator + CLI, examples, CI.
- **Phase 2:** CAD converters (`decad convert` from STEP / OpenSCAD / FreeCAD assemblies), ROS 2 integration package mapping steps to behavior trees and MoveIt 2 (`ros2_odbom`), Scan-to-CAD baselines (image/point cloud → CAD command sequence → OD-BOM).
- **Phase 3:** submit the stabilized specification to open-source robotics and circular-economy consortiums (e.g. ROS Industrial, Linux Foundation projects).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Licensed under [Apache-2.0](LICENSE).
