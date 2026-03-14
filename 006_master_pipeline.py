import sys
import json
import importlib
from pathlib import Path

def run_pipeline(target_gene: str):
    print(f"\n{'='*50}")
    print(f"🚀 ターゲット情報収集パイプライン開始: {target_gene}")
    print(f"{'='*50}\n")
    
    base_dir = Path.home() / "Documents" / "Samplecode"
    output_dir = base_dir / "Output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # モジュール検索パスに Samplecode フォルダを追加
    sys.path.insert(0, str(base_dir))
    
    try:
        print("[*] 過去に作成したモジュール(001~005)を読み込んでいます...")
        mod1 = importlib.import_module("001_uniprot_api")
        mod2 = importlib.import_module("002_string_api")
        mod3 = importlib.import_module("003_kegg_api")
        mod4 = importlib.import_module("004_opentargets_api")
        mod5 = importlib.import_module("005_generate_report")
    except ImportError as e:
        print(f"[-] モジュールのインポートに失敗しました: {e}")
        print("各ステップのファイル (001~005) が Samplecode フォルダにあるか確認してください。")
        return

    # 1. UniProt
    print("\n--- Step 1: UniProt ---")
    res1 = mod1.get_uniprot_info(target_gene)
    if res1:
        with open(output_dir / f"001_{target_gene}_uniprot.json", "w", encoding="utf-8") as f:
            json.dump(res1, f, indent=4, ensure_ascii=False)
            
    # 2. STRING
    print("\n--- Step 2: STRING ---")
    res2 = mod2.get_string_interactions(target_gene, limit=15)
    if res2:
        with open(output_dir / f"002_{target_gene}_string.json", "w", encoding="utf-8") as f:
            json.dump(res2, f, indent=4, ensure_ascii=False)
            
    # 3. KEGG
    print("\n--- Step 3: KEGG ---")
    res3 = mod3.get_kegg_pathways(target_gene)
    if res3:
        with open(output_dir / f"003_{target_gene}_kegg.json", "w", encoding="utf-8") as f:
            json.dump(res3, f, indent=4, ensure_ascii=False)
            
    # 4. Open Targets
    print("\n--- Step 4: Open Targets ---")
    res4 = mod4.get_opentargets_info(target_gene)
    if res4:
        with open(output_dir / f"004_{target_gene}_opentargets.json", "w", encoding="utf-8") as f:
            json.dump(res4, f, indent=4, ensure_ascii=False)
            
    # 5. Report Generation
    print("\n--- Step 5: Report Generation ---")
    mod5.generate_markdown_report(target_gene)
    
    print(f"\n{'='*50}")
    print(f"✨ 全パイプライン完了！")
    print(f"📄 最終レポート: {output_dir / f'{target_gene}_Comprehensive_Report.md'}")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    # コマンドライン引数から遺伝子名を取得（指定がなければデフォルトで EGFR を実行）
    target = sys.argv[1] if len(sys.argv) > 1 else "EGFR"
    
    # 遺伝子名を大文字に統一して実行
    run_pipeline(target.upper())