import requests
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

def get_kegg_pathways(gene_name: str) -> Optional[Dict[str, Any]]:
    """
    KEGG APIから指定した遺伝子（ヒト）が関与するパスウェイを取得する関数。
    ※マップのURL（上流・下流の可視化）も同時に生成します。
    """
    print(f"[*] KEGG APIへ '{gene_name}' の情報をリクエストしています...")
    
    try:
        # 1. 遺伝子名からKEGGの遺伝子ID (hsa:XXXX) を検索
        find_url = f"https://rest.kegg.jp/find/genes/{gene_name}"
        find_res = requests.get(find_url, timeout=15)
        find_res.raise_for_status()
        
        kegg_gene_id = None
        for line in find_res.text.strip().split('\n'):
            if not line: continue
            parts = line.split('\t')
            if len(parts) >= 2:
                gene_symbols = [g.strip().upper() for g in parts[1].split(';')[0].split(',')]
                if gene_name.upper() in gene_symbols and parts[0].startswith('hsa:'):
                    kegg_gene_id = parts[0]
                    break
                    
        if not kegg_gene_id:
            print(f"[!] 警告: KEGG上で '{gene_name}' のヒト遺伝子IDが見つかりませんでした。")
            return None
            
        # 2. ヒトの全パスウェイ名リストを取得
        list_url = "https://rest.kegg.jp/list/pathway/hsa"
        list_res = requests.get(list_url, timeout=15)
        list_res.raise_for_status()
        
        pathway_dict = {}
        for line in list_res.text.strip().split('\n'):
            if line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    pathway_dict[parts[0]] = parts[1]
                    
        # 3. 遺伝子IDから、関連するパスウェイIDを取得し、URLを生成
        link_url = f"https://rest.kegg.jp/link/pathway/{kegg_gene_id}"
        link_res = requests.get(link_url, timeout=15)
        link_res.raise_for_status()
        
        pathways: List[Dict[str, str]] = []
        for line in link_res.text.strip().split('\n'):
            if line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    pathway_id = parts[1]
                    clean_id = pathway_id.replace('path:', '')
                    pathway_name = pathway_dict.get(clean_id, "Unknown Pathway")
                    
                    # 💡 【修正】見やすい標準のパスウェイマップのURLに差し替え
                    map_url = f"https://www.kegg.jp/pathway/{clean_id}"
                    
                    pathways.append({
                        "pathway_id": clean_id,
                        "pathway_name": pathway_name,
                        "map_url": map_url
                    })
                    
        extracted_info = {
            "Target_Gene": gene_name,
            "KEGG_Gene_ID": kegg_gene_id,
            "Total_Pathways": len(pathways),
            "Pathways": pathways
        }
        
        print(f"[+] '{gene_name}' のパスウェイデータ取得に成功しました ({len(pathways)} 件)")
        return extracted_info

    except requests.exceptions.RequestException as e:
        print(f"[-] APIリクエストエラーが発生しました: {e}")
        return None
    except Exception as e:
        print(f"[-] 予期せぬエラーが発生しました: {e}")
        return None

if __name__ == "__main__":
    target_gene = "ERBB2"
    base_dir = Path.home() / "Documents" / "Samplecode"
    output_dir = base_dir / "Output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result_data = get_kegg_pathways(target_gene)
    
    if result_data:
        output_file = output_dir / f"003_{target_gene}_kegg.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=4, ensure_ascii=False)
            
        print(f"[+] 結果をファイルに保存しました: {output_file}")