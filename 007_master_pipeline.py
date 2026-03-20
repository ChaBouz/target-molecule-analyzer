import sys
import json
import importlib
from pathlib import Path

def run_pipeline(target_gene: str):
    print(f"\n{'='*50}")
    print(f"🚀 臨床開発向け ターゲット情報収集パイプライン開始: {target_gene}")
    print(f"{'='*50}\n")
    
    base_dir = Path.home() / "Documents" / "Samplecode"
    output_dir = base_dir / "Output"
    output_dir.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(base_dir))
    
    try:
        mod1 = importlib.import_module("001_uniprot_api")
        mod2 = importlib.import_module("002_string_api")
        mod3 = importlib.import_module("003_omnipath_api")
        mod4 = importlib.import_module("004_kegg_api")
        mod5 = importlib.import_module("005_opentargets_api")
        mod6 = importlib.import_module("006_generate_report")
    except ImportError as e:
        print(f"[-] モジュールのインポートに失敗しました: {e}")
        print("各ステップのファイル名が 001〜006 の連番になっているか確認してください。")
        return

    print("\n--- Step 1: UniProt (基本情報) ---")
    res1 = mod1.get_uniprot_info(target_gene)
    if res1:
        with open(output_dir / f"001_{target_gene}_uniprot.json", "w", encoding="utf-8") as f:
            json.dump(res1, f, indent=4, ensure_ascii=False)
            
    print("\n--- Step 2: STRING (相互作用) ---")
    res2 = mod2.get_string_interactions(target_gene, limit=15)
    if res2:
        with open(output_dir / f"002_{target_gene}_string.json", "w", encoding="utf-8") as f:
            json.dump(res2, f, indent=4, ensure_ascii=False)
            
    print("\n--- Step 3: OmniPath (シグナル上下流) ---")
    res3 = mod3.get_signaling_flow(target_gene)
    if res3:
        with open(output_dir / f"003_{target_gene}_omnipath.json", "w", encoding="utf-8") as f:
            json.dump(res3, f, indent=4, ensure_ascii=False)

    print("\n--- Step 4: KEGG (パスウェイ) ---")
    res4 = mod4.get_kegg_pathways(target_gene)
    if res4:
        with open(output_dir / f"004_{target_gene}_kegg.json", "w", encoding="utf-8") as f:
            json.dump(res4, f, indent=4, ensure_ascii=False)
            
    print("\n--- Step 5: Open Targets (疾患・創薬) ---")
    res5 = mod5.get_opentargets_info(target_gene)
    if res5:
        with open(output_dir / f"005_{target_gene}_opentargets.json", "w", encoding="utf-8") as f:
            json.dump(res5, f, indent=4, ensure_ascii=False)
            
    print("\n--- Step 6: Report Generation (戦略レポート生成) ---")
    mod6.generate_markdown_report(target_gene)
    
    print(f"\n{'='*50}")
    print(f"✨ 全パイプライン完了！")
    print(f"📄 最終レポート: {output_dir / f'{target_gene}_Strategic_Report.md'}")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "ERBB2"
    run_pipeline(target.upper())