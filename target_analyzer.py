import sys
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# ==========================================
# 1. Open Targets API (疾患・既存薬情報 ＆ 正式名称の取得)
# ==========================================
def get_opentargets_info(gene_name: str) -> Optional[Dict[str, Any]]:
    print(f"[*] Open Targets APIへ '{gene_name}' の情報をリクエストしています...")
    graphql_url = "https://api.platform.opentargets.org/api/v4/graphql"
    try:
        search_query = 'query searchTarget($qs: String!) { search(queryString: $qs, entityNames: ["target"]) { hits { id approvedSymbol name } } }'
        search_res = requests.post(graphql_url, json={"query": search_query, "variables": {"qs": gene_name}}, timeout=15)
        hits = search_res.json().get("data", {}).get("search", {}).get("hits", [])
        if not hits: return None
        
        ensembl_id = hits[0]["id"]
        approved_symbol = hits[0].get("approvedSymbol", gene_name) # 正式名称を取得
        
        target_query = 'query targetInfo($id: String!) { target(ensemblId: $id) { knownDrugs { count } associatedDiseases(page: {index: 0, size: 15}) { count rows { disease { name } score } } } }'
        target_res = requests.post(graphql_url, json={"query": target_query, "variables": {"id": ensembl_id}}, timeout=15)
        target_info = target_res.json().get("data", {}).get("target", {})
        
        diseases = [{"disease_name": r.get("disease", {}).get("name"), "association_score": round(r.get("score", 0), 4)} for r in target_info.get("associatedDiseases", {}).get("rows", [])]
        return {
            "Original_Input": gene_name,
            "Approved_Symbol": approved_symbol,
            "Ensembl_ID": ensembl_id,
            "Known_Drugs_Count": target_info.get("knownDrugs", {}).get("count", 0),
            "Total_Associated_Diseases": target_info.get("associatedDiseases", {}).get("count", 0),
            "Top_Diseases": diseases
        }
    except Exception as e:
        print(f"[-] Open Targets エラー: {e}")
        return None

# ==========================================
# 2. UniProt API (基本情報・細胞内局在)
# ==========================================
def get_uniprot_info(gene_name: str) -> Optional[Dict[str, Any]]:
    print(f"[*] UniProt APIへ '{gene_name}' の情報をリクエストしています...")
    url = f"https://rest.uniprot.org/uniprotkb/search?query=(gene_exact:{gene_name})+AND+(taxonomy_id:9606)&format=json"
    try:
        response = requests.get(url, timeout=15)
        results = response.json().get('results', [])
        if not results: return None
        entry = results[0]
        
        subcellular_locations = []
        function_text = "N/A"
        for comment in entry.get('comments', []):
            if comment.get('commentType') == 'FUNCTION':
                texts = comment.get('texts', [])
                if texts: function_text = texts[0].get('value', 'N/A')
            elif comment.get('commentType') == 'SUBCELLULAR LOCATION':
                for sub_loc in comment.get('subcellularLocations', []):
                    loc_value = sub_loc.get('location', {}).get('value')
                    if loc_value: subcellular_locations.append(loc_value)
                    
        return {
            "UniProt_ID": entry.get('primaryAccession', 'N/A'),
            "Protein_Name": entry.get('proteinDescription', {}).get('recommendedName', {}).get('fullName', {}).get('value', 'N/A'),
            "Function": function_text,
            "Subcellular_Location": ", ".join(subcellular_locations) if subcellular_locations else "N/A"
        }
    except Exception as e:
        print(f"[-] UniProt エラー: {e}")
        return None

# ==========================================
# 3. STRING API (相互作用ネットワーク)
# ==========================================
def get_string_interactions(gene_name: str, limit: int = 15) -> Optional[Dict[str, Any]]:
    print(f"[*] STRING APIへ '{gene_name}' の情報をリクエストしています...")
    try:
        id_url = "https://version-12-0.string-db.org/api/json/get_string_ids"
        id_res = requests.get(id_url, params={"identifiers": gene_name, "species": 9606, "limit": 1}, timeout=15)
        if not id_res.json(): return None
        string_id = id_res.json()[0]["stringId"]
        
        net_url = "https://version-12-0.string-db.org/api/json/network"
        net_res = requests.get(net_url, params={"identifiers": string_id, "species": 9606, "required_score": 400}, timeout=15)
        
        interactors = []
        for edge in net_res.json():
            partner = edge.get("preferredName_B") if edge.get("preferredName_A").upper() == gene_name.upper() else edge.get("preferredName_A")
            if partner.upper() != gene_name.upper() and not any(item['partner_gene'] == partner for item in interactors):
                interactors.append({"partner_gene": partner, "interaction_score": edge.get("score", 0.0)})
                
        interactors = sorted(interactors, key=lambda x: x["interaction_score"], reverse=True)[:limit]
        return {"Total_Interactors_Found": len(interactors), "Top_Interactors": interactors}
    except Exception as e:
        print(f"[-] STRING エラー: {e}")
        return None

# ==========================================
# 4. KEGG API (パスウェイ情報とマップURL)
# ==========================================
def get_kegg_pathways(gene_name: str) -> Optional[Dict[str, Any]]:
    print(f"[*] KEGG APIへ '{gene_name}' の情報をリクエストしています...")
    try:
        find_res = requests.get(f"https://rest.kegg.jp/find/genes/{gene_name}", timeout=15)
        kegg_gene_id = None
        for line in find_res.text.strip().split('\n'):
            if line and len(line.split('\t')) >= 2:
                symbols = [g.strip().upper() for g in line.split('\t')[1].split(';')[0].split(',')]
                if gene_name.upper() in symbols and line.startswith('hsa:'):
                    kegg_gene_id = line.split('\t')[0]
                    break
        if not kegg_gene_id: return None

        list_res = requests.get("https://rest.kegg.jp/list/pathway/hsa", timeout=15)
        pathway_dict = {line.split('\t')[0]: line.split('\t')[1] for line in list_res.text.strip().split('\n') if len(line.split('\t')) >= 2}
        
        link_res = requests.get(f"https://rest.kegg.jp/link/pathway/{kegg_gene_id}", timeout=15)
        pathways = []
        for line in link_res.text.strip().split('\n'):
            if line and len(line.split('\t')) >= 2:
                clean_id = line.split('\t')[1].replace('path:', '')
                # 💡【修正】ハイライト専用のCGIエンドポイントのURLを使用
                map_url = f"https://www.kegg.jp/kegg-bin/show_pathway?{clean_id}+{kegg_gene_id}"
                pathways.append({
                    "pathway_id": clean_id, 
                    "pathway_name": pathway_dict.get(clean_id, "Unknown Pathway"),
                    "map_url": map_url
                })
                
        return {"KEGG_Gene_ID": kegg_gene_id, "Total_Pathways": len(pathways), "Pathways": pathways}
    except Exception as e:
        print(f"[-] KEGG エラー: {e}")
        return None

# ==========================================
# 5. メインパイプライン & レポート生成
# ==========================================
def generate_markdown(input_target: str, official_target: str, data: dict, output_dir: Path):
    lines = [
        f"# Target Molecule Report: {official_target}",
        f"*(Searched as: {input_target})*" if input_target != official_target else "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        
        "## 1. Basic Information (from UniProt)",
        f"- **Protein Name:** {data['uniprot'].get('Protein_Name', 'N/A')}" if data['uniprot'] else "*No data available.*",
        f"- **UniProt ID:** {data['uniprot'].get('UniProt_ID', 'N/A')}" if data['uniprot'] else "",
        f"- **Subcellular Location:** {data['uniprot'].get('Subcellular_Location', 'N/A')}" if data['uniprot'] else "",
        f"\n**Function:**\n> {data['uniprot'].get('Function', 'N/A')}\n" if data['uniprot'] else "\n",
        
        "## 2. Drug & Disease Associations (from Open Targets)",
        f"- **Known Drugs Count:** {data['opentargets'].get('Known_Drugs_Count', 0)}" if data['opentargets'] else "*No data available.*",
        f"- **Total Associated Diseases:** {data['opentargets'].get('Total_Associated_Diseases', 0)}\n" if data['opentargets'] else "",
    ]
    
    if data['opentargets'] and data['opentargets'].get('Top_Diseases'):
        lines.extend(["### Top 15 Associated Diseases", "| Rank | Disease Name | Association Score |", "| :--- | :--- | :--- |"])
        lines.extend([f"| {i} | {d['disease_name']} | {d['association_score']} |" for i, d in enumerate(data['opentargets']['Top_Diseases'], 1)])
        lines.append("\n")

    lines.append("## 3. Biological Pathways (from KEGG)")
    if data['kegg']:
        lines.append(f"- **Total Pathways:** {data['kegg'].get('Total_Pathways', 0)}")
        lines.append("*💡 ヒント: パスウェイ名をクリックすると、ターゲット分子が赤くハイライトされたシグナル伝達経路図（上流/下流マップ）がブラウザで開きます。*\n")
        lines.append("### Relevant Pathways")
        for pw in data['kegg'].get('Pathways', [])[:15]:
            if 'map_url' in pw:
                lines.append(f"- [{pw['pathway_name']}]({pw['map_url']}) (`{pw['pathway_id']}`)")
            else:
                lines.append(f"- {pw['pathway_name']} (`{pw['pathway_id']}`)")
        lines.append("\n")
    else: lines.append("*No data available.*\n")

    lines.append("## 4. Protein Interactions (from STRING)")
    if data['string']:
        lines.extend(["### Top 15 Interacting Partners", "| Rank | Partner Gene | Interaction Score |", "| :--- | :--- | :--- |"])
        lines.extend([f"| {i} | {p['partner_gene']} | {p['interaction_score']} |" for i, p in enumerate(data['string'].get('Top_Interactors', []), 1)])
    else: lines.append("*No data available.*\n")

    report_path = output_dir / f"{official_target}_Comprehensive_Report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return report_path

def main():
    target = sys.argv[1].upper() if len(sys.argv) > 1 else "EGFR"
    print(f"\n{'='*50}\n🚀 ターゲット解析開始: {target}\n{'='*50}\n")
    
    output_dir = Path.home() / "Documents" / "Samplecode" / "Output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. まずOpen Targetsを叩いて「正式名称(Approved Symbol)」を取得する
    ot_data = get_opentargets_info(target)
    official_symbol = ot_data.get("Approved_Symbol", target) if ot_data else target
    
    if target != official_symbol:
        print(f"[!] '{target}' の正式名称 '{official_symbol}' を検出しました。以降は正式名称で検索します。")
    
    # 2. 正式名称を使って他のAPIを叩く
    aggregated_data = {
        "opentargets": ot_data,
        "uniprot": get_uniprot_info(official_symbol),
        "string": get_string_interactions(official_symbol, limit=15),
        "kegg": get_kegg_pathways(official_symbol)
    }
    
    # 生データを1つのJSONにまとめて保存 (デバッグや後方互換用)
    with open(output_dir / f"{official_symbol}_All_Data.json", "w", encoding="utf-8") as f:
        json.dump(aggregated_data, f, indent=4, ensure_ascii=False)
        
    # Markdownレポートの生成
    report_file = generate_markdown(target, official_symbol, aggregated_data, output_dir)
    
    print(f"\n{'='*50}\n✨ 解析完了！\n📄 レポート: {report_file}\n{'='*50}\n")

if __name__ == "__main__":
    main()