# -*- coding: utf-8 -*-
"""
Sincronizador de Vocabulário v6.3 Diamond
- Planilha Google (CSV) -> Supabase
- Garante a integridade dos termos IAST para o Editor.
- Suporte a slugs únicos para evitar duplicidade.
"""

import os
import pandas as pd
from supabase import create_client, Client
from typing import Optional

class VanaVocabularySync:
    def __init__(self):
        # Configurações via Variáveis de Ambiente (Desacoplado)
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.sheet_csv_url = os.getenv("GOOGLE_SHEET_VOCABULARY_URL")
        
        if not all([self.supabase_url, self.supabase_key, self.sheet_csv_url]):
            raise EnvironmentError("❌ Variáveis de ambiente do Supabase ou Google Sheet não configuradas!")

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

    def run_sync(self):
        """Executa a sincronização completa."""
        print("🔄 [Sync] Iniciando sincronização da Planilha Mestra...")
        
        try:
            # 1. Carrega os dados da Planilha (Publicada como CSV)
            df = pd.read_csv(self.sheet_csv_url)
            
            # Limpeza básica de dados
            df.columns = [c.strip().lower() for c in df.columns]
            print(f"📊 [Sync] {len(df)} termos encontrados na planilha.")

            # 2. Processamento e Upload
            success_count = 0
            for _, row in df.iterrows():
                # Prepara o objeto para o Supabase
                # Certifique-se que os nomes das colunas na planilha batem com estes:
                # slug, tag_iast, categoria, descricao
                payload = {
                    "slug": str(row['slug']).strip().lower(),
                    "tag_iast": str(row['tag_iast']).strip(),
                    "category": str(row.get('categoria', 'geral')).strip().lower(),
                    "description": str(row.get('descricao', '')).strip()
                }

                # 3. UPSERT no Supabase (Insere se novo, atualiza se o slug já existir)
                try:
                    self.supabase.table("vana_conceitos").upsert(
                        payload, 
                        on_conflict="slug"
                    ).execute()
                    success_count += 1
                except Exception as e:
                    print(f"⚠️ Erro ao sincronizar termo '{payload['slug']}': {e}")

            print(f"✅ [Sync] Sincronização concluída! {success_count} termos processados.")

        except Exception as e:
            print(f"❌ Erro fatal na sincronização: {e}")

if __name__ == "__main__":
    sync = VanaVocabularySync()
    sync.run_sync()