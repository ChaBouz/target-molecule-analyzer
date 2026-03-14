import requests
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

def get_string_interactions(protein_name: str, limit: int = 15) -> Optional[Dict[str, Any]]:
    print(f"[*] STRING APIへ '{protein_name}' の相互作用ネットワークをリクエストしています...")
    
    # 1. まず遺伝子名からSTRINGの内部IDを取得する
    id_url = "https://version-12-0.string-db.org/api/json/get_string_ids"
    id_params = {
        "identifiers": protein_name,
        "species": 9606,
        "limit": 1
    }
    
    try:
        id_response = requests.get(id_url, params=id_params, timeout=15)
        id_response.raise_for_status()
        id_data = id_response.json()
        
        if not id_data:
            print(f"[!] 警告: タンパク質 '{protein_name}' のSTRING IDが見つかりませんでした。")
            return None
            
        string_id = id_data[0]["stringId"]
        
        # 2. 取得したSTRING IDを使ってネットワークを取得する
        net_url = "https://version-12-0.string-db.org/api/json/network"
        net_params = {
            "identifiers": string_id,
            "species": 9606,
            "required_score": 400  # 中程度以上の確度
        }
        
        net_response = requests.get(net_url, params=net_params, timeout=15)
        net_response.raise_for_status()
        net_data = net_response.json()
        
        interactors: List[Dict[str, Any]] = []
        
        for edge in net_data:
            name_a = edge.get("preferredName_A", "")
            name_b = edge.get("preferredName_B", "")
            score = edge.get("score", 0.0)
            
            partner = name_b if name_a.upper() == protein_name.upper() else name_a
            
            if partner.upper() != protein_name.upper():
                if not any(item['partner_gene'] == partner for item in interactors):
                    interactors.append({
                        "partner_gene": partner,
                        "interaction_score": score
                    })
        
        # スコア順にソートして上位を抽出
        interactors = sorted(interactors, key=lambda x: x["interaction_score"], reverse=True)
        top_interactors = interactors[:limit]
        
        extracted_info = {
            "Target_Protein": protein_name,
            "Total_Interactors_Found": len(interactors),
            "Top_Interactors": top_interactors
        }
        
        print(f"[+] '{protein_name}' の相互作用データ取得に成功しました (上位 {len(top_interactors)} 件を抽出)")
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
    
    result_data = get_string_interactions(target_gene, limit=15)
    
    if result_data:
        output_file = output_dir / f"002_{target_gene}_string.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=4, ensure_ascii=False)
            
        print(f"[+] 結果をファイルに保存しました: {output_file}")
        print("\n--- 取得結果プレビュー ---")
        print(f"ターゲット: {result_data['Target_Protein']}")
        for i, interactor in enumerate(result_data['Top_Interactors'][:5], 1):
            print(f"  {i}. {interactor['partner_gene']} (スコア: {interactor['interaction_score']})")
        print("--------------------------\n")