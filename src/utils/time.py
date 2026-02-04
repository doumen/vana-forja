# -*- coding: utf-8 -*-
"""
Utilitários de Tempo v2.0
Responsável por converter, validar e normalizar marcadores [H:MM:SS].
"""
import re
from datetime import timedelta

# Regex flexível que captura [H:MM:SS] ou [HH:MM:SS]
# Útil para extrair o tempo de strings sujas vindas da transcrição
TS_PATTERN = re.compile(r"(\d{1,2}):(\d{2}):(\d{2})")

def parse_timestamp(ts: str) -> int | None:
    """
    Converte uma string de tempo (H:MM:SS) para o total de segundos.
    Retorna None se o formato for inválido.
    """
    m = TS_PATTERN.search(ts.strip())
    if not m:
        return None
    
    # Extrai grupos: horas, minutos e segundos
    h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return h * 3600 + mi * 60 + s

def format_timestamp(seconds: int) -> str:
    """
    Converte um total de segundos para a string canônica H:MM:SS.
    Utiliza a classe timedelta do Python para garantir precisão matemática.
    """
    # max(0, ...) evita tempos negativos em casos de erro de cálculo
    return str(timedelta(seconds=max(0, int(seconds))))

def normalize_timestamp(ts: str) -> str:
    """
    Recebe uma string de tempo possivelmente mal formatada (ex: 0:5:09)
    e a transforma no padrão canônico (ex: 0:05:09).
    """
    secs = parse_timestamp(ts)
    if secs is not None:
        return format_timestamp(secs)
    return ts  # Retorna o original se não conseguir parsear

def shift_timestamp(ts: str, seconds_offset: int) -> str:
    """
    Aplica um deslocamento (offset) a um timestamp.
    Muito útil quando processamos chunks de áudio e precisamos
    ajustar o tempo relativo para o tempo absoluto da aula.
    """
    current_secs = parse_timestamp(ts)
    if current_secs is not None:
        return format_timestamp(current_secs + seconds_offset)
    return ts