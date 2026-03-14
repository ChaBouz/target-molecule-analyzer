# 依存ライブラリのインストール: pip install requests
import requests
import json
from pathlib import Path
from typing import Optional, Dict, Any

def get_uniprot_info(gene_name: str) -> Optional[Dict[str, Any]]:
    """
    UniProt APIから指定した遺伝子（ヒト）のタンパク質情報を取得する関数。
    
    Args:
        gene_name (str): 検索する遺伝子名 (例: 'ERBB2')
        
    Returns:
        Optional[Dict[str, Any]]: 取得した情報の辞書。失敗時や見つからない場合はNone。
    """
    print(f"[*] UniProt APIへ '{gene_name}' の情報をリクエストしています...")
    
    # ヒト(9606)かつ遺伝子名完全一致で検索するエンドポイント
    url = f"https://rest.uniprot.org/uniprotkb/search?query=(gene_exact:{gene_name})+AND+(taxonomy_id:9606)&format=json"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        results = data.get('results', [])
        if not results:
            print(f"[!] 警告: 遺伝子 '{gene_name}' のデータが見つかりませんでした。")
            return None
            
        # 最初の結果（通常は最もスコアが高くReviewedなもの）を取得
        entry = results[0]
        
        # 1. UniProt ID
        uniprot_id = entry.get('primaryAccession', 'N/A')
        
        # 2. タンパク質名
        protein_name = entry.get('proteinDescription', {}).get('recommendedName', {}).get('fullName', {}).get('value', 'N/A')
        
        # 3. 遺伝子名 (複数ある場合は最初のものを取得)
        genes = entry.get('genes', [{}])
        primary_gene_name = genes[0].get('geneName', {}).get('value', gene_name) if genes else gene_name
        
        # 4. 機能概要 & 5. 細胞内局在 を Comments から抽出
        function_text = "N/A"
        subcellular_locations = []
        
        for comment in entry.get('comments', []):
            comment_type = comment.get('commentType')
            
            # 機能の抽出
            if comment_type == 'FUNCTION':
                texts = comment.get('texts', [])
                if texts:
                    function_text = texts[0].get('value', 'N/A')
            
            # 細胞内局在の抽出
            elif comment_type == 'SUBCELLULAR LOCATION':
                for sub_loc in comment.get('subcellularLocations', []):
                    loc_value = sub_loc.get('location', {}).get('value')
                    if loc_value:
                        subcellular_locations.append(loc_value)
                        
        location_text = ", ".join(subcellular_locations) if subcellular_locations else "N/A"
        
        # 抽出結果をまとめる
        extracted_info = {
            "UniProt_ID": uniprot_id,
            "Protein_Name": protein_name,
            "Gene_Name": primary_gene_name,
            "Function": function_text,
            "Subcellular_Location": location_text
        }
        
        print(f"[+] '{gene_name}' のデータ取得に成功しました (UniProt ID: {uniprot_id})")
        return extracted_info

    except requests.exceptions.RequestException as e:
        print(f"[-] APIリクエストエラーが発生しました: {e}")
        return None
    except json.JSONDecodeError:
        print("[-] レスポンスのJSON解析に失敗しました。")
        return None
    except Exception as e:
        print(f"[-] 予期せぬエラーが発生しました: {e}")
        return None

if __name__ == "__main__":
    # テスト用のターゲット遺伝子
    target_gene = "ERBB2"
    
    # OS依存を避けるパス設定 (Macの ~/Documents/Samplecode/Output)
    base_dir = Path.home() / "Documents" / "Samplecode"
    output_dir = base_dir / "Output"
    
    # フォルダが存在しない場合は作成する
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 実行
    result_data = get_uniprot_info(target_gene)
    
    if result_data:
        # 結果をJSONとして保存
        output_file = output_dir / f"001_{target_gene}_uniprot.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=4, ensure_ascii=False)
            
        print(f"[+] 結果をファイルに保存しました: {output_file}")
        
        # コンソールにもわかりやすく出力
        print("\n--- 取得結果プレビュー ---")
        for key, value in result_data.items():
            # 文字列が長すぎる場合は省略して表示
            display_value = value if len(str(value)) < 100 else str(value)[:100] + "..."
            print(f"{key}: {display_value}")
        print("--------------------------\n")