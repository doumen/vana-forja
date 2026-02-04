# -*- coding: utf-8 -*-
"""
Merger v5.9.1 – O Teólogo
- Resolução de referências [[REF: ...]] via Google Sheets
- Cache persistente de 24h para performance e economia de API
- Sanitização HTML (Proteção contra XSS e quebra de layout)
- Fallback automático para cache offline
"""
import os
import re
import json
import html
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.cache import PersistentCache
from src.utils.io import write_json

# Caminhos de Arquivo
INP_PATH = Path("work/edited/edited_repaired.txt")
OUT_PATH = Path("work/final/POST_WORDPRESS_PRONTO.txt")
REPORT_PATH = Path("work/audit/merger_report.json")

# Regex para capturar [[REF: chave]]
REF_REGEX = re.compile(r"\[\[REF:\s*(.+?)\s*\]\]", re.IGNORECASE)

class GlossaryLoader:
    def __init__(self):
        # Cache de 24h para o glossário
        self._cache = PersistentCache("glossario", ttl_seconds=24 * 3600)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _fetch_from_sheets(self) -> dict:
        """Conecta ao Google Sheets e extrai o mapeamento chave -> conteúdo."""
        creds_json = os.getenv("GOOGLE_CREDS")
        if not creds_json:
            raise ValueError("Secret GOOGLE_CREDS não configurada no GitHub.")

        creds_info = json.loads(creds_json)
        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)

        gc = gspread.authorize(creds)
        sheet_id = os.getenv("GLOSSARIO_SHEET_ID")
        tab_name = os.getenv("GLOSSARIO_SHEET_TAB", "Glossario")

        sh = gc.open_by_key(sheet_id)
        ws = sh.worksheet(tab_name)
        rows = ws.get_all_records()

        # Normaliza chaves para facilitar o 'match'
        mapping = {}
        for row in rows:
            # Tenta encontrar colunas 'chave' e 'conteudo'
            key = str(row.get("chave") or row.get("key") or "").strip().lower()
            val = str(row.get("conteudo") or row.get("content") or "").strip()
            if key and val:
                mapping[key] = val

        return mapping

    def load(self) -> dict:
        """Carrega o glossário priorizando o cache persistente."""
        cached = self._cache.get("mapping")
        if cached:
            return cached

        try:
            mapping = self._fetch_from_sheets()
            self._cache.set("mapping", mapping)
            return mapping
        except Exception as e:
            # Fallback: Se a API falhar, tenta usar o cache mesmo que expirado
            stale = self._cache.get("mapping")
            if stale:
                print(f"   ⚠️ Falha na API Google Sheets. Usando cache offline.")
                return stale
            raise RuntimeError(f"Erro fatal ao carregar glossário: {e}")

def _apply_refs(text: str, mapping: dict) -> tuple[str, dict]:
    """Substitui as marcações [[REF]] pelos shortcodes [note] sanitizados."""
    stats = {"found": 0, "resolved": 0, "unresolved": []}

    def replacer(m):
        key = m.group(1).strip().lower()
        stats["found"] += 1
        
        val = mapping.get(key)
        if val:
            stats["resolved"] += 1
            # Sanitização Crítica: impede que caracteres especiais quebrem o shortcode
            sanitized_val = html.escape(val)
            return f"[note]{sanitized_val}[/note]"
        else:
            stats["unresolved"].append(key)
            # Mantém a tag original se não houver tradução no glossário
            return m.group(0)

    result = REF_REGEX.sub(replacer, text)
    return result, stats

def run_merger() -> dict:
    """Orquestra o processo de injeção teológica."""
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not INP_PATH.exists():
        return {"ok": False, "reason": "edited_repaired.txt não encontrado."}

    content = INP_PATH.read_text(encoding="utf-8")

    # 1. Carregar Glossário
    loader = GlossaryLoader()
    try:
        mapping = loader.load()
        glossary_ok = True
    except Exception:
        mapping = {}
        glossary_ok = False

    # 2. Aplicar Substituições
    final_text, ref_stats = _apply_refs(content, mapping)

    # 3. Salvar Output Final
    OUT_PATH.write_text(final_text, encoding="utf-8")

    report = {
        "ok": True,
        "glossary_status": "ONLINE" if glossary_ok else "OFFLINE/EMPTY",
        "glossary_entries": len(mapping),
        "refs": ref_stats,
        "output_file": str(OUT_PATH)
    }

    write_json(REPORT_PATH, report)
    return report