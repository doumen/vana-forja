# -*- coding: utf-8 -*-
"""
PersistentCache v2.0
Cache persistente em disco (JSON) para sobreviver entre jobs do GitHub Actions.
Implementa expiração baseada em TTL (Time To Live).
"""
import json
import time
import os
from pathlib import Path
from typing import Any

# Diretório onde o cache será persistido (deve ser mapeado no actions/cache do GHA)
CACHE_DIR = Path("work/.cache")

class PersistentCache:
    def __init__(self, name: str, ttl_seconds: int = 86400):
        """
        Inicializa o cache.
        :param name: Nome do arquivo de cache (ex: 'ai_responses')
        :param ttl_seconds: Tempo de vida das entradas em segundos (padrão 24h)
        """
        self.path = CACHE_DIR / f"{name}.json"
        self.ttl = ttl_seconds
        self._data: dict = {}
        self._load()

    def _load(self):
        """Carrega os dados do disco e limpa entradas expiradas."""
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                now = time.time()
                # Filtra apenas entradas que ainda estão dentro do TTL
                self._data = {
                    k: v for k, v in raw.items() 
                    if v.get("_ts", 0) + self.ttl > now
                }
            except Exception:
                # Se o arquivo estiver corrompido, reseta o cache
                self._data = {}

    def _save(self):
        """Escreve o estado atual do cache no disco de forma atômica."""
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def set(self, key: str, value: Any):
        """Armazena um valor vinculado a uma chave com o timestamp atual."""
        self._data[key] = {
            "value": value,
            "_ts": time.time()
        }
        self._save()

    def get(self, key: str) -> Any | None:
        """
        Recupera o valor se a chave existir e não estiver expirada.
        Retorna None se não encontrar ou se expirado.
        """
        entry = self._data.get(key)
        if not entry:
            return None
            
        # Verificação dupla de expiração na leitura
        if time.time() > entry.get("_ts", 0) + self.ttl:
            del self._data[key]
            self._save()
            return None
            
        return entry.get("value")

    def has(self, key: str) -> bool:
        """Verifica se existe uma entrada válida no cache."""
        return self.get(key) is not None