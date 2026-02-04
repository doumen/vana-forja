# -*- coding: utf-8 -*-
"""
Notifier v5.9.1 – O Vigia do Templo
- Integração com Telegram Bot API
- Notificações formatadas em HTML
- Resumo de Performance (Custo, Tempo, Fonte)
- Alertas de Falha com contexto para Debug
"""
import os
import requests
from typing import Any

def _send(message: str, parse_mode: str = "HTML") -> bool:
    """
    Função base para envio via Telegram.
    Utiliza as Secrets configuradas no GitHub Actions.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        # Se as chaves não estiverem configuradas, o sistema continua sem notificar
        return False
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        resp = requests.post(url, json=payload, timeout=15)
        return resp.status_code == 200
    except Exception:
        # Falhas na notificação não devem interromper o pipeline principal
        return False

def notify_success(stats: dict):
    """
    Formata e envia uma mensagem de sucesso com os KPIs da Forja.
    """
    source = stats.get('source_url', 'Desconhecida')
    # Trunca a URL para não poluir o chat
    short_url = (source[:45] + '...') if len(source) > 45 else source
    
    msg = (
        f"✅ <b>Forja Concluída com Sucesso!</b>\n\n"
        f"🎙️ <b>Fonte:</b> <code>{short_url}</code>\n"
        f"📝 <b>Post ID:</b> <code>{stats.get('post_id', 'N/A')}</code>\n"
        f"⏱️ <b>Tempo Total:</b> <code>{stats.get('duration_seconds', 0):.0f}s</code>\n"
        f"💰 <b>Custo Estimado:</b> <code>${stats.get('total_cost', 0):.4f}</code>\n\n"
        f"✨ <i>A aula foi salva como rascunho e está pronta para revisão.</i>"
    )
    _send(msg)

def notify_failure(error: str, context: dict):
    """
    Envia um alerta de falha detalhado para diagnóstico rápido.
    """
    source = context.get('source_url', 'Desconhecida')
    short_url = (source[:45] + '...') if len(source) > 45 else source
    
    # Sanitização básica para evitar que caracteres do erro quebrem o HTML do Telegram
    safe_error = str(error).replace("<", "&lt;").replace(">", "&gt;")
    
    msg = (
        f"❌ <b>Alerta: Falha na Forja</b>\n\n"
        f"🔗 <b>Fonte:</b> <code>{short_url}</code>\n"
        f"📝 <b>Post ID:</b> {context.get('post_id', 'N/A')}\n"
        f"💥 <b>Erro:</b> <code>{safe_error[:300]}</code>\n\n"
        f"⚠️ <i>Verifique os logs no GitHub Actions para mais detalhes.</i>"
    )
    _send(msg)