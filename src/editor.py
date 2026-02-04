# -*- coding: utf-8 -*-
"""
Editor Vaishnava v6.3 Diamond – O Escriba de Shortcodes
- Geração de Shortcodes [vana-xxx] para Estudo Cruzado.
- Cláusula de Autoridade (Vāṇī-Śuddha) e IAST Estrito.
- Sistema de Flags 🚩 para Revisão Humana.
- Blindagem de Timestamps ⟦HH:MM:SS⟧.
"""

import os
import re
from pathlib import Path
from src.smart_ai_wrapper import SmartAIWrapper # Wrapper para Anthropic/Claude
from src.utils.io import write_json

# Configurações de Caminho
RAW_PATH = Path("work/transcripts/raw_transcript.txt")
EDIT_DIR = Path("work/edited")

def get_system_prompt(target_lang: str) -> str:
    """Define a personalidade e as regras de ouro do editor."""
    lang_map = {"pt": "Português", "en": "English", "es": "Español"}
    idioma = lang_map.get(target_lang, "Português")

    return f"""Você é um editor sênior especializado em filosofia Vaishnava e na preservação da Hari-kathā.
Sua tarefa é refinar a transcrição bruta para {idioma}, mantendo a pureza e autoridade da fala de Gurudeva.

### 🛡️ CLÁUSULA DE AUTORIDADE (VĀṆĪ-ŚUDDHA)
1. A fala original de Gurudeva é a autoridade suprema. Corrija erros do tradutor da live baseando-se no original.
2. Use IAST (transliteração sânscrita) perfeito: Kṛṣṇa, Bhakti, Śrīmad-Bhāgavatam, Caitanya.

### 💎 ESTRUTURA DE MINERAÇÃO (SHORTCODES)
Você deve identificar e envolver as "pérolas" nos seguintes shortcodes:
- [vana-verso ref="REF"] : Envolva versos citados. Dentro dele, use [original] para o sânscrito e [explicacao] para o comentário.
- [vana-lila title="TITULO"] : Para passatempos de Kṛṣṇa e Seus associados.
- [vana-instrucao] : Para ordens de Sādhana ou conclusões filosóficas fundamentais.
- [vana-historia title="TITULO"] : Para analogias, parábolas e histórias morais.
- [vana-bio name="NOME"] : Para relatos biográficos de Ācāryas.
- [vana-cancao author="AUTOR"] : Para trechos de Bhajans comentados.
- [vana-tattva] : Para explicações técnicas de conceitos (ex: Guru-tattva).

### 🚩 HUMILDADE E REVISÃO
- Se houver dúvida teológica ou áudio inaudível, NÃO invente. Use a flag: 🚩 [DÚVIDA: motivo].
- Mantenha os timestamps ⟦HH:MM:SS⟧ no início dos parágrafos onde eles ocorrem.

Retorne apenas o texto final estruturado."""

def _apply_timestamp_guard(text: str) -> str:
    """Protege os timestamps convertendo [HH:MM:SS] em ⟦HH:MM:SS⟧."""
    pattern = r"\[(\d{1,2}:\d{2}:\d{2})\]"
    return re.sub(pattern, r"⟦\1⟧", text)

def run_editor(target_lang: str = "pt") -> dict:
    """Executa o processo de refino editorial e auditoria."""
    EDIT_DIR.mkdir(parents=True, exist_ok=True)
    
    if not RAW_PATH.exists():
        raise FileNotFoundError("Arquivo raw_transcript.txt não encontrado.")

    raw_text = RAW_PATH.read_text(encoding="utf-8")
    
    # 1. Preparação: Blindagem de Timestamps
    guarded_text = _apply_timestamp_guard(raw_text)
    ts_original_count = len(re.findall(r"⟦\d{1,2}:\d{2}:\d{2}⟧", guarded_text))

    # 2. Chamada à Inteligência Artificial (Claude 3.5 Sonnet)
    ai = SmartAIWrapper()
    sys_prompt = get_system_prompt(target_lang)
    
    print(f"   ✨ Refinando e Minerando pérolas em [{target_lang}]...")
    response = ai.edit_text(sys_prompt, guarded_text)
    
    final_text = response.text
    
    # 3. Auditoria de Integridade
    flags = final_text.count("🚩")
    ts_final_count = len(re.findall(r"⟦\d{1,2}:\d{2}:\d{2}⟧", final_text))
    
    status = "verificado"
    if flags > 0 or ts_final_count != ts_original_count:
        status = "revisao_pendente"

    # 4. Salvamento
    output_path = EDIT_DIR / "edited_text.txt"
    output_path.write_text(final_text, encoding="utf-8")
    
    stats = {
        "status": status,
        "flags_count": flags,
        "ts_integrity": ts_final_count == ts_original_count,
        "cost_usd": response.cost_usd,
        "model": response.model,
        "text": final_text
    }
    
    write_json(EDIT_DIR / "editor_stats.json", stats)
    return stats