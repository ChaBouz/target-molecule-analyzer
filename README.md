[日本語](#japanese) | [English](#english) 

---

<a id="japanese"></a>
# Target Molecule Strategic Analyzer 🧬💊

指定したターゲット遺伝子（ヒト）に関する生化学的・医学的な情報を複数の主要なパブリックデータベースから自動で収集し、**臨床開発やポートフォリオ戦略の立案に特化した**統合Markdownレポートを生成するPythonツールです。

ユーザーの用途に合わせて、**「すぐに使える統合版」**と**「改造しやすいモジュール版」**の2つの形式を提供しています。

## 🌟 特徴 (Features)

1回の実行で以下の5つのデータベース/APIへ自動でアクセスし、戦略立案に最適な順序で情報を集約します。
* **Clinical-First Layout:** 臨床開発で最も重視される「適応症候補（関連疾患リスト）」と「既存薬の状況」をレポートの最上位に配置。
* **OmniPath:** シグナル伝達の「上流」と「下流」を方向性（活性化/抑制）とともに可視化し、作用機序（MoA）の裏付けをサポート。
* **Open Targets:** 関連疾患（スコア付き）および既存薬の開発状況。
* **UniProt:** タンパク質の基本情報、機能概要、細胞内局在。
* **STRING:** タンパク質間相互作用（PPI）ネットワークの上位リスト（併用療法のターゲット探索に活用）。
* **KEGG:** 関連するシグナル伝達パスウェイ（見やすい全体図のマップURLへのリンク）。

## 📁 リポジトリの構成 (Repository Structure)

本リポジトリには、用途に合わせた2種類の実行形式が含まれています。

1. **統合版スクリプト (`target_analyzer.py`)**
   * すべての機能が1つのファイルにまとまっています。**「とにかくツールとして手軽に使いたい」**という方に最適です。
2. **モジュール版スクリプト (`001` 〜 `007`)**
   * API取得やレポート生成の機能ごとにファイルが分割されています。**「特定のデータベースを追加したい」「自分でコードを改造・拡張したい」**という開発者・研究者向けです。

## 📦 動作環境 (Prerequisites)

* Python 3.7 以上
* 高速パッケージマネージャー: [uv](https://github.com/astral-sh/uv) (推奨)
* 外部ライブラリ: `requests`

## 🚀 使い方 (Usage)

面倒な事前インストールは不要です。`uv` を使えば1行のコマンドで実行できます。引数に検索したい遺伝子名（例: `ERBB2`, `EGFR`, `TP53` など）を指定してください。

**A. 統合版（1ファイル）を実行する場合:**
```bash
uv run --with requests target_analyzer.py ERBB2
```

**B. モジュール版を実行する場合:**
```bash
uv run --with requests 007_master_pipeline.py ERBB2
```

※ 引数を指定せずに実行した場合は、デフォルトで `ERBB2` の解析が行われます。

### 📂 出力結果について

実行すると、自動的に出力フォルダ（`~/Documents/Samplecode/Output/`）が作成され、生データ(JSON)と最終的な戦略レポート(`[遺伝子名]_Strategic_Report.md`)が保存されます。

---

<a id="english"></a>
# Target Molecule Strategic Analyzer 🧬💊

A Python tool that automatically collects biochemical and medical information about a specified target gene (human) from major public databases, generating an integrated Markdown report **tailored specifically for Clinical Development and Portfolio Strategy**.

We provide two formats to suit your needs: a **"Standalone Version"** for easy use, and a **"Modular Version"** for easy customization.

## 🌟 Features

* **Clinical-First Layout:** Places "Candidate Indications" and "Known Drug Status" at the very top of the report.
* **OmniPath Integration:** Extracts directional signaling cascades (Upstream/Downstream) with interaction types (Activation/Inhibition) to clarify MoA.
* **Open Targets:** Associated diseases and known drug development status.
* **UniProt:** Basic protein information and subcellular location.
* **STRING:** Top Protein-Protein Interaction (PPI) networks.
* **KEGG:** Related signal transduction pathways (with direct map URLs).

## 📁 Repository Structure

1. **Standalone Script (`target_analyzer.py`)**
   * All features in a single file. Best for **end-users** who want a simple, ready-to-use tool.
2. **Modular Scripts (`001` to `007`)**
   * Functions are split into separate files. Best for **developers/researchers** who want to customize, debug, or add new databases.

## 📦 Prerequisites

* Python 3.7 or higher
* Fast Python package installer: [uv](https://github.com/astral-sh/uv) (Highly Recommended)
* External library: `requests`

## 🚀 Usage

Using `uv`, you can run the tool in a single command. Specify the target gene name (e.g., `ERBB2`, `EGFR`) as an argument.

**A. To run the Standalone Version:**
```bash
uv run --with requests target_analyzer.py ERBB2
```

**B. To run the Modular Version:**
```bash
uv run --with requests 007_master_pipeline.py ERBB2
```

### 📂 Output Details

An output folder (`~/Documents/Samplecode/Output/`) will be automatically created, saving the intermediate JSON data and the final report (`[GENE]_Strategic_Report.md`).