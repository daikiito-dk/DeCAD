# Open Disassembly & Reverse BOM (OD-BOM) Specification

**Version:** 0.1.0 · **Status:** Draft for public comment
**Canonical schema:** [`schemas/v0.1.0/odbom.schema.json`](../schemas/v0.1.0/odbom.schema.json)
**Reference implementation:** the `decad` package in this repository ([DeCAD](https://github.com/daikiito-dk/DeCAD))

OD-BOM is developed in the open as part of the DeCAD project. Feedback belongs in the [issue tracker](https://github.com/daikiito-dk/DeCAD/issues).

## 1. Overview & purpose

The **Open Disassembly BOM (OD-BOM)** is an open, machine-readable data format that represents the structural decomposition, assembly/disassembly semantics, physical dependencies, and robotic execution steps required to deconstruct a physical product.

Unlike traditional **eBOM** (Engineering Bill of Materials) or **mBOM** (Manufacturing Bill of Materials), which dictate how parts are assembled from raw materials up, OD-BOM captures:

1. **Reverse hierarchies** — inside-out / outside-in topology.
2. **Interference & precedence graphs** — constraint networks.
3. **Physical tool & trajectory requirements for removal.**
4. **End-of-Life (EoL) material classification and economic value.**

## 2. Core concepts & graph model

An OD-BOM document models an assembly as a **directed acyclic graph (DAG)** plus a **spatial constraint network**:

- **Nodes ($\mathcal{V}$):** physical entities — components, sub-assemblies, fasteners, and structural bonds (adhesive seams, welds).
- **Edges ($\mathcal{E}$):** physical connections, geometric interferences, and procedural dependencies. Four kinds:
  - **Fastener edge ($E_{fast}$):** "Fastener $C$ retains component $D$ with torque $T$." $C$ must be removed before $D$.
  - **Bond edge ($E_{bond}$):** "Bond $B$ joins the surfaces of $A$ and $C$." $B$ must be released before $A$ or $C$ can be removed.
  - **Interference edge ($E_{int}$):** "Component $A$ blocks the removal vector of component $B$." $A$ must be removed before $B$.
  - **Precedence edge ($E_{prec}$):** "Execution step $X$ must happen before step $Y$" (plan-level ordering).

Fastener, bond, and interference edges together form the **removal constraint graph**, which MUST be a DAG: some feasible removal order must exist for every node.

## 3. File format

- Serialization: JSON (UTF-8).
- File extension: `.odbom` (`.odbom.json` is also accepted for editor friendliness).
- Media type (provisional, unregistered): `application/odbom+json`.
- Conformance target: [`schemas/v0.1.0/odbom.schema.json`](../schemas/v0.1.0/odbom.schema.json) (JSON Schema draft 2020-12).
- Reference documents: [EV battery pack](../examples/ev_battery_pack.odbom.json), [smartphone](../examples/smartphone.odbom.json).

Minimal document:

```json
{
  "$schema": "https://open-disassembly.org/schemas/v0.1.0/odbom.schema.json",
  "metadata": {
    "odbom_version": "0.1.0",
    "product_id": "URN:PRODUCT:WIDGET-01",
    "name": "Widget"
  },
  "nodes": [
    { "id": "base", "type": "structural_part", "label": "Cast Base" },
    { "id": "lid", "type": "structural_part", "label": "Plastic Lid" },
    {
      "id": "screws",
      "type": "fastener",
      "label": "T10 Screws",
      "fastener_attributes": { "subtype": "screw", "head_type": "Torx_T10", "fastener_count": 4 }
    }
  ],
  "graph_edges": {
    "fasteners": [
      { "fastener_id": "screws", "retains": ["lid"], "anchored_to": "base", "removal_method": "unscrew" }
    ]
  },
  "disassembly_execution_plan": [
    { "step_id": 1, "action": "unfasten", "target_nodes": ["screws"] }
  ]
}
```

## 4. Data dictionary

### 4.1 Node types

| `type` | Meaning | Required attributes |
| --- | --- | --- |
| `structural_part` | Rigid mechanical body (housing, bracket, plate) | — |
| `fastener` | Removable mechanical joiner (screw, bolt, clip, snap-fit, rivet) | `fastener_attributes` |
| `bonding` | Non-mechanical joiner (adhesive seam, solder joint, weld) | `bonding_attributes` |
| `sub_assembly` | Cluster of nodes removable as a single unit before internal disassembly | — |

Nodes MAY carry `material` (`primary_material`, `recyclability_category`, `hazardous`, `hazard_details`) and `bounding_box` (`min`, `max`; millimeters, local frame), and `cad_ref` pointing at reconstructed geometry (STEP etc.) plus an optional `feature_history` script that can regenerate it.

### 4.2 Edge types

**Fastener edges** (`graph_edges.fasteners`):

| Field | Meaning |
| --- | --- |
| `fastener_id` | Node id of type `fastener` |
| `retains` | Node ids held in place; each becomes removable only after the fastener |
| `anchored_to` | Node the fastener threads into (informational in v0.1) |
| `removal_method` | Intended release technique (see 4.4) |

**Bond edges** (`graph_edges.bonds`):

| Field | Meaning |
| --- | --- |
| `bond_id` | Node id of type `bonding` |
| `joins` | Exactly two node ids the bond connects; both become removable only after the bond is released |
| `removal_method` | Intended release technique (see 4.4) |

**Interference edges** (`graph_edges.interferences`):

| Field | Meaning |
| --- | --- |
| `blocker` | Node in the way |
| `blocked_node` | Node whose removal is restricted |
| `blocked_vectors` | Direction vectors along which translation is blocked |
| `description` | Human-readable note |

**Precedence edges** (`graph_edges.precedences`):

| Field | Meaning |
| --- | --- |
| `before_step_id`, `after_step_id` | Step ids; the first must execute before the second |
| `description` | Human-readable note |

### 4.3 Direction vectors

`blocked_vectors` and `trajectory_vector` are `[x, y, z]` arrays in the product's local coordinate frame. They MUST be non-zero and SHOULD be normalized to unit length. Path planners (A\*, RRT\*) consume them to compute collision-free extraction paths.

### 4.4 Removal methods & actions

`removal_method` (fastener and bond edges):

`unscrew` · `unclip` · `pry_open` · `cut` · `apply_heat` · `drill_out` · `destruct_cut` · `manual`

Execution plan `action` vocabulary:

- `unfasten` — screw/bolt removal (targets a `fastener` node).
- `cut_adhesive` — mechanical, solvent, or laser release of a bond (targets a `bonding` node).
- `pick_and_lift` — suction or gripper extraction.
- `pry_open` — leveraged force for snap-fits.
- `drill_out` / `destruct_cut` — destructive overrides when non-destructive release fails.

### 4.5 Execution plan semantics

- The **array order** of `disassembly_execution_plan` defines execution order. `step_id` is a stable identifier: it must be unique but need not be sequential.
- Every step **removes** its `target_nodes` from the assembly: `unfasten` removes the fastener, `cut_adhesive` releases the bond, `pick_and_lift`/`pry_open`/destructive actions remove parts.
- A step MUST NOT target a node that is still blocked (interference edge) or retained (fastener/bond edge) by anything not yet removed.
- `required_tool` describes the end effector (`tool_type` plus free-form parameters such as `bit`, `max_torque_nm`, `min_payload_kg`).
- `fallback_strategy` maps failure conditions to counter-strategies, e.g. `{"on_stripping": "drill_out"}`.

## 5. Conformance

A **conforming document**:

1. validates against the JSON Schema of its declared version;
2. has unique node ids and unique step ids;
3. resolves every node and step reference (no dangling ids);
4. uses `fastener_id`/`bond_id` only on nodes of the matching type;
5. forms a DAG from its fastener, bond, and interference edges (no cycles, no self-edges);
6. contains an execution plan consistent with the constraint graph and its precedence edges.

A **conforming validator**:

- MUST report violations of 1–6 as **errors**;
- SHOULD report non-unit direction vectors and action/target-type mismatches (e.g. `unfasten` pointed at a structural part) as **warnings**;
- MUST ignore unknown `x-*` vendor extension keys while preserving them on rewrite.

## 6. Ecosystem & integration

```
  ┌────────────────────────┐      ┌────────────────────────┐
  │  Reverse-CAD Engine    │      │  Non-Destructive CT/   │
  │  (Scan2Command AI)     │      │  LiDAR Vision System   │
  └───────────┬────────────┘      └───────────┬────────────┘
              │                               │
              └───────────────┬───────────────┘
                              │ Generates
                              ▼
                   ┌────────────────────┐
                   │  OD-BOM Document   │
                   │    (.odbom)        │
                   └─────────┬──────────┘
                             │ Consumed by
            ┌────────────────┴────────────────┐
            ▼                                 ▼
┌─────────────────────────┐      ┌─────────────────────────┐
│ Robot Controller (ROS 2)│      │ EoL Circular Economy    │
│ Trajectory / Task Plan  │      │ Valuation Engine (ERP)  │
└─────────────────────────┘      └─────────────────────────┘
```

1. **ROS 2 integration (planned: `ros2_odbom`)** — maps OD-BOM steps to behavior trees and MoveIt 2 motion planners.
2. **CAD converters (planned: `decad convert`)** — turn STEP / OpenSCAD / FreeCAD assemblies into OD-BOM graph representations.
3. **Circular economy ERP** — computes net recovery value:

$$\text{Net Value} = \sum \text{Material Value} - \sum (\text{Energy Cost} + \text{Tool Wear} + \text{Disassembly Time Cost})$$

## 7. Governance & versioning

- The schema is versioned with **SemVer** and published under `schemas/vX.Y.Z/`.
- Additive changes bump the **minor** version; breaking changes bump the **major** version.
- `metadata.odbom_version` names the specification version a document targets; documents may use any feature of that version.
- Validators should support the current and previous major version during migration windows.

## 8. Revision history

| Version | Date | Notes |
| --- | --- | --- |
| 0.1.0 | 2026-10-10 | Initial public draft. |

Changes from the pre-release draft, folded into 0.1.0 before publication:

- Added `bonds` and `precedences` to `graph_edges` (the draft defined bond/precedence concepts but had no encoding for them).
- Direction vectors are `[x, y, z]` arrays everywhere (the draft mixed arrays and `{x, y, z}` objects).
- Added `bonding_attributes` to `bonding` nodes; formalized the `removal_method` vocabulary.
- Clarified execution plan semantics: array order is the execution order; `step_id` need not be sequential.
- Permitted `x-*` vendor extension keys (ignored but preserved by conforming tools).
