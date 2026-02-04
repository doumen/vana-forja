# -*- coding: utf-8 -*-
"""
Parser Vaishnava v6.3 Diamond – O Minerador de Dados
- Extração de Atributos: type, reel, hook.
- Identificação de Timestamps: Vincula o tempo ao bloco.
- Prontidão para Supabase: Formata os dados para a Fábrica de Reels.
"""

import re
from typing import List, Dict, Optional

class VanaParser:
    def __init__(self):
        # Regex Diamond: Captura a abertura [hk_passage ...], o conteúdo interno e o fechamento
        self.passage_regex = re.compile(r'\[hk_passage\s+([^\]]+)\](.*?)\[/hk_passage\]', re.DOTALL)
        
        # Regex para extrair atributos no formato chave="valor"
        self.attr_regex = re.compile(r'(\w+)="([^"]*)"')
        
        # Regex para encontrar o timestamp protegido ⟦HH:MM:SS⟧
        self.timestamp_regex = re.compile(r'⟦(\d{1,2}:\d{2}:\d{2})⟧')

    def parse_aula(self, text: str, post_id: int) -> List[Dict]:
        """
        Minera o texto do post em busca de passagens estruturadas.
        Retorna uma lista de dicionários prontos para o Supabase.
        """
        print(f"🔍 [VanaParser] Minerando pérolas no post {post_id}...")
        
        extracted_data = []
        matches = self.passage_regex.finditer(text)

        for match in matches:
            attr_raw = match.group(1)
            content = match.group(2).strip()
            
            # 1. Extração de Atributos
            attrs = dict(self.attr_regex.findall(attr_raw))
            
            # 2. Detecção de Contexto (Timestamps)
            # Buscamos o timestamp mais próximo ANTES do início deste bloco
            timestamp = self._find_nearest_timestamp(text, match.start())

            # 3. Construção do Objeto Diamond
            passage_obj = {
                "wp_post_id": post_id,
                "type": attrs.get("type", "tattva"), # lila, biografia, etc.
                "is_reel": attrs.get("reel", "false").lower() == "true",
                "hook": attrs.get("hook", ""),
                "content_raw": content,
                "timestamp_start": timestamp,
                "clean_content": self._remove_internal_shortcodes(content)
            }
            
            extracted_data.append(passage_obj)

        print(f"✅ [VanaParser] {len(extracted_data)} passagens mineradas com sucesso.")
        return extracted_data

    def _find_nearest_timestamp(self, text: str, position: int) -> str:
        """
        Busca reversa pelo timestamp ⟦HH:MM:SS⟧ mais próximo da posição atual.
        """
        # Pega todo o texto até o início do bloco
        lookback_text = text[:position]
        timestamps = self.timestamp_regex.findall(lookback_text)
        
        if timestamps:
            return timestamps[-1] # Retorna o último encontrado antes do bloco
        return "00:00:00"

    def _remove_internal_shortcodes(self, text: str) -> str:
        """
        Limpa shortcodes internos como [original] e [explicacao] 
        para que o Reel/Legenda tenha apenas o texto limpo.
        """
        clean = re.sub(r'\[/?original\]', '', text)
        clean = re.sub(r'\[/?explicacao\]', '', clean)
        return clean.strip()

    def get_summary(self, passages: List[Dict]) -> str:
        """Gera um resumo rápido para log/auditoria."""
        reels = [p for p in passages if p['is_reel']]
        bios = [p for p in passages if p['type'] == 'biografia']
        return f"Total: {len(passages)} | Reels: {len(reels)} | Biografias: {len(bios)}"