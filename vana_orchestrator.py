# -*- coding: utf-8 -*-
"""
Vana Orchestrator v5.9.1 – O Maestro da Forja
- Gerencia o fluxo completo: Ingestão -> STT -> Auditoria -> Edição -> Reparo -> Merge -> WP
- Implementa Idempotência e Tratamento de Exceções Silenciosas
- Consolida métricas de custo e performance no stats.json
- Gatilho final de notificações (Telegram)
"""
import argparse
import sys
import time
import os
import traceback
from pathlib import Path

# Importação dos Módulos da Forja
from src.transcriber import run_transcription
from src.auditor_raw import audit_or_fix
from src.editor import run_editor
from src.auditor_reparador import run_repair
from src.merger import run_merger
from src.wp_rest_client import publish_wp
from src.notifier import notify_success, notify_failure
from src.smart_ai_wrapper import SmartAIWrapper
from src.utils.io import write_json

def main():
    # 1. Configuração de Argumentos (Entradas do GHA)
    parser = argparse.ArgumentParser(description="Forja HariKatha – Pipeline Digital")
    parser.add_argument("--source_url", required=True, help="URL da Live ou Vídeo")
    parser.add_argument("--post_id", type=int, required=True, help="ID do post no WordPress")
    parser.add_argument("--lang", default="pt", help="Idioma da transcrição")
    parser.add_argument("--publish", action="store_true", help="Publicar imediatamente?")
    args = parser.parse_args()

    start_time = time.time()
    stats = {
        "source_url": args.source_url,
        "post_id": args.post_id,
        "lang": args.lang,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "success": False
    }

    try:
        print(f"🚀 Iniciando Forja para o Post #{args.post_id}")

        # --- PASSO 1: TRANSCRIÇÃO (Whisper v3) ---
        print("\n--- PASSO 1: Transcrição ---")
        t_stats = run_transcription(args.source_url, lang_hint=args.lang)
        stats["transcription"] = t_stats

        # --- PASSO 2: AUDITORIA BRUTA ---
        print("\n--- PASSO 2: Auditoria de Qualidade ---")
        a_stats = audit_or_fix()
        stats["audit_raw"] = a_stats
        if not a_stats.get("ok"):
            reasons = "; ".join(a_stats.get("reasons", ["Falha desconhecida"]))
            raise RuntimeError(f"Qualidade insuficiente da transcrição: {reasons}")

        # --- PASSO 3: EDIÇÃO LITERÁRIA (IAST) ---
        print("\n--- PASSO 3: Refino Editorial e IAST ---")
        e_stats = run_editor()
        stats["editor"] = e_stats

        # --- PASSO 4: REPARO DE BLINDAGEM ---
        print("\n--- PASSO 4: Restauração de Timestamps ---")
        r_stats = run_repair()
        stats["repair"] = r_stats

        # --- PASSO 5: MERGE DE GLOSSÁRIO ---
        print("\n--- PASSO 5: Injeção de Referências Śāstricas ---")
        m_stats = run_merger()
        stats["merger"] = m_stats

        # --- PASSO 6: PUBLICAÇÃO INCREMENTAL ---
        print("\n--- PASSO 6: Entrega ao WordPress ---")
        final_file = m_stats.get("output_file")
        p_stats = publish_wp(args.post_id, final_file, publish=args.publish)
        stats["publish"] = p_stats

        # --- FINALIZAÇÃO ---
        end_time = time.time()
        stats["duration_seconds"] = round(end_time - start_time, 2)
        stats["total_cost"] = e_stats.get("cost_usd", 0)
        stats["success"] = True

        # Resumo de Custo para o Telegram
        ai_info = SmartAIWrapper().get_cost_summary()
        stats["cost_summary"] = ai_info

        print(f"\n✅ Forja Concluída em {stats['duration_seconds']}s")
        notify_success(stats)

    except Exception as e:
        # Sanitização: remove senhas de app do log de erro
        error_msg = str(e).replace(os.getenv("WP_APP_PASS", "SECRET"), "***")
        print(f"\n❌ ERRO NO PIPELINE: {error_msg}")
        
        stats["success"] = False
        stats["error"] = error_msg
        stats["traceback"] = traceback.format_exc(limit=3)
        
        notify_failure(error_msg, stats)
        # Retorna código de erro para o GitHub Actions entender que falhou
        sys.exit(1)

    finally:
        # Salva o relatório final independente do resultado
        write_json("work/stats.json", stats)

if __name__ == "__main__":
    main()