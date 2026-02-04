# -*- coding: utf-8 -*-
"""
Supabase Client v6.3 Diamond – O Guardião do Acervo
- Gestão de Idempotência Universal (YT, FB, MP3)
- Módulo FinOps para controle de gastos
- Suporte à Mineração de Segmentos (Estudo Cruzado)
"""
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from supabase import create_client, Client

class VanaSupabase:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.url or not self.key:
            self.client = None
            print("⚠️ ERRO CRÍTICO: Credenciais Supabase ausentes.")
        else:
            self.client: Client = create_client(self.url, self.key)

    # --- 💰 MÓDULO FINOPS (CONTROLE DE ORÇAMENTO) ---

    def get_monthly_spend(self) -> float:
        """Calcula o total gasto no mês atual para trava de segurança."""
        if not self.client: return 0.0
        try:
            inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0).isoformat()
            res = self.client.table("versoes_finais").select("custo_usd").gte("criado_em", inicio_mes).execute()
            return sum(float(item['custo_usd'] or 0) for item in res.data)
        except Exception:
            return 999.0 # Bloqueia por segurança

    # --- 🧬 MÓDULO DE IDENTIDADE (FONTES E DNA) ---

    def get_source_id(self, url: str) -> str:
        """Identifica a fonte independente da plataforma (YT/FB)."""
        res = self.client.table("fontes").select("id").eq("url_original", url).execute()
        if res.data: return res.data[0]['id']
        
        plataforma = "youtube" if "youtu" in url else "facebook"
        new = self.client.table("fontes").insert({"url_original": url, "plataforma": plataforma}).execute()
        return new.data[0]['id']

    def upsert_aula(self, source_id: str) -> Dict[str, Any]:
        """Gerencia o registro mestre da aula."""
        res = self.client.table("aulas").select("*").eq("fonte_id", source_id).execute()
        if res.data: return res.data[0]
        
        new = self.client.table("aulas").insert({"fonte_id": source_id}).execute()
        return new.data[0]

    def buscar_raw_existente(self, aula_id: str) -> Optional[str]:
        """Busca DNA existente para evitar custo duplicado de Whisper."""
        res = self.client.table("aulas").select("raw_transcript").eq("id", aula_id).execute()
        return res.data[0]["raw_transcript"] if res.data and res.data[0]["raw_transcript"] else None

    # --- ✨ MÓDULO DE REFINO E MINERAÇÃO (ESTUDO CRUZADO) ---

    def salvar_versao_final(self, aula_id: str, idioma: str, texto: str, custo: float, status: str) -> str:
        """Salva o texto lapidado com shortcodes e status de revisão."""
        data = {
            "aula_id": aula_id,
            "idioma": idioma,
            "texto_editado": texto,
            "custo_usd": custo,
            "status": status
        }
        res = self.client.table("versoes_finais").upsert(data, on_conflict="aula_id,idioma").execute()
        return res.data[0]['id']

    def salvar_segmentos(self, fragmentos: List[Dict[str, Any]]):
        """Injeta as pérolas (Lilas, Versos, etc) no banco para estudo cruzado."""
        if not self.client or not fragmentos: return
        try:
            self.client.table("segmentos_teologicos").insert(fragmentos).execute()
            print(f"   💎 {len(fragmentos)} fragmentos indexados para estudo cruzado.")
        except Exception as e:
            print(f"⚠️ Erro na mineração de segmentos: {e}")

    def atualizar_post_id(self, aula_id: str, idioma: str, wp_id: int):
        self.client.table("versoes_finais").update({"post_id_wp": wp_id})\
            .eq("aula_id", aula_id).eq("idioma", idioma).execute()