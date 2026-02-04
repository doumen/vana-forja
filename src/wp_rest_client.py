# -*- coding: utf-8 -*-
"""
WP REST Client v5.9.1 – O Mensageiro Resiliente
- Desenvolvido especificamente para ambientes Hostinger (Hospedagem Compartilhada)
- Estratégia de PATCH Incremental (Evita erros 413 e 504)
- Throttling (TPS) para evitar bloqueios por Rate Limit (Erro 429)
- Retry com Backoff Exponencial e Jitter para máxima estabilidade
"""
import os
import time
import math
import requests
from pathlib import Path
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type
)
from src.utils.io import write_json

# Caminho para relatório de auditoria de publicação
REPORT_PATH = Path("work/audit/wp_publish_report.json")

class WPPublishError(Exception):
    """Exceção customizada para erros na API do WordPress."""
    pass

class WPClient:
    def __init__(self):
        self.base_url = os.getenv("WP_BASE_URL", "").rstrip("/")
        self.user = os.getenv("WP_USER")
        self.app_pass = os.getenv("WP_APP_PASS")
        self.cpt = os.getenv("WP_CPT", "vana_aula")  # Custom Post Type padrão
        
        # Parâmetros de Resiliência para Hostinger
        self.chunk_size = int(os.getenv("WP_CHUNK_SIZE", "25000")) # ~25KB por envio
        self.tps = float(os.getenv("WP_TPS", "1.0")) # 1 requisição por segundo

        if not all([self.base_url, self.user, self.app_pass]):
            raise ValueError("Configurações REST do WP incompletas (URL, USER ou APP_PASS).")

    def _throttle(self):
        """Implementa uma pausa controlada entre requisições para acalmar o WAF da Hostinger."""
        time.sleep(max(0.1, 1.0 / self.tps))

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential_jitter(initial=2, max=30),
        retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError, WPPublishError))
    )
    def _request(self, method: str, post_id: int, payload: dict) -> dict:
        """Executa a chamada HTTP com autenticação e retentativas automáticas."""
        url = f"{self.base_url}/wp-json/wp/v2/{self.cpt}/{post_id}"
        
        try:
            resp = requests.request(
                method,
                url,
                auth=(self.user, self.app_pass),
                json=payload,
                timeout=60,
                headers={"Content-Type": "application/json"}
            )
        except Exception as e:
            raise WPPublishError(f"Erro de conexão: {str(e)}")

        # Tratamento de Erros Específicos de Hospedagem
        if resp.status_code == 413:
            raise WPPublishError("Erro 413: Payload muito grande. Reduza o WP_CHUNK_SIZE.")
        if resp.status_code == 429:
            raise WPPublishError("Erro 429: Rate Limit atingido. Reduza o WP_TPS.")
        if resp.status_code >= 400:
            raise WPPublishError(f"Erro WP {resp.status_code}: {resp.text[:200]}")

        return resp.json()

    def publish(self, post_id: int, content: str, publish_now: bool = False) -> dict:
        """
        Publica o conteúdo de forma incremental.
        Envia blocos acumulados para garantir que o servidor processe em partes.
        """
        total_chars = len(content)
        num_parts = math.ceil(total_chars / self.chunk_size)
        accumulated_text = ""

        print(f"   📡 Iniciando envio incremental para Post #{post_id} ({num_parts} partes)...")

        for i in range(num_parts):
            start = i * self.chunk_size
            end = (i + 1) * self.chunk_size
            chunk = content[start:end]
            accumulated_text += chunk

            # Envia como 'draft' durante o processo incremental
            self._throttle()
            self._request("POST", post_id, {"content": accumulated_text, "status": "draft"})
            print(f"      📦 Parte {i+1}/{num_parts} enviada com sucesso.")

        # Passo Final: Define o status final (Publicado ou permanece Draft)
        status_final = "publish" if publish_now else "draft"
        self._throttle()
        self._request("POST", post_id, {"status": status_final})

        return {
            "ok": True,
            "post_id": post_id,
            "total_chars": total_chars,
            "parts_sent": num_parts,
            "final_status": status_final
        }

def publish_wp(post_id: int, path_txt: str, publish: bool = False) -> dict:
    """Função de entrada para o orquestrador."""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        content = Path(path_txt).read_text(encoding="utf-8")
        client = WPClient()
        result = client.publish(post_id, content, publish_now=publish)
        write_json(REPORT_PATH, result)
        return result
    except Exception as e:
        error_result = {"ok": False, "error": str(e), "post_id": post_id}
        write_json(REPORT_PATH, error_result)
        raise