# -*- coding: utf-8 -*-
"""
Editor Vaishnava v5.9.1 – O Escriba IAST
- Blindagem Alquímica de timestamps (Unicode ⟦ ⟧)
- Refino semântico e estruturação literária via Claude/Gemini
- Chunking inteligente para evitar estouro de contexto
- Preservação absoluta da Vāṇī original
"""
import re
import json
from pathlib import Path
from src.smart_ai_wrapper import SmartAIWrapper
from src.utils.io import write_json

# Configurações de Caminhos
RAW_PATH = Path("work/transcripts/raw_transcript.txt")
EDIT_DIR = Path("work/edited")

# Regex para timestamps (captura [H:MM:SS] ou [HH:MM:SS])
TS_REGEX = re.compile(r"\[(\d{1,2}:\d{2}:\d{2})\]")

# Caracteres de blindagem (Unicode Sagrado)
# Usados para que a IA identifique como objetos imutáveis
GUARD_L = "⟦"
GUARD_R = "⟧"

# Prompt Editorial Mestre
PROMPT = """Você é um editor sênior da BBT (Bhaktivedanta Book Trust), especialista em Hari-kathā.
Sua missão é refinar a transcrição bruta de uma palestra devocional.

### REGRAS DE OURO:
1. **TIMESTAMPS SAGRADOS**: Os marcadores ⟦H:MM:SS⟧ NÃO podem ser alterados, removidos ou reordenados.
2. **IAST OBRIGATÓRIO**: Use transliteração sânscrita perfeita (ex: Krishna -> Kṛṣṇa, Shastra -> Śāstra).
3. **ESTRUTURA**: Divida o texto em parágrafos coerentes. Coloque o timestamp no início de cada parágrafo relevante.
4. **PÉROLAS**: Identifique citações de escrituras e marque-as como [[REF: nome_da_escritura]].
5. **ESTILO**: Mantenha o "sabor" da fala de Gurudeva, mas remova vícios de linguagem excessivos.

### FORMATO DE SAÍDA:
Apenas o texto editado, preservando os timestamps blindados ⟦H:MM:SS⟧."""

# Limite de caracteres por chunk para manter a atenção da IA e o contexto
MAX_CHUNK_CHARS = 12000 

def _protect_timestamps(text: str) -> str:
    """Converte [H:MM:SS] em ⟦H:MM:SS⟧ para blindagem contra a IA."""
    return TS_REGEX.sub(lambda m: f"{GUARD_L}{m.group(1)}{GUARD_R}", text)

def _chunk_text(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Divide o texto em blocos menores respeitando as quebras de parágrafo."""
    paragraphs = text.split("\n")
    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        para_len = len(para) + 1
        if current_length + para_len > max_chars and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = [para]
            current_length = para_len
        else:
            current_chunk.append(para)
            current_length += para_len

    if current_chunk:
        chunks.append("\n".join(current_chunk))
    return chunks

def run_editor() -> dict:
    """Executa o processo completo de refino editorial."""
    EDIT_DIR.mkdir(parents=True, exist_ok=True)

    if not RAW_PATH.exists():
        return {"ok": False, "reason": "Transcrição bruta não localizada."}

    raw_text = RAW_PATH.read_text(encoding="utf-8")
    original_ts_count = len(TS_REGEX.findall(raw_text))

    # 1. Aplicar Blindagem
    guarded_text = _protect_timestamps(raw_text)

    # 2. Chunking
    chunks = _chunk_text(guarded_text)
    
    ai = SmartAIWrapper()
    edited_parts = []
    total_cost = 0.0
    provider_info = ""

    print(f"   ✨ Iniciando refino de {len(chunks)} blocos de texto...")

    for i, chunk in enumerate(chunks):
        # 3. Chamada à IA (com sistema de cache e fallback)
        res = ai.edit_text(PROMPT, chunk)
        edited_parts.append(res.text)
        total_cost += res.cost_usd
        provider_info = f"{res.provider} ({res.model})"
        
        print(f"      part_{i:02d} processada ({'Cache' if res.cached else 'Live API'})")

    # 4. Consolidação
    final_text = "\n\n".join(edited_parts)
    
    # Validação de preservação (contagem de timestamps blindados)
    final_ts_count = len(re.findall(rf"{GUARD_L}\d{{1,2}}:\d{{2}}:\d{{2}}{GUARD_R}", final_text))

    # 5. Persistência
    output_file = EDIT_DIR / "edited.txt"
    output_file.write_text(final_text, encoding="utf-8")

    stats = {
        "ok": True,
        "provider": provider_info,
        "cost_usd": round(total_cost, 4),
        "chunks": len(chunks),
        "ts_original": original_ts_count,
        "ts_preserved": final_ts_count,
        "integrity": "OK" if original_ts_count == final_ts_count else "WARNING"
    }
    
    write_json(EDIT_DIR / "editor_stats.json", stats)
    return stats