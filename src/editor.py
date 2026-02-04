# -*- coding: utf-8 -*-
"""
Editor Vaishnava v5.9.2 – O Escriba IAST (Edição Darshan)
- Blindagem Alquímica de timestamps (Unicode ⟦ ⟧)
- Refino semântico com sensibilidade para Darshans informais
- Filtro inteligente: Preserva a Vāṇī e descarta ruído logístico
- Chunking inteligente para manter o contexto teológico
"""
import re
import json
from pathlib import Path
from src.smart_ai_wrapper import SmartAIWrapper
from src.utils.io import write_json

# Configurações de Caminhos
RAW_PATH = Path("work/transcripts/raw_transcript.txt")
EDIT_DIR = Path("work/edited")

# Regex para timestamps blindados
TS_REGEX = re.compile(r"\[(\d{1,2}:\d{2}:\d{2})\]")
GUARD_L, GUARD_R = "⟦", "⟧"

# Prompt Editorial Mestre (Calibrado para Darshans e Aulas Formais)
PROMPT = """Você é um editor sênior da BBT (Bhaktivedanta Book Trust), especialista em Hari-kathā.
Sua missão é refinar a transcrição bruta de uma fala devocional (Aula ou Darshan).

### SENSIBILIDADE EDITORIAL (MODO DARSHAN):
1. **Identificação da Vāṇī**: Identifique o início da instrução espiritual assim que o mestre começar a dissertar sobre temas do Bhakti ou responder perguntas. 
2. **Filtro de Ruído**: Em ambientes informais, remova diálogos logísticos ("o som está bom?", "traga uma cadeira", "querem chá?") que não agreguem valor teológico.
3. **Sem Maṅgalācaraṇa**: Se não houver preces formais, comece o texto de forma digna a partir da primeira fala de substância filosófica.

### REGRAS DE OURO:
1. **TIMESTAMPS SAGRADOS**: Os marcadores ⟦H:MM:SS⟧ NÃO podem ser alterados, removidos ou reordenados.
2. **IAST OBRIGATÓRIO**: Use transliteração sânscrita perfeita (ex: Krishna -> Kṛṣṇa, Shastra -> Śāstra, Chaitanya -> Caitanya).
3. **ESTRUTURA**: Divida o texto em parágrafos coerentes. Coloque o timestamp no início de cada parágrafo.
4. **PÉROLAS**: Identifique citações de escrituras e marque-as como [[REF: nome_da_escritura]].

Apenas retorne o texto editado, mantendo os timestamps blindados ⟦H:MM:SS⟧."""

MAX_CHUNK_CHARS = 12000 

def _protect_timestamps(text: str) -> str:
    """Aplica a Blindagem Alquímica aos timestamps."""
    return TS_REGEX.sub(lambda m: f"{GUARD_L}{m.group(1)}{GUARD_R}", text)

def _chunk_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Divide o texto respeitando quebras de parágrafo."""
    paragraphs = text.split("\n")
    chunks, current_chunk, current_length = [], [], 0

    for para in paragraphs:
        para_len = len(para) + 1
        if current_length + para_len > max_chars and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk, current_length = [para], para_len
        else:
            current_chunk.append(para)
            current_length += para_len

    if current_chunk:
        chunks.append("\n".join(current_chunk))
    return chunks

def run_editor() -> dict:
    """Executa o refino editorial com foco na integridade da Vāṇī."""
    EDIT_DIR.mkdir(parents=True, exist_ok=True)
    if not RAW_PATH.exists():
        return {"ok": False, "reason": "Transcrição bruta não encontrada."}

    raw_text = RAW_PATH.read_text(encoding="utf-8")
    original_ts_count = len(TS_REGEX.findall(raw_text))

    # 1. Blindagem e Chunking
    guarded_text = _protect_timestamps(raw_text)
    chunks = _chunk_text(guarded_text)
    
    ai = SmartAIWrapper()
    edited_parts, total_cost, provider_info = [], 0.0, ""

    print(f"   ✨ Refinando {len(chunks)} blocos (Modo Darshan Ativado)...")

    for i, chunk in enumerate(chunks):
        res = ai.edit_text(PROMPT, chunk)
        edited_parts.append(res.text)
        total_cost += res.cost_usd
        provider_info = f"{res.provider} ({res.model})"
        print(f"      part_{i:02d} concluída ({'Cache' if res.cached else 'Live API'})")

    # 2. Consolidação e Validação
    final_text = "\n\n".join(edited_parts)
    final_ts_count = len(re.findall(rf"{GUARD_L}\d{{1,2}}:\d{{2}}:\d{{2}}{GUARD_R}", final_text))

    # 3. Persistência
    output_file = EDIT_DIR / "edited.txt"
    output_file.write_text(final_text, encoding="utf-8")

    stats = {
        "ok": True,
        "provider": provider_info,
        "cost_usd": round(total_cost, 4),
        "ts_original": original_ts_count,
        "ts_preserved": final_ts_count,
        "integrity": "OK" if abs(original_ts_count - final_ts_count) < 5 else "CHECK_REQUIRED"
    }
    
    write_json(EDIT_DIR / "editor_stats.json", stats)
    return stats