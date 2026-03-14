[日本語](#japanese) | [English](#english) 

---

<a id="japanese"></a>
# Target Molecule Analyzer 🧬

指定したターゲット遺伝子（ヒト）に関する生化学的・医学的な情報を、複数の主要なパブリックデータベースから自動で収集し、統合されたMarkdownレポートを生成するPythonパイプラインです。

## 🌟 特徴 (Features)

1回の実行で以下の4つのAPIへ自動でアクセスし、情報を集約します。
* **Open Targets:** 関連疾患（スコア付き）および既存薬の開発状況
* **UniProt:** タンパク質の基本情報、機能概要、細胞内局在
* **STRING:** タンパク質間相互作用（PPI）ネットワークの上位リスト
* **KEGG:** 関連するシグナル伝達パスウェイ（ハイライトされたマップURL付き）

## 📦 動作環境 (Prerequisites)

* Python 3.7 以上
* 外部ライブラリ: `requests`

## 🚀 インストール方法 (Installation)

1. このリポジトリをダウンロード（または `git clone`）します。
2. ターミナル（コマンドプロンプト）を開き、プロジェクトのフォルダに移動します。
3. 以下のコマンドを実行して、必要なライブラリをインストールします。

```bash
pip install -r requirements.txt
```

## 💡 使い方 (Usage)

ターミナルで以下のコマンドを実行します。引数に検索したい遺伝子名（例: `EGFR`, `ERBB2`, `TP53` など）を指定してください。

```bash
# 統合解析スクリプトを実行する場合
python target_analyzer.py EGFR
```

※ 引数を指定せずに実行した場合は、デフォルトで `EGFR` の解析が行われます。

### 📂 出力結果について

スクリプトを実行すると、ユーザーのホームディレクトリ内に自動的に出力フォルダが作成され、そこにJSONデータとMarkdownレポートが保存されます。

* **保存先:** `~/Documents/Samplecode/Output/`
* **出力ファイル例:** * `EGFR_Comprehensive_Report.md` (最終的な統合レポート)
  * `EGFR_All_Data.json` (取得した全生データ)

## ⚠️ 免責事項 (Disclaimer)

* 本ツールは各パブリックデータベース（UniProt, STRING, KEGG, Open Targets）のAPIを利用しています。データの利用にあたっては、各データベースの利用規約（商用利用の制限など）に従ってください。
* 本ツールは研究および教育目的で作成されたものであり、出力される情報について医学的な正確性を保証するものではありません。

## 📄 ライセンス (License)

This project is licensed under the MIT License - see the LICENSE file for details.

---

<a id="english"></a>
# Target Molecule Analyzer 🧬

A Python pipeline that automatically collects biochemical and medical information about a specified target gene (human) from major public databases and generates an integrated Markdown report.

## 🌟 Features

With a single run, it automatically accesses the following four APIs and aggregates the information:
* **Open Targets:** Associated diseases (with scores) and known drug development status.
* **UniProt:** Basic protein information, functional overview, and subcellular location.
* **STRING:** Top list of Protein-Protein Interaction (PPI) networks.
* **KEGG:** Related signal transduction pathways (includes highlighted map URLs).

## 📦 Prerequisites

* Python 3.7 or higher
* External library: `requests`

## 🚀 Installation

1. Download or `git clone` this repository.
2. Open your terminal and navigate to the project folder.
3. Run the following command to install the required library:

```bash
pip install -r requirements.txt
```

## 💡 Usage

Run the following command in your terminal. Specify the target gene name (e.g., `EGFR`, `ERBB2`, `TP53`) as an argument.

```bash
# Run the integrated analysis script
python target_analyzer.py EGFR
```
*Note: If no argument is specified, the analysis will run for `EGFR` by default.*

### 📂 Output Details

Upon execution, an output folder is automatically created in your home directory, saving the JSON data and Markdown report.
* **Save Location:** `~/Documents/Samplecode/Output/`
* **Output Files Example:**
  * `EGFR_Comprehensive_Report.md` (Final integrated report)
  * `EGFR_All_Data.json` (All raw data retrieved)

## ⚠️ Disclaimer

* This tool utilizes APIs from public databases (UniProt, STRING, KEGG, Open Targets). Please adhere to the terms of service (e.g., restrictions on commercial use) of each database when using the data.
* This tool was created for research and educational purposes and does not guarantee the medical accuracy of the output information.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.