import json
from pathlib import Path
from datetime import datetime

def load_json(file_path: Path) -> dict:
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def generate_markdown_report(gene_name: str):
    print(f"[*] '{gene_name}' の統合Markdownレポートを作成中...")
    
    base_dir = Path.home() / "Documents" / "Samplecode" / "Output"
    
    uniprot_data = load_json(base_dir / f"001_{gene_name}_uniprot.json")
    string_data = load_json(base_dir / f"002_{gene_name}_string.json")
    kegg_data = load_json(base_dir / f"003_{gene_name}_kegg.json")
    ot_data = load_json(base_dir / f"004_{gene_name}_opentargets.json")
    
    report_lines = []
    report_lines.append(f"# Target Molecule Report: {gene_name}")
    report_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. UniProt
    report_lines.append("## 1. Basic Information (from UniProt)")
    if uniprot_data:
        report_lines.append(f"- **Protein Name:** {uniprot_data.get('Protein_Name', 'N/A')}")
        report_lines.append(f"- **UniProt ID:** {uniprot_data.get('UniProt_ID', 'N/A')}")
        report_lines.append(f"- **Subcellular Location:** {uniprot_data.get('Subcellular_Location', 'N/A')}")
        report_lines.append(f"\n**Function:**\n> {uniprot_data.get('Function', 'N/A')}\n")
    else:
        report_lines.append("*No data available. (※正式な遺伝子名(Official Symbol)で再検索するとヒットする場合があります)*\n")
        
    # 2. Open Targets
    report_lines.append("## 2. Drug & Disease Associations (from Open Targets)")
    if ot_data:
        report_lines.append(f"- **Known Drugs Count:** {ot_data.get('Known_Drugs_Count', 0)}")
        report_lines.append(f"- **Total Associated Diseases:** {ot_data.get('Total_Associated_Diseases', 0)}\n")
        report_lines.append("### Top 15 Associated Diseases")
        report_lines.append("| Rank | Disease Name | Association Score |")
        report_lines.append("| :--- | :--- | :--- |")
        for i, dis in enumerate(ot_data.get('Top_Diseases', [])[:15], 1):
            report_lines.append(f"| {i} | {dis['disease_name']} | {dis['association_score']} |")
        report_lines.append("\n")
    else:
        report_lines.append("*No data available.*\n")

    # 3. KEGG (💡ここが変更点: URLリンクの反映)
    report_lines.append("## 3. Biological Pathways (from KEGG)")
    if kegg_data:
        report_lines.append(f"- **Total Pathways:** {kegg_data.get('Total_Pathways', 0)}")
        report_lines.append("*💡 ヒント: パスウェイ名をクリックすると、ターゲット分子が赤くハイライトされたシグナル伝達経路図（上流/下流マップ）がブラウザで開きます。*\n")
        report_lines.append("### Relevant Pathways")
        for pw in kegg_data.get('Pathways', [])[:15]:
            # map_url があればリンク化、なければテキストのみ
            if 'map_url' in pw:
                report_lines.append(f"- [{pw['pathway_name']}]({pw['map_url']}) (`{pw['pathway_id']}`)")
            else:
                report_lines.append(f"- {pw['pathway_name']} (`{pw['pathway_id']}`)")
        report_lines.append("\n")
    else:
        report_lines.append("*No data available.*\n")

    # 4. STRING
    report_lines.append("## 4. Protein Interactions (from STRING)")
    if string_data:
        report_lines.append("### Top 15 Interacting Partners")
        report_lines.append("| Rank | Partner Gene | Interaction Score |")
        report_lines.append("| :--- | :--- | :--- |")
        for i, inter in enumerate(string_data.get('Top_Interactors', [])[:15], 1):
            report_lines.append(f"| {i} | {inter['partner_gene']} | {inter['interaction_score']} |")
        report_lines.append("\n")
    else:
        report_lines.append("*No data available.*\n")

    output_file = base_dir / f"{gene_name}_Comprehensive_Report.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"[+] レポートの生成が完了しました: {output_file}")

if __name__ == "__main__":
    target_gene = "ERBB2"
    generate_markdown_report(target_gene)