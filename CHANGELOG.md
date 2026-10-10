# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-10-10

Initial public draft.

### Added

- **OD-BOM v0.1.0 JSON Schema** (`schemas/v0.1.0/odbom.schema.json`): nodes (structural parts, fasteners, bonds, sub-assemblies), fastener/bond/interference/precedence edges, robotic execution plans with tools, trajectories, clearances, and fallback strategies; `x-*` vendor extension keys permitted and preserved.
- **`decad` Python package**: JSON Schema validation plus semantic checks (unique ids, reference resolution, node-type rules, DAG acyclicity, plan-order and precedence consistency), constraint-graph analysis (deterministic topological removal order, Graphviz DOT export), and document summaries.
- **CLI** (`decad validate | summary | order | dot`) with `--json` machine-readable output.
- **Reference examples**: EV battery pack module and generic smartphone teardown.
- **Specification** (`docs/specification.md`) with conformance clauses, governance/versioning policy, and ecosystem roadmap.
- Bilingual README (English / 日本語), contributing guide, and CI (Python 3.10–3.13 matrix; lint, tests, example validation).

### Notes on the format vs. the pre-release draft

- Added `graph_edges.bonds` and `graph_edges.precedences` (the draft defined bond/precedence concepts but had no encoding).
- Direction vectors are `[x, y, z]` arrays everywhere (the draft mixed arrays and `{x, y, z}` objects).
- Added `bonding_attributes` for `bonding` nodes; formalized the `removal_method` vocabulary.
- Clarified execution plan semantics: array order is the execution order; `step_id` must be unique but need not be sequential.
