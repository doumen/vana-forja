# -*- coding: utf-8 -*-
"""
Minerador de Fragmentos v6.3 - Diamond
- Extração cirúrgica de Shortcodes [vana-xxx].
- Mapeamento de Atributos (ref, title, author).
- Sincronização de Timestamps para cada fragmento.
"""

import re
import uuid

def parse_shortcodes(text: str, versao_id: str):
    """
    Varre o texto final em busca de blocos teológicos e prepara para o Supabase.
    """
    # Regex para capturar: [vana-TIPO atributo="valor"]CONTEUDO[/vana-TIPO]
    # O flag re.DOTALL (s) permite que o '.' capture quebras de linha.
    pattern = r"\[vana-(?P<tipo>\w+)(?P<attrs>[^\]]*)\](?P<conteudo>.*?)\[/vana-(?P=tipo)\]"
    
    fragments = []
    matches = re.finditer(pattern, text, re.DOTALL)
    
    for match in matches:
        tipo = match.group('tipo')
        attrs_raw = match.group('attrs')
        conteudo = match.group('conteudo').strip()
        
        # 1. Extração de Atributos (ex: ref="BG 4.9")
        metadata = {}
        attr_matches = re.findall(r'(\w+)="([^"]*)"', attrs_raw)
        for key, val in attr_matches:
            metadata[key] = val
            
        # 2. Identificação do Título do Segmento
        # Prioriza 'title', depois 'ref', depois 'name', senão usa o tipo.
        titulo = metadata.get('title') or metadata.get('ref') or metadata.get('name') or tipo.capitalize()
        
        # 3. Captura do Timestamp de Início (o primeiro ⟦HH:MM:SS⟧ dentro do bloco)
        ts_match = re.search(r"⟦(\d{1,2}:\d{2}:\d{2})⟧", conteudo)
        timestamp = ts_match.group(1) if ts_match else None
        
        # 4. Formatação para a tabela 'segmentos_teologicos'
        fragments.append({
            "versao_id": versao_id,
            "tipo": tipo,
            "titulo_segmento": titulo,
            "conteudo": conteudo,
            "timestamp_inicio": timestamp,
            "metadata": metadata
        })
        
    return fragments

def clean_shortcodes_for_wp(text: str):
    """
    Remove ou limpa as tags para o WordPress (opcional). 
    Se o seu plugin WP já processa shortcodes, esta função não é necessária.
    """
    # Exemplo: Remove apenas as tags [vana-xxx] e [/vana-xxx] mantendo o conteúdo.
    clean_text = re.sub(r"\[/?vana-\w+[^\]]*\]", "", text)
    return clean_text