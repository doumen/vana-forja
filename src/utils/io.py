# -*- coding: utf-8 -*-
"""
Utilitários de I/O v2.0
Funções para manipulação de arquivos, hashes SHA-256 e persistência JSON.
"""
import hashlib
import json
from pathlib import Path
from typing import Any

def sha256_file(p: Path) -> str:
    """Gera o hash SHA-256 de um arquivo (útil para áudios grandes)."""
    h = hashlib.sha256()
    if not p.exists():
        return ""
    with open(p, "rb") as f:
        # Lê em pedaços de 1MB para não estourar a RAM
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_text(s: str) -> str:
    """Gera o hash SHA-256 de uma string de texto (útil para prompts)."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def read(path: str | Path, default: str = "") -> str:
    """Lê o conteúdo de um arquivo de texto com segurança."""
    p = Path(path)
    return p.read_text(encoding="utf-8") if p.exists() else default

def write(path: str | Path, text: str):
    """Escreve texto em um arquivo, criando os diretórios pais se necessário."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

def write_json(path: str | Path, data: Any):
    """Salva um objeto Python como JSON formatado."""
    write(path, json.dumps(data, ensure_ascii=False, indent=2))

def read_json(path: str | Path, default: Any = None) -> Any:
    """Lê um arquivo JSON e retorna o objeto correspondente."""
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        # Retorna o valor padrão em caso de erro no parse do JSON
        return default