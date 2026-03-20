import json
from pathlib import Path
from datetime import datetime

def load_json(file_path: Path) -> dict:
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def generate_markdown_report(gene_name: str):
    print(f"[*] '{gene_name}' の臨床開発戦略向けMarkdownレポートを作成中...")
    
    base_dir = Path.home() / "Documents" / "Samplecode" / "Output"
    
    # 新しい連番に合わせてJSONを読み込み
    uniprot_data = load_json(base_dir / f"001_{gene_name}_uniprot.json")
    string_data = load_json(base_dir / f"002_{gene_name}_string.json")
    omnipath_data = load_json(base_dir / f"003_{gene_name}_omnipath.json")
    kegg_data = load_json(base_dir / f"004_{gene_name}_kegg.json")
    ot_data = load_json(base_dir / f"005_{gene_name}_opentargets.json")
    
    report_lines = []
    report_lines.append(f"# Target Molecule Strategic Report: {gene_name}")
    report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # --- 【戦略的配置 1】 最も重要な疾患適応症を一番上に ---
    report_lines.append("## 1. Candidate Indications (適応症候補)")
    if ot_data:
        report_lines.append(f"- **Total Associated Diseases:** {ot_data.get('Total_Associated_Diseases', 0)}")
        report_lines.append(f"- **Known Drugs targeting this molecule:** {ot_data.get('Known_Drugs_Count', 0)}\n")
        report_lines.append("### Top 15 Disease Associations")
        report_lines.append("| Rank | Disease Name | Association Score | Strategic Note |")
        report_lines.append("| :--- | :--- | :--- | :--- |")
        for i, dis in enumerate(ot_data.get('Top_Diseases', [])[:15], 1):
            report_lines.append(f"| {i} | {dis['disease_name']} | {dis['association_score']} |  |")
        report_lines.append("\n")
    else:
        report_lines.append("*No data available.*\n")

    # --- 【戦略的配置 2】 作用機序(MoA)の裏付け ---
    report_lines.append("## 2. Biological Rationale & Mechanism of Action (作用機序の裏付け)")
    if uniprot_data:
        report_lines.append(f"**Protein Name:** {uniprot_data.get('Protein_Name', 'N/A')} (UniProt: {uniprot_data.get('UniProt_ID', 'N/A')})")
        report_lines.append(f"**Subcellular Location:** {uniprot_data.get('Subcellular_Location', 'N/A')}")
        report_lines.append(f"\n**Function Summary:**\n> {uniprot_data.get('Function', 'N/A')}\n")
        
    if omnipath_data:
        report_lines.append("### Signaling Flow (1-Step Up/Downstream)")
        report_lines.append(f"**▼ Upstream (リガンド・活性化因子: {gene_name} を駆動するもの)**")
        upstreams = omnipath_data.get("Upstream_Signals", [])
        if upstreams:
            for item in upstreams:
                report_lines.append(f"- {item['gene']} --[{item['effect']}]--> **{gene_name}**")
        else:
            report_lines.append("- *No upstream data found.*")
            
        report_lines.append(f"\n**▼ Downstream (エフェクター/PDマーカー候補: {gene_name} が駆動するもの)**")
        downstreams = omnipath_data.get("Downstream_Signals", [])
        if downstreams:
            for item in downstreams:
                report_lines.append(f"- **{gene_name}** --[{item['effect']}]--> {item['gene']}")
        else:
            report_lines.append("- *No downstream data found.*")
        report_lines.append("\n")

    # --- 【戦略的配置 3】 併用療法や複合体の候補 ---
    report_lines.append("## 3. Potential Combination Therapies & Interactions (併用療法・相互作用候補)")
    if string_data:
        report_lines.append("### Top 15 Interacting Partners (from STRING)")
        report_lines.append("| Rank | Partner Gene | Interaction Score |")
        report_lines.append("| :--- | :--- | :--- |")
        for i, inter in enumerate(string_data.get('Top_Interactors', [])[:15], 1):
            report_lines.append(f"| {i} | {inter['partner_gene']} | {inter['interaction_score']} |")
        report_lines.append("\n")
    else:
        report_lines.append("*No data available.*\n")

    # --- 【戦略的配置 4】 パスウェイ全体図（参考資料） ---
    report_lines.append("## 4. Pathway Maps (KEGG全体図)")
    if kegg_data:
        report_lines.append(f"- **Total Pathways:** {kegg_data.get('Total_Pathways', 0)}")
        report_lines.append("*💡 ヒント: リンクをクリックすると、ブラウザで経路図が開きます。プレゼン資料等の作成にご活用ください。*")
        for pw in kegg_data.get('Pathways', [])[:15]:
            if 'map_url' in pw:
                report_lines.append(f"- [{pw['pathway_name']}]({pw['map_url']}) (`{pw['pathway_id']}`)")
            else:
                report_lines.append(f"- {pw['pathway_name']} (`{pw['pathway_id']}`)")
        report_lines.append("\n")
    else:
        report_lines.append("*No data available.*\n")

    output_file = base_dir / f"{gene_name}_Strategic_Report.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"[+] レポートの生成が完了しました: {output_file}")

if __name__ == "__main__":
    target_gene = "ERBB2"
    generate_markdown_report(target_gene)