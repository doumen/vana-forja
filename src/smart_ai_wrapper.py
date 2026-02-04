# -*- coding: utf-8 -*-
"""
SmartAIWrapper v5.9.1 – O Guardião de Lakṣmī
- Multi-provedor com Fallback Automático (Claude/Gemini/OpenAI)
- Cache persistente para evitar reprocessamento (Deduplicação)
- Controle de orçamento Diário e Mensal com Hard-Stop
- Chunking inteligente para textos longos
"""
import hashlib
import os
import time
from dataclasses import dataclass
from datetime import date
from typing import Callable, Optional, Dict, Any, Tuple

from tenacity import retry, stop_after_attempt, wait_exponential
from src.utils.cache import PersistentCache

# Imports robustos com tratamento de ausência de libs
try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

@dataclass
class AIResult:
    text: str
    provider: str
    model: str
    cost_usd: float
    cached: bool = False

class ProviderError(Exception): pass
class BudgetExceeded(Exception): pass

# Tabela de Preços (Referência para estimativa de custo)
# Valores aproximados por 1M de tokens (Input + Output médio)
PRICING = {
    "claude-3-5-sonnet-latest": 3.0,
    "claude-3-5-haiku-latest": 0.80,
    "gemini-1.5-pro": 1.25,
    "gemini-1.5-flash": 0.15,
    "gpt-4o-mini": 0.15,
    "gpt-4o": 5.0,
}

FALLBACK_ORDER = ["claude", "gemini", "openai"]

class SmartAIWrapper:
    def __init__(self):
        self.primary = os.getenv("AI_PROVIDER", "claude").lower()
        self.budget_day = float(os.getenv("BUDGET_DAY_USD", "5.0"))
        self.budget_month = float(os.getenv("BUDGET_MONTH_USD", "100.0"))

        self.models = {
            "claude": os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest"),
            "gemini": os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
            "openai": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        }

        # Caches Persistentes (Garantem a memória da Forja entre execuções GHA)
        self._cache = PersistentCache("ai_responses", ttl_seconds=7 * 86400) # 7 dias
        self._cost_cache = PersistentCache("ai_costs", ttl_seconds=30 * 86400) # 30 dias

        self._init_clients()

    def _init_clients(self):
        """Inicializa os clientes das APIs com as chaves do segredo."""
        self._clients = {}
        if anthropic and os.getenv("ANTHROPIC_API_KEY"):
            self._clients["claude"] = anthropic.Client(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        if genai and os.getenv("GEMINI_API_KEY"):
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            self._clients["gemini"] = True # Gemini usa configuração global
            
        if OpenAI and os.getenv("OPENAI_API_KEY"):
            self._clients["openai"] = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _generate_hash(self, prompt: str, text: str) -> str:
        """Gera um identificador único para a requisição."""
        h = hashlib.sha256()
        h.update(prompt.encode("utf-8"))
        h.update(b"|")
        h.update(text.encode("utf-8"))
        return h.hexdigest()[:24]

    def _estimate_cost(self, provider: str, prompt: str, text: str) -> float:
        """Calcula o custo estimado com base no tamanho do texto (~3 chars/token)."""
        model = self.models.get(provider, "")
        price_per_1M = PRICING.get(model, 1.0)
        tokens = (len(prompt) + len(text)) / 3
        return (tokens / 1_000_000) * price_per_1M * 1.5 # Margem de segurança para output

    def _check_budget(self, estimated: float):
        """Bloqueia a execução se os limites financeiros forem atingidos."""
        day_key = f"cost_day_{date.today().isoformat()}"
        month_key = f"cost_month_{date.today().strftime('%Y-%m')}"
        
        today_cost = self._cost_cache.get(day_key) or 0.0
        month_cost = self._cost_cache.get(month_key) or 0.0

        if today_cost + estimated > self.budget_day:
            raise BudgetExceeded(f"Hard-Stop Diário atingido: ${today_cost:.2f}")
        if month_cost + estimated > self.budget_month:
            raise BudgetExceeded(f"Hard-Stop Mensal atingido: ${month_cost:.2f}")

    def _record_cost(self, amount: float):
        """Registra o gasto real no cache persistente."""
        day_key = f"cost_day_{date.today().isoformat()}"
        month_key = f"cost_month_{date.today().strftime('%Y-%m')}"
        
        self._cost_cache.set(day_key, (self._cost_cache.get(day_key) or 0.0) + amount)
        self._cost_cache.set(month_key, (self._cost_cache.get(month_key) or 0.0) + amount)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def _call_claude(self, prompt: str, text: str) -> Tuple[str, str]:
        if "claude" not in self._clients: raise ProviderError("Claude indisponível")
        model = self.models["claude"]
        resp = self._clients["claude"].messages.create(
            model=model, max_tokens=8192, temperature=0.2,
            messages=[{"role": "user", "content": f"{prompt}\n\nTexto:\n{text}"}]
        )
        return "".join(b.text for b in resp.content if b.type == "text"), model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def _call_gemini(self, prompt: str, text: str) -> Tuple[str, str]:
        if "gemini" not in self._clients: raise ProviderError("Gemini indisponível")
        model_name = self.models["gemini"]
        model = genai.GenerativeModel(model_name)
        resp = model.generate_content(f"{prompt}\n\nTexto:\n{text}")
        return resp.text, model_name

    def edit_text(self, prompt: str, text: str) -> AIResult:
        """
        Função principal para refino de texto.
        Tenta o cache primeiro, depois fallback entre provedores.
        """
        request_hash = self._generate_hash(prompt, text)
        
        # 1. Tentar Cache
        cached = self._cache.get(request_hash)
        if cached:
            return AIResult(cached['text'], cached['provider'], cached['model'], 0.0, True)

        # 2. Verificar Orçamento
        est_cost = self._estimate_cost(self.primary, prompt, text)
        self._check_budget(est_cost)

        # 3. Ciclo de Fallback
        providers = [self.primary] + [p for p in FALLBACK_ORDER if p != self.primary]
        last_error = None

        for provider in providers:
            try:
                if provider == "claude": out, model = self._call_claude(prompt, text)
                elif provider == "gemini": out, model = self._call_gemini(prompt, text)
                else: continue # Adicionar OpenAI se necessário

                actual_cost = self._estimate_cost(provider, prompt, out)
                self._record_cost(actual_cost)
                self._cache.set(request_hash, {"text": out, "provider": provider, "model": model})
                
                return AIResult(out, provider, model, actual_cost)
            except Exception as e:
                last_error = e
                continue

        raise ProviderError(f"Todos os provedores falharam. Último erro: {last_error}")

    def get_cost_summary(self) -> Dict:
        """Retorna o resumo de gastos para o log/Telegram."""
        day_key = f"cost_day_{date.today().isoformat()}"
        return {
            "today_usd": round(self._cost_cache.get(day_key) or 0.0, 4),
            "limit_day": self.budget_day,
            "provider": self.primary
        }