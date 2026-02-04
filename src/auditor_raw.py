# -*- coding: utf-8 -*-
"""
Auditor Raw v5.9.1 – O Filtro de Pureza
- Validação de Densidade de Palavras (WPM)
- Verificação de Cobertura de Timestamps
- Validação de Sequência Temporal (Garante que o tempo não volta atrás)
- Prevenção de desperdício de tokens em transcrições ruins
"""
import re
import json
from pathlib import Path
from src.utils.io import read_json, write_json
from src.utils.time import parse_timestamp

# Caminhos de Trabalho
RAW_PATH = Path("work/transcripts/raw_transcript.txt")
META_PATH = Path("work/transcripts/.meta/transcription_stats.json")
AUDIT_PATH = Path("work/audit/auditoria_raw.json")

# Regex aprimorada: Captura [H:MM:SS] ou [HH:MM:SS]
TS_REGEX = re.compile(r"\[(\d{1,2}:\d{2}:\d{2})\]")

def audit_or_fix(min_wpm: float = 25.0, min_ts_per_minute: float = 0.5) -> dict:
    """
    Analisa a qualidade da transcrição bruta.
    Retorna um dicionário com o status 'ok' e os motivos de falha se houver.
    """
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not RAW_PATH.exists():
        result = {"ok": False, "reason": "Arquivo de transcrição bruta não encontrado."}
        write_json(AUDIT_PATH, result)
        return result

    # 1. Carregamento dos dados
    text = RAW_PATH.read_text(encoding="utf-8")
    meta = read_json(META_PATH, {})
    
    # 2. Extração e Validação de Timestamps
    timestamps = TS_REGEX.findall(text)
    ts_seconds = [parse_timestamp(t) for t in timestamps]
    # Remove eventuais Nones de falha de parse
    ts_seconds = [t for t in ts_seconds if t is not None]

    # 3. Cálculo de Densidade de Palavras
    # Remove os timestamps para contar apenas as palavras faladas
    clean_text = TS_REGEX.sub("", text)
    word_count = len(clean_text.split())
    
    duration_min = max(1, meta.get("coverage_seconds", 1) / 60.0)
    wpm = word_count / duration_min
    ts_density = len(timestamps) / duration_min

    # 4. Checagem de Sequência Temporal (Crítico!)
    # Garante que um erro no Whisper não fez o tempo 'saltar' para trás
    is_sequential = True
    if len(ts_seconds) > 1:
        for i in range(len(ts_seconds) - 1):
            if ts_seconds[i] > ts_seconds[i + 1]:
                is_sequential = False
                break

    # 5. Verificação de Critérios de Qualidade
    ok_density = wpm >= min_wpm
    ok_timestamps = ts_density >= min_ts_per_minute
    ok_sequence = is_sequential

    result = {
        "ok": ok_density and ok_timestamps and ok_sequence,
        "metrics": {
            "wpm": round(wpm, 2),
            "ts_per_minute": round(ts_density, 2),
            "word_count": word_count,
            "duration_minutes": round(duration_min, 2)
        },
        "checks": {
            "density_pass": ok_density,
            "timestamps_pass": ok_timestamps,
            "sequence_pass": ok_sequence
        }
    }

    # Registro de motivos de reprovação
    if not result["ok"]:
        reasons = []
        if not ok_density: reasons.append(f"Densidade de fala muito baixa ({wpm:.1f} WPM)")
        if not ok_timestamps: reasons.append(f"Faltam marcadores de tempo ({ts_density:.2f}/min)")
        if not ok_sequence: reasons.append("Erro de cronologia (timestamps fora de ordem)")
        result["reasons"] = reasons

    write_json(AUDIT_PATH, result)
    return result

if __name__ == "__main__":
    # Teste rápido se executado diretamente
    print(json.dumps(audit_or_fix(), indent=2))