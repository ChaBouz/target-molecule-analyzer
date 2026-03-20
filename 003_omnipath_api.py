import requests
import json
from pathlib import Path
from typing import Optional, Dict, Any

def get_signaling_flow(gene_name: str) -> Optional[Dict[str, Any]]:
    print(f"[*] OmniPath APIへ '{gene_name}' のシグナル伝達経路をリクエストしています...")
    
    url = "https://omnipathdb.org/interactions"
    params = {
        "genesymbols": 1,
        "partners": gene_name
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        lines = response.text.strip().split('\n')
        if len(lines) < 2:
            print(f"[!] 警告: OmniPath上で '{gene_name}' のデータが見つかりませんでした。")
            return None
            
        headers = lines[0].split('\t')
        upstream_list = []
        downstream_list = []
        query_upper = gene_name.upper()
        
        for line in lines[1:]:
            values = line.split('\t')
            interaction = dict(zip(headers, values))
            
            is_directed = str(interaction.get("is_directed", "")).strip() in ["1", "True", "true"]
            is_stimulation = str(interaction.get("is_stimulation", "")).strip() in ["1", "True", "true"]
            is_inhibition = str(interaction.get("is_inhibition", "")).strip() in ["1", "True", "true"]
            
            if not (is_directed or is_stimulation or is_inhibition):
                continue
                
            source_raw = interaction.get("source_genesymbol") or interaction.get("source", "")
            target_raw = interaction.get("target_genesymbol") or interaction.get("target", "")
            source_upper = source_raw.upper()
            target_upper = target_raw.upper()
            
            if source_upper == target_upper:
                continue
            
            effect = "Unknown"
            if is_stimulation and is_inhibition:
                effect = "Both (Context-dependent)"
            elif is_stimulation:
                effect = "Activation (->)"
            elif is_inhibition:
                effect = "Inhibition (-|)"
            
            if target_upper == query_upper:
                upstream_list.append({"gene": source_raw, "effect": effect})
            elif source_upper == query_upper:
                downstream_list.append({"gene": target_raw, "effect": effect})
                
        upstream_list = [dict(t) for t in {tuple(d.items()) for d in upstream_list}]
        downstream_list = [dict(t) for t in {tuple(d.items()) for d in downstream_list}]
        
        extracted_info = {
            "Target_Gene": gene_name,
            "Upstream_Signals": sorted(upstream_list, key=lambda x: x['gene'])[:15],
            "Downstream_Signals": sorted(downstream_list, key=lambda x: x['gene'])[:15]
        }
        
        print(f"[+] '{gene_name}' のシグナル伝達データ取得に成功しました。")
        return extracted_info

    except requests.exceptions.RequestException as e:
        print(f"[-] APIリクエストエラーが発生しました: {e}")
        return None