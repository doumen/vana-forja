# -*- coding: utf-8 -*-
"""
Supabase Client v6.3 Diamond
- Persistência de Dados: Aulas, Passagens e Conceitos.
- Vocabulário Dinâmico: Recuperação de termos IAST para a IA.
- Gestão de UUIDs: Integração segura com o schema PostgreSQL.
"""

import os
from typing import List, Dict, Optional, Any
from supabase import create_client, Client

class VanaSupabase:
    def __init__(self):
        # Configurações de ambiente (Secrets do GitHub ou .env)
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY") # Service Role Key recomendada
        
        if not self.url or not self.key:
            raise EnvironmentError("❌ Credenciais do Supabase não configuradas!")

        self.client: Client = create_client(self.url, self.key)

    # --- GESTÃO DE VOCABULÁRIO ---
    def get_all_concepts(self) -> Dict[str, str]:
        """
        Busca todos os conceitos e retorna um dicionário {slug: tag_iast}.
        Usado pelo Editor.py para garantir precisão teológica.
        """
        try:
            response = self.client.table("vana_conceitos").select("slug, tag_iast").execute()
            # Transforma em dicionário para busca rápida O(1)
            return {item['slug']: item['tag_iast'] for item in response.data}
        except Exception as e:
            print(f"⚠️ Erro ao buscar vocabulário no Supabase: {e}")
            return {}

    # --- GESTÃO DE AULAS ---
    def upsert_aula(self, aula_data: Dict[str, Any]) -> Optional[str]:
        """
        Cria ou atualiza o registro mestre de uma aula.
        Retorna o UUID da aula no Supabase.
        """
        print(f"💾 Salvando registro da aula no Supabase...")
        try:
            # O on_conflict="wp_post_id" garante que não dupliquemos posts
            response = self.client.table("vana_aulas").upsert(
                aula_data, 
                on_conflict="wp_post_id"
            ).execute()
            
            if response.data:
                return response.data[0]['id']
            return None
        except Exception as e:
            print(f"❌ Erro ao salvar aula no Supabase: {e}")
            return None

    # --- GESTÃO DE PASSAGENS (REELS) ---
    def save_passagens(self, aula_uuid: str, passagens: List[Dict[str, Any]]):
        """
        Salva todos os fragmentos (Lilas, Tattvas, etc.) extraídos pelo Parser.
        """
        if not passagens:
            return

        print(f"💎 Minerando e salvando {len(passagens)} passagens no Supabase...")
        
        # Prepara os dados vinculando ao UUID da aula
        for p in passagens:
            p['aula_id'] = aula_uuid
            # Remove campos que são apenas para o WP se necessário
            if 'wp_post_id' in p: del p['wp_post_id']

        try:
            self.client.table("vana_passagens").insert(passagens).execute()
            print("✅ Passagens salvas com sucesso.")
        except Exception as e:
            print(f"❌ Erro ao salvar passagens: {e}")

    # --- BUSCAS ESPECÍFICAS ---
    def get_reels_queue(self) -> List[Dict]:
        """Busca todas as passagens marcadas como reel=true que ainda não foram postadas."""
        response = self.client.table("vana_passagens")\
            .select("*, vana_aulas(title, archive_url)")\
            .eq("is_reel", True)\
            .execute()
        return response.data