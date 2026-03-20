import requests
import json
from pathlib import Path
from typing import Optional, Dict, Any

def get_opentargets_info(gene_name: str) -> Optional[Dict[str, Any]]:
    """
    Open Targets Platform (GraphQL API) から、指定した遺伝子の
    関連疾患（上位15件）と既存薬（Known Drugs）の数を取得する関数。
    """
    print(f"[*] Open Targets APIへ '{gene_name}' の情報をリクエストしています...")
    
    graphql_url = "https://api.platform.opentargets.org/api/v4/graphql"
    
    # 【ステップA】遺伝子名(Symbol)からEnsembl IDを検索するGraphQLクエリ
    search_query = """
    query searchTarget($queryString: String!) {
      search(queryString: $queryString, entityNames: ["target"]) {
        hits {
          id
          name
        }
      }
    }
    """
    
    try:
        # 1. Ensembl IDの取得
        search_res = requests.post(
            graphql_url, 
            json={"query": search_query, "variables": {"queryString": gene_name}},
            timeout=15
        )
        search_res.raise_for_status()
        search_data = search_res.json()
        
        hits = search_data.get("data", {}).get("search", {}).get("hits", [])
        if not hits:
            print(f"[!] 警告: Open Targets上で '{gene_name}' のIDが見つかりませんでした。")
            return None
            
        ensembl_id = hits[0]["id"]
        approved_name = hits[0]["name"]
        
        # 【ステップB】Ensembl IDを使って、関連疾患と既存薬のデータを取得するクエリ
        target_query = """
        query targetInfo($ensemblId: String!) {
          target(ensemblId: $ensemblId) {
            knownDrugs {
              count
            }
            associatedDiseases(page: {index: 0, size: 15}) {
              count
              rows {
                disease {
                  name
                }
                score
              }
            }
          }
        }
        """
        
        # 2. 疾患・医薬品情報の取得
        target_res = requests.post(
            graphql_url, 
            json={"query": target_query, "variables": {"ensemblId": ensembl_id}},
            timeout=15
        )
        target_res.raise_for_status()
        target_data = target_res.json()
        
        target_info = target_data.get("data", {}).get("target", {})
        
        # データ抽出
        known_drugs_count = target_info.get("knownDrugs", {}).get("count", 0)
        total_diseases = target_info.get("associatedDiseases", {}).get("count", 0)
        
        diseases_list = []
        for row in target_info.get("associatedDiseases", {}).get("rows", []):
            disease_name = row.get("disease", {}).get("name", "Unknown")
            score = row.get("score", 0.0)
            diseases_list.append({
                "disease_name": disease_name,
                "association_score": round(score, 4)
            })
            
        extracted_info = {
            "Target_Gene": gene_name,
            "Ensembl_ID": ensembl_id,
            "Approved_Name": approved_name,
            "Known_Drugs_Count": known_drugs_count,
            "Total_Associated_Diseases": total_diseases,
            "Top_Diseases": diseases_list
        }
        
        print(f"[+] '{gene_name}' のデータ取得に成功しました (関連疾患数: {total_diseases}, 既存薬数: {known_drugs_count})")
        return extracted_info

    except requests.exceptions.RequestException as e:
        print(f"[-] API通信エラーが発生しました: {e}")
        return None
    except Exception as e:
        print(f"[-] 予期せぬエラーが発生しました: {e}")
        return None

if __name__ == "__main__":
    target_gene = "ERBB2"
    base_dir = Path.home() / "Documents" / "Samplecode"
    output_dir = base_dir / "Output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result_data = get_opentargets_info(target_gene)
    
    if result_data:
        output_file = output_dir / f"004_{target_gene}_opentargets.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=4, ensure_ascii=False)
            
        print(f"[+] 結果をファイルに保存しました: {output_file}")
        print("\n--- 取得結果プレビュー ---")
        print(f"ターゲット: {result_data['Target_Gene']} ({result_data['Ensembl_ID']})")
        print(f"開発済みの既存薬(Known Drugs)の数: {result_data['Known_Drugs_Count']}")
        print("【関連疾患スコア上位5件】")
        for i, dis in enumerate(result_data['Top_Diseases'][:5], 1):
            print(f"  {i}. {dis['disease_name']} (スコア: {dis['association_score']})")
        print("--------------------------\n")