import sys
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# ==========================================
# 1. UniProt API (基本情報)
# ==========================================
def get_uniprot_info(gene_name: str) -> Optional[Dict[str, Any]]:
    print(f"[*] UniProt APIへ '{gene_name}' の情報をリクエストしています...")
    url = f"https://rest.uniprot.org/uniprotkb/search?query=(gene_exact:{gene_name})+AND+(taxonomy_id:9606)&format=json"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        results = data.get('results', [])
        if not results:
            print(f"[!] 警告: 遺伝子 '{gene_name}' のデータが見つかりませんでした。")
            return None
            
        entry = results[0]
        uniprot_id = entry.get('primaryAccession', 'N/A')
        protein_name = entry.get('proteinDescription', {}).get('recommendedName', {}).get('fullName', {}).get('value', 'N/A')
        genes = entry.get('genes', [{}])
        primary_gene_name = genes[0].get('geneName', {}).get('value', gene_name) if genes else gene_name
        
        function_text = "N/A"
        subcellular_locations = []
        for comment in entry.get('comments', []):
            comment_type = comment.get('commentType')
            if comment_type == 'FUNCTION':
                texts = comment.get('texts', [])
                if texts: function_text = texts[0].get('value', 'N/A')
            elif comment_type == 'SUBCELLULAR LOCATION':
                for sub_loc in comment.get('subcellularLocations', []):
                    loc_value = sub_loc.get('location', {}).get('value')
                    if loc_value: subcellular_locations.append(loc_value)
                        
        location_text = ", ".join(subcellular_locations) if subcellular_locations else "N/A"
        
        return {
            "UniProt_ID": uniprot_id,
            "Protein_Name": protein_name,
            "Gene_Name": primary_gene_name,
            "Function": function_text,
            "Subcellular_Location": location_text
        }
    except Exception as e:
        print(f"[-] UniProt APIエラー: {e}")
        return None

# ==========================================
# 2. STRING API (相互作用)
# ==========================================
def get_string_interactions(protein_name: str, limit: int = 15) -> Optional[Dict[str, Any]]:
    print(f"[*] STRING APIへ '{protein_name}' の相互作用ネットワークをリクエストしています...")
    id_url = "https://version-12-0.string-db.org/api/json/get_string_ids"
    try:
        id_response = requests.get(id_url, params={"identifiers": protein_name, "species": 9606, "limit": 1}, timeout=15)
        id_response.raise_for_status()
        id_data = id_response.json()
        if not id_data: return None
            
        string_id = id_data[0]["stringId"]
        net_url = "https://version-12-0.string-db.org/api/json/network"
        net_response = requests.get(net_url, params={"identifiers": string_id, "species": 9606, "required_score": 400}, timeout=15)
        net_response.raise_for_status()
        
        interactors = []
        for edge in net_response.json():
            name_a, name_b = edge.get("preferredName_A", ""), edge.get("preferredName_B", "")
            score = edge.get("score", 0.0)
            partner = name_b if name_a.upper() == protein_name.upper() else name_a
            if partner.upper() != protein_name.upper():
                if not any(item['partner_gene'] == partner for item in interactors):
                    interactors.append({"partner_gene": partner, "interaction_score": score})
        
        interactors = sorted(interactors, key=lambda x: x["interaction_score"], reverse=True)[:limit]
        return {"Target_Protein": protein_name, "Total_Interactors_Found": len(interactors), "Top_Interactors": interactors}
    except Exception as e:
        print(f"[-] STRING APIエラー: {e}")
        return None

# ==========================================
# 3. OmniPath API (シグナル上下流)
# ==========================================
def get_signaling_flow(gene_name: str) -> Optional[Dict[str, Any]]:
    print(f"[*] OmniPath APIへ '{gene_name}' のシグナル伝達経路をリクエストしています...")
    url = "https://omnipathdb.org/interactions"
    params = {"genesymbols": 1, "partners": gene_name}
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        lines = response.text.strip().split('\n')
        if len(lines) < 2: return None
            
        headers = lines[0].split('\t')
        upstream_list, downstream_list = [], []
        query_upper = gene_name.upper()
        
        for line in lines[1:]:
            interaction = dict(zip(headers, line.split('\t')))
            is_directed = str(interaction.get("is_directed", "")).strip() in ["1", "True", "true"]
            is_stimulation = str(interaction.get("is_stimulation", "")).strip() in ["1", "True", "true"]
            is_inhibition = str(interaction.get("is_inhibition", "")).strip() in ["1", "True", "true"]
            
            if not (is_directed or is_stimulation or is_inhibition): continue
                
            source_raw = interaction.get("source_genesymbol") or interaction.get("source", "")
            target_raw = interaction.get("target_genesymbol") or interaction.get("target", "")
            if source_raw.upper() == target_raw.upper(): continue
            
            effect = "Unknown"
            if is_stimulation and is_inhibition: effect = "Both (Context-dependent)"
            elif is_stimulation: effect = "Activation (->)"
            elif is_inhibition: effect = "Inhibition (-|)"
            
            if target_raw.upper() == query_upper:
                upstream_list.append({"gene": source_raw, "effect": effect})
            elif source_raw.upper() == query_upper:
                downstream_list.append({"gene": target_raw, "effect": effect})
                
        upstream_list = [dict(t) for t in {tuple(d.items()) for d in upstream_list}]
        downstream_list = [dict(t) for t in {tuple(d.items()) for d in downstream_list}]
        
        return {
            "Target_Gene": gene_name,
            "Upstream_Signals": sorted(upstream_list, key=lambda x: x['gene'])[:15],
            "Downstream_Signals": sorted(downstream_list, key=lambda x: x['gene'])[:15]
        }
    except Exception as e:
        print(f"[-] OmniPath APIエラー: {e}")
        return None

# ==========================================
# 4. KEGG API (パスウェイ)
# ==========================================
def get_kegg_pathways(gene_name: str) -> Optional[Dict[str, Any]]:
    print(f"[*] KEGG APIへ '{gene_name}' の情報をリクエストしています...")
    try:
        find_res = requests.get(f"https://rest.kegg.jp/find/genes/{gene_name}", timeout=15)
        kegg_gene_id = None
        for line in find_res.text.strip().split('\n'):
            if not line: continue
            parts = line.split('\t')
            if len(parts) >= 2 and gene_name.upper() in [g.strip().upper() for g in parts[1].split(';')[0].split(',')] and parts[0].startswith('hsa:'):
                kegg_gene_id = parts[0]
                break
        if not kegg_gene_id: return None
            
        list_res = requests.get("https://rest.kegg.jp/list/pathway/hsa", timeout=15)
        pathway_dict = {line.split('\t')[0]: line.split('\t')[1] for line in list_res.text.strip().split('\n') if len(line.split('\t')) >= 2}
        
        link_res = requests.get(f"https://rest.kegg.jp/link/pathway/{kegg_gene_id}", timeout=15)
        pathways = []
        for line in link_res.text.strip().split('\n'):
            if line:
                pathway_id = line.split('\t')[1].replace('path:', '')
                pathways.append({
                    "pathway_id": pathway_id,
                    "pathway_name": pathway_dict.get(pathway_id, "Unknown Pathway"),
                    "map_url": f"https://www.kegg.jp/pathway/{pathway_id}"
                })
        return {"Target_Gene": gene_name, "KEGG_Gene_ID": kegg_gene_id, "Total_Pathways": len(pathways), "Pathways": pathways}
    except Exception as e:
        print(f"[-] KEGG APIエラー: {e}")
        return None

# ==========================================
# 5. Open Targets API (疾患・創薬)
# ==========================================
def get_opentargets_info(gene_name: str) -> Optional[Dict[str, Any]]:
    print(f"[*] Open Targets APIへ '{gene_name}' の情報をリクエストしています...")
    graphql_url = "https://api.platform.opentargets.org/api/v4/graphql"
    search_query = """query searchTarget($queryString: String!) { search(queryString: $queryString, entityNames: ["target"]) { hits { id name } } }"""
    try:
        search_res = requests.post(graphql_url, json={"query": search_query, "variables": {"queryString": gene_name}}, timeout=15)
        hits = search_res.json().get("data", {}).get("search", {}).get("hits", [])
        if not hits: return None
            
        ensembl_id, approved_name = hits[0]["id"], hits[0]["name"]
        target_query = """query targetInfo($ensemblId: String!) { target(ensemblId: $ensemblId) { knownDrugs { count } associatedDiseases(page: {index: 0, size: 15}) { count rows { disease { name } score } } } }"""
        target_res = requests.post(graphql_url, json={"query": target_query, "variables": {"ensemblId": ensembl_id}}, timeout=15)
        target_info = target_res.json().get("data", {}).get("target", {})
        
        diseases = [{"disease_name": r.get("disease", {}).get("name", "Unknown"), "association_score": round(r.get("score", 0.0), 4)} 
                    for r in target_info.get("associatedDiseases", {}).get("rows", [])]
        
        return {
            "Target_Gene": gene_name, "Ensembl_ID": ensembl_id, "Approved_Name": approved_name,
            "Known_Drugs_Count": target_info.get("knownDrugs", {}).get("count", 0),
            "Total_Associated_Diseases": target_info.get("associatedDiseases", {}).get("count", 0),
            "Top_Diseases": diseases
        }
    except Exception as e:
        print(f"[-] Open Targets APIエラー: {e}")
        return None

# ==========================================
# 6. Report Generation (レポート生成)
# ==========================================
def generate_markdown_report(gene_name: str, output_dir: Path, data: dict):
    print(f"[*] '{gene_name}' の臨床開発戦略向けMarkdownレポートを作成中...")
    
    lines = []
    lines.append(f"# Target Molecule Strategic Report: {gene_name}")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. Candidate Indications
    lines.append("## 1. Candidate Indications (適応症候補)")
    ot = data.get("opentargets")
    if ot:
        lines.append(f"- **Total Associated Diseases:** {ot.get('Total_Associated_Diseases', 0)}")
        lines.append(f"- **Known Drugs targeting this molecule:** {ot.get('Known_Drugs_Count', 0)}\n")
        lines.append("### Top 15 Disease Associations")
        lines.append("| Rank | Disease Name | Association Score | Strategic Note |")
        lines.append("| :--- | :--- | :--- | :--- |")
        for i, dis in enumerate(ot.get('Top_Diseases', []), 1):
            lines.append(f"| {i} | {dis['disease_name']} | {dis['association_score']} |  |")
        lines.append("\n")
    else: lines.append("*No data available.*\n")

    # 2. MoA
    lines.append("## 2. Biological Rationale & Mechanism of Action (作用機序の裏付け)")
    up = data.get("uniprot")
    if up:
        lines.append(f"**Protein Name:** {up.get('Protein_Name', 'N/A')} (UniProt: {up.get('UniProt_ID', 'N/A')})")
        lines.append(f"**Subcellular Location:** {up.get('Subcellular_Location', 'N/A')}")
        lines.append(f"\n**Function Summary:**\n> {up.get('Function', 'N/A')}\n")
        
    om = data.get("omnipath")
    if om:
        lines.append("### Signaling Flow (1-Step Up/Downstream)")
        lines.append(f"**▼ Upstream (リガンド・活性化因子: {gene_name} を駆動するもの)**")
        upstreams = om.get("Upstream_Signals", [])
        if upstreams:
            for item in upstreams: lines.append(f"- {item['gene']} --[{item['effect']}]--> **{gene_name}**")
        else: lines.append("- *No upstream data found.*")
            
        lines.append(f"\n**▼ Downstream (エフェクター/PDマーカー候補: {gene_name} が駆動するもの)**")
        downstreams = om.get("Downstream_Signals", [])
        if downstreams:
            for item in downstreams: lines.append(f"- **{gene_name}** --[{item['effect']}]--> {item['gene']}")
        else: lines.append("- *No downstream data found.*")
        lines.append("\n")

    # 3. Interactions
    lines.append("## 3. Potential Combination Therapies & Interactions (併用療法・相互作用候補)")
    st = data.get("string")
    if st:
        lines.append("### Top 15 Interacting Partners (from STRING)")
        lines.append("| Rank | Partner Gene | Interaction Score |")
        lines.append("| :--- | :--- | :--- |")
        for i, inter in enumerate(st.get('Top_Interactors', []), 1):
            lines.append(f"| {i} | {inter['partner_gene']} | {inter['interaction_score']} |")
        lines.append("\n")
    else: lines.append("*No data available.*\n")

    # 4. Pathways
    lines.append("## 4. Pathway Maps (KEGG全体図)")
    kg = data.get("kegg")
    if kg:
        lines.append(f"- **Total Pathways:** {kg.get('Total_Pathways', 0)}")
        lines.append("*💡 ヒント: リンクをクリックすると、ブラウザで経路図が開きます。プレゼン資料等の作成にご活用ください。*")
        for pw in kg.get('Pathways', [])[:15]:
            lines.append(f"- [{pw['pathway_name']}]({pw['map_url']}) (`{pw['pathway_id']}`)")
        lines.append("\n")
    else: lines.append("*No data available.*\n")

    output_file = output_dir / f"{gene_name}_Strategic_Report.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[+] 戦略レポートの生成が完了しました: {output_file}")

# ==========================================
# 7. Master Pipeline (全体実行)
# ==========================================
def run_pipeline(target_gene: str):
    print(f"\n{'='*50}")
    print(f"🚀 臨床開発向け ターゲット情報収集パイプライン開始: {target_gene}")
    print(f"{'='*50}\n")
    
    # 出力フォルダの準備
    base_dir = Path.home() / "Documents" / "Samplecode"
    output_dir = base_dir / "Output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # データを格納する辞書
    collected_data = {}

    # 実行とJSON保存
    print("\n--- Step 1: UniProt (基本情報) ---")
    collected_data["uniprot"] = get_uniprot_info(target_gene)
    if collected_data["uniprot"]:
        with open(output_dir / f"{target_gene}_01_uniprot.json", "w", encoding="utf-8") as f: json.dump(collected_data["uniprot"], f, indent=4, ensure_ascii=False)

    print("\n--- Step 2: STRING (相互作用) ---")
    collected_data["string"] = get_string_interactions(target_gene)
    if collected_data["string"]:
        with open(output_dir / f"{target_gene}_02_string.json", "w", encoding="utf-8") as f: json.dump(collected_data["string"], f, indent=4, ensure_ascii=False)

    print("\n--- Step 3: OmniPath (シグナル上下流) ---")
    collected_data["omnipath"] = get_signaling_flow(target_gene)
    if collected_data["omnipath"]:
        with open(output_dir / f"{target_gene}_03_omnipath.json", "w", encoding="utf-8") as f: json.dump(collected_data["omnipath"], f, indent=4, ensure_ascii=False)

    print("\n--- Step 4: KEGG (パスウェイ) ---")
    collected_data["kegg"] = get_kegg_pathways(target_gene)
    if collected_data["kegg"]:
        with open(output_dir / f"{target_gene}_04_kegg.json", "w", encoding="utf-8") as f: json.dump(collected_data["kegg"], f, indent=4, ensure_ascii=False)

    print("\n--- Step 5: Open Targets (疾患・創薬) ---")
    collected_data["opentargets"] = get_opentargets_info(target_gene)
    if collected_data["opentargets"]:
        with open(output_dir / f"{target_gene}_05_opentargets.json", "w", encoding="utf-8") as f: json.dump(collected_data["opentargets"], f, indent=4, ensure_ascii=False)

    print("\n--- Step 6: Report Generation (戦略レポート生成) ---")
    generate_markdown_report(target_gene, output_dir, collected_data)
    
    print(f"\n{'='*50}")
    print(f"✨ 全パイプライン完了！")
    print(f"📄 最終レポート: {output_dir / f'{target_gene}_Strategic_Report.md'}")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "ERBB2"
    run_pipeline(target.upper())