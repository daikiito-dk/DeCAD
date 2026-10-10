# DeCAD

[![CI](https://github.com/daikiito-dk/DeCAD/actions/workflows/ci.yml/badge.svg)](https://github.com/daikiito-dk/DeCAD/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/decad.svg)](https://pypi.org/project/decad/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

[English](README.md) | **日本語**

DeCADは、リバースCADと製品解体のためのオープンソースツールキットです。中核は **OD-BOM（Open Disassembly & Reverse BOM）** フォーマット、つまり物理製品が「どう分解されるか」を機械可読に記述するオープン標準です。製品の内容物、何が何を固定し、何が何の取り外しを妨げ、ロボットがどのような手順で分解できるかを記述します。

従来のeBOM/mBOMは製品が「どう組み立てられるか」を表します。OD-BOMはその逆、「どう解体されるか」を表します：リバース階層構造、干渉・優先順位の制約グラフ、取り外しステップごとの工具・軌跡要件、そしてサーキュラーエコノミー評価のためのEnd-of-Life材料分類です。

## 30秒でわかるフォーマット

```json
{
  "$schema": "https://open-disassembly.org/schemas/v0.1.0/odbom.schema.json",
  "metadata": { "odbom_version": "0.1.0", "product_id": "URN:PRODUCT:EV-BATTERY-PACK-2026", "name": "EVバッテリーパック" },
  "nodes": [
    { "id": "node_top_cover", "type": "structural_part", "label": "アルミ上部ハウジングカバー" },
    { "id": "node_m6_screw_01", "type": "fastener", "label": "M6 Torxネジ" },
    { "id": "node_cell_array_01", "type": "sub_assembly", "label": "Li-Ionポーチセルアレイ" }
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

注目すべき3点：

1. **ノードはEoL分類を持つ** — リサイクルカテゴリと危険物フラグがあり、回収価値計算にそのまま使えます。
2. **エッジはプランナーが使える制約** — ネジがカバーを固定し、カバーが+Z方向へのセルアレイの取り出しを妨げています。
3. **実行計画は検証可能** — `decad validate` が、計画の順序が制約グラフと矛盾しないことを機械的に証明します。

## インストール

PyPIで公開済みです（Python 3.10以上）：

```bash
pip install decad
```

開発用にチェックアウトから入れる場合（[uv](https://docs.astral.sh/uv/) 推奨）：

```bash
git clone https://github.com/daikiito-dk/DeCAD.git
cd DeCAD
make setup        # .venvを作成し -e ".[dev]" をインストール
```

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
doc.summary()  # 概要dict（タイプ別ノード数、危険物、エッジ、計画）
doc.to_dot()  # 制約グラフのGraphviz DOT
```

## リポジトリ構成

```
DeCAD/
├── schemas/            # バージョン管理されたOD-BOM JSON Schema（規格本体）
│   └── v0.1.0/odbom.schema.json
├── examples/           # 参照用 .odbom ドキュメント
├── docs/specification.md
├── src/decad/          # Pythonバリデータライブラリ + CLI
└── tests/              # スキーマ・意味論・グラフ・CLIのテスト
```

## スキーマのバージョニングとガバナンス

- スキーマはSemVerでバージョン管理し、`schemas/vX.Y.Z/` に公開します。
- 追加的な変更はマイナー、破壊的変更はメジャーを上げます。
- パッケージ同梱のスキーマコピー（`src/decad/_data/`）と正本が一致することをテストが強制します。
- 不明な `x-*` ベンダー拡張キーはどこでも許容され、適合ツールはそれを保存します。

## ロードマップ

- **フェーズ1（本リリース）：** OD-BOM v0.1.0 スキーマ、仕様書、参照バリデータ+CLI、サンプル、CI。
- **フェーズ2：** CADコンバータ（STEP / OpenSCAD / FreeCADからOD-BOMへの `decad convert`）、ROS 2統合パッケージ（ステップをビヘイビアツリーとMoveIt 2にマップする `ros2_odbom`）、Scan-to-CAD基線モデル（画像/点群 → CADコマンド列 → OD-BOM）。
- **フェーズ3：** 安定化した仕様をOSSロボティクス・サーキュラーエコノミーコンソーシアム（ROS-Industrial、Linux Foundation系プロジェクト等）に提出。

## コントリビューション

[CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。ライセンスは [Apache-2.0](LICENSE) です。
