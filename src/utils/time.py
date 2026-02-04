# -*- coding: utf-8 -*-
"""
Utilitários de Tempo v5.9.2
- Conversão bidirecional: HH:MM:SS <-> Segundos
- Normalização de timestamps para o padrão WordPress
- Suporte para cálculos de Offset (Sincronia de Live)
"""
import re
from datetime import timedelta

# Regex flexível que captura [H:MM:SS] ou [HH:MM:SS]
TS_PATTERN = re.compile(r"(\d{1,2}):(\d{2}):(\d{2})")

def parse_timestamp(ts: str) -> int | None:
    """
    Converte uma string de tempo (HH:MM:SS ou H:MM:SS) para total de segundos.
    Retorna None se a string não for um timestamp válido.
    """
    if not ts or not isinstance(ts, str):
        return None
        
    m = TS_PATTERN.search(ts.strip())
    if not m:
        return None
    
    # Extrai horas, minutos e segundos
    h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return h * 3600 + mi * 60 + s

def format_timestamp(seconds: int) -> str:
    """
    Converte total de segundos para a string canônica [H:MM:SS].
    Garante que não existam tempos negativos.
    """
    # max(0, ...) evita erros caso o offset resulte em tempo negativo
    td = timedelta(seconds=max(0, int(seconds)))
    
    # O str(td) do Python retorna H:MM:SS ou HH:MM:SS dependendo da magnitude
    return str(td)

def normalize_timestamp(ts: str) -> str:
    """
    Recebe um timestamp possivelmente mal formatado (ex: 0:5:9)
    e o transforma no padrão canônico (ex: 0:05:09).
    """
    secs = parse_timestamp(ts)
    if secs is not None:
        return format_timestamp(secs)
    return ts

def shift_timestamp(ts: str, seconds_offset: int) -> str:
    """
    Aplica um deslocamento (offset) a um timestamp existente.
    Essencial para sincronizar o tempo de um corte cirúrgico com a live original.
    """
    current_secs = parse_timestamp(ts)
    if current_secs is not None:
        return format_timestamp(current_secs + seconds_offset)
    return ts